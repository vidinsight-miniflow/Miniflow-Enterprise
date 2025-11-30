import time
import ipaddress
import os
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from src.miniflow.utils import RedisClient
from src.miniflow.core.exceptions import (
    IpRateLimitExceededError,
    UserRateLimitExceededError,
    ApiKeyMinuteRateLimitExceededError,
    ApiKeyHourRateLimitExceededError,
    ApiKeyDayRateLimitExceededError,
)

from ..dependencies import get_workspace_plans_service, get_api_key_service
from src.miniflow.utils.helpers.jwt_helper import validate_access_token
from src.miniflow.utils import ConfigurationHandler

# Debug mode kontrolü - environment variable ile açılıp kapatılabilir
DEBUG_RATE_LIMIT = os.getenv("DEBUG_RATE_LIMIT", "false").lower() == "true"


def _validate_ip_address(ip: str) -> Optional[str]:
    """
    IP adresini validate eder.
    """
    try:
        parsed_ip = ipaddress.ip_address(ip)
        return str(parsed_ip)
    except ValueError:
        return None

def get_client_ip(
    request: Request,
    trust_proxies: Optional[list[str]] = None,
    validate_ip: bool = True,
    fallback_ip: str = "unknown",
) -> str:
    """
    Client IP adresini alır (proxy/load balancer desteği ile).
    
    Öncelik sırası:
    1. X-Forwarded-For header'ı (ilk IP - gerçek client IP)
    2. X-Real-IP header'ı
    3. request.client.host (direkt bağlantı)
    4. "unknown" (fallback)
    """
    ip_address = None

    if trust_proxies:
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            ip_address = forwarded_for.split(",")[0].strip()
        if not ip_address:
            real_ip = request.headers.get("X-Real-IP")
            if real_ip:
                ip_address = real_ip.strip()
        
        if ip_address and validate_ip:
            validated_ip = _validate_ip_address(ip_address)
            if validated_ip:
                return validated_ip
            return fallback_ip

        return ip_address or fallback_ip
    
    # trust_proxies None ise request.client.host kullan
    if request.client:
        ip_address = request.client.host
        if ip_address and validate_ip:
            validated_ip = _validate_ip_address(ip_address)
            if validated_ip:
                return validated_ip
            return fallback_ip
        return ip_address or fallback_ip
    
    return fallback_ip


