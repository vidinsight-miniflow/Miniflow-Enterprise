import time
import ipaddress
from datetime import datetime, timezone, timedelta
from typing import Optional, FrozenSet
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from miniflow.utils import RedisClient, ConfigurationHandler


class IPRateLimitMiddleware(BaseHTTPMiddleware):
    # Paths to exclude from rate limiting
    EXCLUDE_PATHS: FrozenSet[str] = frozenset([
        "/",
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/favicon.ico",
    ])

    # Prefix patterns to exclude
    EXCLUDE_PREFIXES = ("/docs", "/redoc")

    def __init__(self, app, exclude_paths: Optional[list] = None):
        super().__init__(app)
        
        # Try to load configuration, but use fallbacks if config not available
        try:
            ConfigurationHandler.ensure_loaded()
        except Exception:
            # Configuration not available - use defaults
            pass
        
        # Load limits from configuration (with safe fallbacks)
        self.limits = {
            "minute": ConfigurationHandler.get_int(
                "Rate Limiting", "ip_requests_per_minute", fallback=1000
            ) or 1000,
            "hour": ConfigurationHandler.get_int(
                "Rate Limiting", "ip_requests_per_hour", fallback=10000
            ) or 10000,
        }
        
        # Allow custom exclude paths
        if exclude_paths:
            self.EXCLUDE_PATHS = frozenset(list(self.EXCLUDE_PATHS) + exclude_paths)
    
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        
        # 1. Check if path should be excluded
        if self._should_skip(path):
            return await call_next(request)
        
        # 2. Get client IP
        client_ip = self._extract_client_ip(request)
        
        # 3. Check rate limit
        is_allowed, retry_after = self._check_rate_limit(client_ip)
        
        if not is_allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "error": {
                        "code": "IP_RATE_LIMIT_EXCEEDED",
                        "message": "Too many requests from this IP address",
                        "retry_after_seconds": retry_after,
                    }
                },
                headers={"Retry-After": str(retry_after)}
            )
        
        # 4. Continue to next middleware/handler
        return await call_next(request)
    
    def _should_skip(self, path: str) -> bool:
        """Check if path should skip rate limiting."""
        if path in self.EXCLUDE_PATHS:
            return True
        for prefix in self.EXCLUDE_PREFIXES:
            if path.startswith(prefix):
                return True
        return False
    
    def _extract_client_ip(self, request: Request) -> str:
        """
        Extract client IP with proxy support.
        
        Priority:
        1. X-Forwarded-For (first IP)
        2. X-Real-IP
        3. request.client.host
        4. "unknown" fallback
        """
        # Try X-Forwarded-For first (load balancer/proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # First IP in the chain is the original client
            ip = forwarded_for.split(",")[0].strip()
            if self._is_valid_ip(ip):
                return ip
        
        # Try X-Real-IP (nginx)
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            ip = real_ip.strip()
            if self._is_valid_ip(ip):
                return ip
        
        # Fall back to direct connection
        if request.client and request.client.host:
            ip = request.client.host
            if self._is_valid_ip(ip):
                return ip
        
        return "unknown"
    
    def _is_valid_ip(self, ip: str) -> bool:
        """Validate IP address format."""
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False
    
    def _check_rate_limit(self, ip: str) -> tuple[bool, int]:
        """
        Check if IP is within rate limits.
        
        Returns:
            (is_allowed, retry_after_seconds)
        """
        # Graceful degradation: if Redis unavailable, allow request
        if not RedisClient._initialized or not RedisClient._client:
            try:
                RedisClient.initialize()
            except Exception:
                # Redis not available, allow request
                return (True, 0)
        
        if not RedisClient._client:
            return (True, 0)
        
        now = time.time()
        current_minute = int(now // 60)
        current_hour = int(now // 3600)
        
        try:
            pipe = RedisClient._client.pipeline()
            
            # Minute counter
            minute_key = f"rl:ip:{ip}:m:{current_minute}"
            pipe.incr(minute_key)
            pipe.expire(minute_key, 120)  # 2 minute TTL for safety
            
            # Hour counter
            hour_key = f"rl:ip:{ip}:h:{current_hour}"
            pipe.incr(hour_key)
            pipe.expire(hour_key, 7200)  # 2 hour TTL for safety
            
            results = pipe.execute()
            minute_count = results[0]
            hour_count = results[2]
            
            # Check minute limit
            if minute_count > self.limits["minute"]:
                retry_after = int(60 - (now % 60))
                return (False, retry_after)
            
            # Check hour limit
            if hour_count > self.limits["hour"]:
                retry_after = int(3600 - (now % 3600))
                return (False, retry_after)
            
            return (True, 0)
            
        except Exception:
            # Redis error, allow request (fail open)
            return (True, 0)