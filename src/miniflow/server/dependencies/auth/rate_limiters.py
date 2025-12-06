import time
from datetime import datetime, timezone, timedelta
from typing import Optional

from miniflow.utils import RedisClient, ConfigurationHandler
from miniflow.core.exceptions import UserRateLimitExceededError


class BaseRateLimiter:
    """Base class for rate limiters with common functionality."""
    
    def __init__(self, limits: dict):
        self.limits = limits
    
    def _get_timestamp(self) -> dict:
        """Get current timestamps for rate limit windows."""
        now = time.time()
        return {
            "minute": int(now // 60),
            "hour": int(now // 3600),
            "day": time.strftime("%Y-%m-%d"),
        }
    
    def _get_ttl(self, window: str) -> int:
        """Get TTL for a rate limit window."""
        now = time.time()
        if window == "minute":
            return int(60 - (now % 60)) + 10  # Extra 10s buffer
        if window == "hour":
            return int(3600 - (now % 3600)) + 60  # Extra 60s buffer
        if window == "day":
            now_dt = datetime.now(timezone.utc)
            tomorrow = datetime(
                now_dt.year, now_dt.month, now_dt.day, tzinfo=timezone.utc
            ) + timedelta(days=1)
            return int((tomorrow - now_dt).total_seconds()) + 60
        return 60
    
    def _increment(self, key: str, ttl: int) -> int:
        """Atomically increment a counter in Redis."""
        if not RedisClient._client:
            return 0
        
        try:
            pipe = RedisClient._client.pipeline()
            pipe.incr(key)
            pipe.expire(key, ttl)
            results = pipe.execute()
            return results[0] if results else 0
        except Exception:
            return 0
    
    def _get_reset_time(self, window: str) -> str:
        """Get human-readable reset time for error message."""
        now = int(time.time())
        if window == "minute":
            reset_ts = (now // 60 + 1) * 60
        elif window == "hour":
            reset_ts = (now // 3600 + 1) * 3600
        else:
            now_dt = datetime.now(timezone.utc)
            tomorrow = datetime(
                now_dt.year, now_dt.month, now_dt.day, tzinfo=timezone.utc
            ) + timedelta(days=1)
            return tomorrow.strftime("%Y-%m-%d %H:%M:%S UTC")
        
        return time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(reset_ts))


class UserRateLimiter(BaseRateLimiter):
    """
    Per-user rate limiting for JWT authenticated requests.
    
    Limits:
    - minute: requests per minute per user
    - hour: requests per hour per user
    - day: requests per day per user
    
    Usage:
        limiter = UserRateLimiter()
        limiter.check_limit("USR-123456")  # Raises if exceeded
    """
    
    def __init__(self):
        # Try to load configuration, but use fallbacks if config not available
        try:
            ConfigurationHandler.ensure_loaded()
        except Exception:
            # Configuration not available - use defaults
            pass
        
        limits = {
            "minute": ConfigurationHandler.get_int(
                "Rate Limiting", "user_requests_per_minute", fallback=600
            ) or 600,
            "hour": ConfigurationHandler.get_int(
                "Rate Limiting", "user_requests_per_hour", fallback=6000
            ) or 6000,
            "day": ConfigurationHandler.get_int(
                "Rate Limiting", "user_requests_per_day", fallback=60000
            ) or 60000,
        }
        super().__init__(limits)
    
    def check_limit(self, user_id: str) -> None:
        """
        Check if user is within rate limits.
        
        Args:
            user_id: User ID to check
        
        Raises:
            UserRateLimitExceededError: If any limit is exceeded
        """
        if not RedisClient._client:
            # Redis not available, allow request
            return
        
        timestamps = self._get_timestamp()
        
        for window in ["minute", "hour", "day"]:
            key = f"rl:user:{user_id}:{window}:{timestamps[window]}"
            ttl = self._get_ttl(window)
            count = self._increment(key, ttl)
            
            if count > self.limits[window]:
                reset_time = self._get_reset_time(window)
                raise UserRateLimitExceededError(
                    reset_time=reset_time,
                    message=f"User rate limit exceeded ({window})"
                )


class WorkspaceRateLimiter(BaseRateLimiter):
    """
    Per-workspace rate limiting for API Key authenticated requests.
    
    Limits are based on workspace plan:
    - Different plans have different limits
    - Loaded dynamically from WorkspacePlansService
    
    Usage:
        limiter = WorkspaceRateLimiter()
        limiter.check_limit("WSP-123456", "WPL-PREMIUM")
    """
    
    def __init__(self):
        super().__init__({})
        self._plan_limits_cache: Optional[dict] = None
        self._cache_time: float = 0
        self._cache_ttl: float = 300  # 5 minute cache
    
    def _load_plan_limits(self) -> dict:
        """Load plan limits from service with caching."""
        now = time.time()
        
        # Return cached if valid
        if self._plan_limits_cache and (now - self._cache_time) < self._cache_ttl:
            return self._plan_limits_cache
        
        try:
            from ..service_providers import get_workspace_plan_service
            service = get_workspace_plan_service()
            self._plan_limits_cache = service.get_api_limits() or {}
            self._cache_time = now
            return self._plan_limits_cache
        except Exception:
            return self._plan_limits_cache or {}
    
    def check_limit(self, workspace_id: str, plan_id: str) -> None:
        """
        Check if workspace is within rate limits based on plan.
        
        Args:
            workspace_id: Workspace ID to check
            plan_id: Workspace plan ID for limit lookup
        
        Raises:
            Exception: If any limit is exceeded
        """
        if not RedisClient._client:
            return
        
        plan_limits = self._load_plan_limits()
        
        if plan_id not in plan_limits:
            # Unknown plan, use defaults
            limits = {"minute": 100, "hour": 1000, "day": 10000}
        else:
            limits = plan_limits[plan_id].get("limits", {})
        
        timestamps = self._get_timestamp()
        
        for window in ["minute", "hour", "day"]:
            if window not in limits:
                continue
            
            key = f"rl:ws:{workspace_id}:{window}:{timestamps[window]}"
            ttl = self._get_ttl(window)
            count = self._increment(key, ttl)
            
            if count > limits[window]:
                reset_time = self._get_reset_time(window)
                # Import specific exception based on window
                from miniflow.core.exceptions import (
                    ApiKeyMinuteRateLimitExceededError,
                    ApiKeyHourRateLimitExceededError,
                    ApiKeyDayRateLimitExceededError,
                )
                
                if window == "minute":
                    raise ApiKeyMinuteRateLimitExceededError(reset_time=reset_time)
                elif window == "hour":
                    raise ApiKeyHourRateLimitExceededError(reset_time=reset_time)
                else:
                    raise ApiKeyDayRateLimitExceededError(reset_time=reset_time)