class BaseRateLimiter:
    def __init__(self, limits: dict):
        self.limits = limits

    def _timestamp(self):
        now = time.time()
        return {
            "minute": int(now // 60),
            "hour": int(now // 3600),
            "day": time.strftime("%Y-%m-%d")
        }
    
    def _ttl(self, window: str):
        now = time.time()
        if window == "minute":
            return int(60 - (now % 60))
        if window == "hour":
            return int(3600 - (now % 3600))
        if window == "day":
            now_dt = datetime.now(timezone.utc)
            today_start = datetime(now_dt.year, now_dt.month, now_dt.day, tzinfo=timezone.utc)
            # Yarın gece yarısına kadar olan süreyi hesapla
            tomorrow = today_start + timedelta(days=1)
            return int((tomorrow - now_dt).total_seconds())
        raise ValueError("Invalid window")

    def _inc(self, key: str, ttl: int):
        if not RedisClient._client:
            # Redis client yoksa rate limit atla
            return 0
        try:
            pipe = RedisClient._client.pipeline()
            pipe.incr(key)
            pipe.expire(key, ttl)
            results = pipe.execute()
            return results[0] if results else 0
        except Exception as e:
            # Redis hatası durumunda rate limit atla (sessizce)
            if DEBUG_RATE_LIMIT:
                print(f"[RATE-LIMIT] Redis error in _inc: {type(e).__name__}: {str(e)}")
            return 0

    def _reset_time(self, window: str):
        now = int(time.time())
        if window == "minute":
            return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime((now // 60 + 1) * 60))
        if window == "hour":
            return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime((now // 3600 + 1) * 3600))
        if window == "day":
            now_dt = datetime.now(timezone.utc)
            today_start = datetime(now_dt.year, now_dt.month, now_dt.day, tzinfo=timezone.utc)
            # Yarın gece yarısı
            tomorrow = today_start + timedelta(days=1)
            return tomorrow.strftime("%Y-%m-%d %H:%M:%S")

        return None


class IpRateLimiter(BaseRateLimiter):
    """
    IP bazlı rate limiting - DDoS ve abuse koruması
    """
    def __init__(self):
        super().__init__( {
            "minute": ConfigurationHandler.get_int("Rate Limitting", "ip_minute_limit", fallback=1000),      # Dakikada 1000 istek
            "hour":  ConfigurationHandler.get_int("Rate Limitting", "ip_hour_limit", fallback=10000),        # Saatte 10,000 istek
            "day":  ConfigurationHandler.get_int("Rate Limitting", "ip_day_limit", fallback=100000)          # Günde 100,000 istek
        })

    def check_limit(self, ip: str):
        timestamp = self._timestamp()
        for window in ["minute", "hour", "day"]:
            ttl = self._ttl(window)
            key = f"rl:ip:{ip}:{window}:{timestamp[window]}"
            count = self._inc(key, ttl)
            if count > self.limits[window]:
                raise IpRateLimitExceededError(
                    message=f"IP rate limit exceeded for {ip}",
                    retry_after=self._ttl(window)
                )


class UserRateLimiter(BaseRateLimiter):
    """
    User bazlı rate limiting - Normal authenticated kullanım
    """
    def __init__(self):
        super().__init__({
            "minute": ConfigurationHandler.get_int("Rate Limitting", "user_minute_limit", fallback=600),      # Dakikada 600 istek
            "hour": ConfigurationHandler.get_int("Rate Limitting", "user_hour_limit", fallback=6000),         # Saatte 6,000 istek
            "day": ConfigurationHandler.get_int("Rate Limitting", "user_day_limit", fallback=60000)          # Günde 60,000 istek
        })

    def check_limit(self, user_id: str):
        timestamp = self._timestamp()
        for window in ["minute", "hour", "day"]:
            ttl = self._ttl(window)
            key = f"rl:user:{user_id}:{window}:{timestamp[window]}"
            count = self._inc(key, ttl)
            if count > self.limits[window]:
                reset_time = self._reset_time(window)
                raise UserRateLimitExceededError(
                    reset_time=reset_time,
                    message=f"User rate limit exceeded for user {user_id}"
                )


class ApiKeyRateLimiter(BaseRateLimiter):
    """
    API Key bazlı rate limiting - Ücretli/yoğun kullanım
    """
    def __init__(self):
        try:
            # Lazy loading: get_api_limits session gerektirir, bu yüzden her request'te çağrılmalı
            # Şimdilik boş dict, check_limit içinde dinamik olarak yüklenecek
            self.workspace_limits = {}
        except Exception:
            # Servis hatası durumunda boş dict kullan
            self.workspace_limits = {}
        super().__init__({}) 

    def check_limit(self, workspace_id: str, plan_id: str):
        # Lazy loading: workspace_limits boşsa yükle
        if not self.workspace_limits:
            try:
                self.workspace_limits = get_workspace_plans_service().get_api_limits() or {}
            except Exception:
                # Servis hatası durumunda boş dict kullan
                self.workspace_limits = {}
        
        if plan_id not in self.workspace_limits:
            raise ValueError(f"Plan {plan_id} bulunamadı")

        plan_data = self.workspace_limits[plan_id]
        if "limits" not in plan_data:
            raise ValueError(f"Plan {plan_id} için limits bulunamadı")

        limits = plan_data["limits"]
        timestamp = self._timestamp()

        for window in ["minute", "hour", "day"]:
            if window not in limits:
                continue  # Bu window için limit yoksa atla
            
            ttl = self._ttl(window)
            key = f"rl:workspace:{workspace_id}:{window}:{timestamp[window]}"
            count = self._inc(key, ttl)
            
            if count > limits[window]:
                reset_time = self._reset_time(window)
                if window == "minute":
                    raise ApiKeyMinuteRateLimitExceededError(
                        reset_time=reset_time,
                        message=f"API key rate limit exceeded for workspace {workspace_id}"
                    )
                elif window == "hour":
                    raise ApiKeyHourRateLimitExceededError(
                        reset_time=reset_time,
                        message=f"API key rate limit exceeded for workspace {workspace_id}"
                    )
                elif window == "day":
                    raise ApiKeyDayRateLimitExceededError(
                        reset_time=reset_time,
                        message=f"API key rate limit exceeded for workspace {workspace_id}"
                    )




class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, exclude_paths: Optional[list] = None):
        super().__init__(app)

        self.ip_limiter = IpRateLimiter()
        self.user_limiter = UserRateLimiter()
        self.api_key_limiter = ApiKeyRateLimiter()

        self.exclude_paths = exclude_paths or [
            "/",
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/favicon.ico"
        ]

    def _should_skip_rate_limit(self, path: str) -> bool:
        """Bu path için rate limit kontrolü yapılmayacak mı?"""
        for excluded in self.exclude_paths:
            # "/" için özel kontrol - sadece tam olarak "/" ise exclude et
            if excluded == "/":
                if path == "/":
                    return True
            # Diğer path'ler için startswith kontrolü
            elif path.startswith(excluded):
                return True
        return False
    
    
    def _get_user_id_from_token(self, request: Request) -> Optional[str]:
        """Request'te geçerli bir JWT token varsa user_id döndürür."""
        # Önce request.state'den kontrol et (authenticate_user dependency'si set eder)
        # Not: Middleware dependency'lerden önce çalışır, bu yüzden state'de olmayabilir
        if hasattr(request.state, 'user_id') and request.state.user_id:
            if DEBUG_RATE_LIMIT:
            print(f"[RATE-LIMIT] User ID from state: {request.state.user_id}")
            return request.state.user_id
        
        # Eğer state'de yoksa header'dan parse et (middleware dependency'lerden önce çalışır)
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            if DEBUG_RATE_LIMIT:
            print("[RATE-LIMIT] No Authorization header found")
            return None
        
        if not auth_header.startswith("Bearer "):
            if DEBUG_RATE_LIMIT:
            print(f"[RATE-LIMIT] Authorization header doesn't start with 'Bearer ': {auth_header[:20]}...")
            return None
        
        token = auth_header.replace("Bearer ", "").strip()
        if not token:
            if DEBUG_RATE_LIMIT:
            print("[RATE-LIMIT] Token is empty after removing 'Bearer '")
            return None
        
        try:
            # validate_access_token exception fırlatabilir, bu yüzden try-except kullanıyoruz
            is_valid, payload = validate_access_token(token)
            
            if not is_valid or not payload:
                if DEBUG_RATE_LIMIT:
                print("[RATE-LIMIT] Token validation failed or payload is empty")
                return None
            
            user_id = payload.get("user_id") or None
            
            # State'e kaydet (sonraki kontroller için)
            if user_id:
                request.state.user_id = user_id
                # Token'ı da kaydet (authenticate_user optimization için)
                request.state._validated_token = token
                if DEBUG_RATE_LIMIT:
                print(f"[RATE-LIMIT] User ID saved to request.state: {user_id}")
            
            return user_id
        except Exception as e:
            # Token geçersiz veya parse edilemedi
            if DEBUG_RATE_LIMIT:
            print(f"[RATE-LIMIT] Token parse error: {type(e).__name__}: {str(e)}")
            import traceback
            print(f"[RATE-LIMIT] Traceback: {traceback.format_exc()}")
            return None
    
    def _has_api_key(self, request: Request) -> Optional[dict]:
        """Request'te geçerli bir API key var mı?"""
        api_key = request.headers.get("X-API-KEY")
        if api_key:
            try:
                api_key_service = get_api_key_service()
                result = api_key_service.validate_api_key(full_api_key=api_key)
                if result and result.get("valid"):
                    return result
            except Exception:
                # Servis hatası durumunda None döndür (rate limit atlanır)
                return None
        return None

    async def dispatch(self, request: Request, call_next):
        if DEBUG_RATE_LIMIT:
        print(f"[RATE-LIMIT] Middleware çalışıyor - Path: {request.url.path}")
        
        if self._should_skip_rate_limit(request.url.path):
            if DEBUG_RATE_LIMIT:
            print(f"[RATE-LIMIT] Path exclude edildi: {request.url.path}")
            return await call_next(request)
        
        # Redis client kontrolü - her request'te kontrol et (worker process'lerde farklı olabilir)
        from src.miniflow.utils import RedisClient
        if not RedisClient._initialized:
            if DEBUG_RATE_LIMIT:
            print("[RATE-LIMIT] Redis initialized değil, initialize ediliyor...")
            try:
                RedisClient.initialize()
                if DEBUG_RATE_LIMIT:
                print("[RATE-LIMIT] Redis başarıyla initialize edildi")
            except Exception as e:
                # Redis bağlantı hatası - rate limit atla, request devam etsin
                if DEBUG_RATE_LIMIT:
                print(f"[RATE-LIMIT] Redis bağlantı hatası: {type(e).__name__}: {str(e)}")
                print("[RATE-LIMIT] Rate limit atlanıyor, request devam ediyor")
                return await call_next(request)
        
        if not RedisClient._client:
            # Redis client yoksa rate limit atla
            if DEBUG_RATE_LIMIT:
            print("[RATE-LIMIT] Redis client yok, rate limit atlanıyor")
            return await call_next(request)
        
        api_key_info = self._has_api_key(request)
        if api_key_info:
            workspace_id = api_key_info.get("workspace_id")
            plan_id = api_key_info.get("workspace_plan_id")
            if DEBUG_RATE_LIMIT:
            print(f"[RATE-LIMIT] API Key detected for workspace: {workspace_id}")
            try:
                self.api_key_limiter.check_limit(workspace_id, plan_id)
            except (ApiKeyMinuteRateLimitExceededError, ApiKeyHourRateLimitExceededError, ApiKeyDayRateLimitExceededError) as e:
                raise HTTPException(status_code=429, detail=str(e)) from e
            except ValueError:
                # Plan bulunamadı veya limits eksik - rate limit atla, request devam etsin
                pass
            
            return await call_next(request)
        
        user_id = self._get_user_id_from_token(request)
        
        if user_id:
            try:
                # Redis client kontrolü
                from src.miniflow.utils import RedisClient
                if not RedisClient._client:
                    if DEBUG_RATE_LIMIT:
                    print("[RATE-LIMIT] Redis client not initialized, skipping user rate limit")
                    return await call_next(request)
                
                self.user_limiter.check_limit(user_id)
                # PERFORMANCE: RedisClient.keys() çağrısı kaldırıldı - O(N) complexity, çok yavaş!
            except UserRateLimitExceededError as e:
                raise HTTPException(status_code=429, detail=str(e)) from e
            except Exception as e:
                if DEBUG_RATE_LIMIT:
                print(f"[RATE-LIMIT] User rate limit error: {type(e).__name__}: {str(e)}")
                # Redis hatası veya başka bir hata - sessizce atla, request devam etsin
                pass
            
            return await call_next(request)
        
        # IP bazlı rate limit (en son kontrol - her istek için)
        # IP "unknown" olsa bile rate limit yapılmalı (güvenlik için)
        # Önce header'ları kontrol et (Bruno gibi client'lar için), sonra request.client.host kullan
        client_ip = None
        
        # 1. Önce header'lardan IP al (Bruno ve diğer client'lar için)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        if not client_ip:
            real_ip = request.headers.get("X-Real-IP")
            if real_ip:
                client_ip = real_ip.strip()
        
        # 2. Header'da yoksa request.client.host kullan
        if not client_ip and request.client:
            client_ip = request.client.host
        
        # 3. IP'yi validate et
        if client_ip:
            validated_ip = _validate_ip_address(client_ip)
            if validated_ip:
                client_ip = validated_ip
            else:
                client_ip = "unknown"
        else:
            client_ip = "unknown"
        
        try:
            # Redis client kontrolü
            from src.miniflow.utils import RedisClient
            if not RedisClient._client:
                if DEBUG_RATE_LIMIT:
                print("[RATE-LIMIT] Redis client not initialized, skipping IP rate limit")
                return await call_next(request)
            
            self.ip_limiter.check_limit(client_ip)
            # PERFORMANCE: RedisClient.keys() çağrısı kaldırıldı - O(N) complexity, çok yavaş!
        except IpRateLimitExceededError as e:
            raise HTTPException(status_code=429, detail=str(e)) from e
        except Exception as e:
            if DEBUG_RATE_LIMIT:
            print(f"[RATE-LIMIT] IP rate limit error: {type(e).__name__}: {str(e)}")
            # Redis hatası veya başka bir hata - sessizce atla, request devam etsin
            pass
        
        return await call_next(request)




