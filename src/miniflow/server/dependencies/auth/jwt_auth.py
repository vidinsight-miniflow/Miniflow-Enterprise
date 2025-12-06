from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
"""
HTTPBearer: FastAPI'nin sunduğu hazır bir security scheme (güvenlik şeması). 
HTTP header'ından Authorization başlığını bekler ve içeriğin Bearer <token> 
formatında olup olmadığını kontrol eder. Bunu bir dependency olarak kullanırsınız.

HTTPAuthorizationCredentials: HTTPBearer dependency'si başarılı olduğunda size 
verdiği nesnedir. İçinde iki önemli alan vardır: 
- scheme: örn. "Bearer" (başlığın hangi scheme olduğunu gösterir)
- credentials: gerçek token stringi, örn. "eyJhbGciOiJIUzI1NiIsInR5cCI6..."
"""

from fastapi import Depends, HTTPException, status, Header, Request

"""
Depends: FastAPI dependency injection (bağımlılık enjeksiyonu) için kullanılır. 
Bir route veya başka bir fonksiyonda bu dependency'yi parametre olarak eklediğinizde 
FastAPI otomatik olarak çalıştırır ve sonucunu o parametreye geçirir.

HTTPException: Bir isteği hata ile sonlandırmak istediğinizde (401, 403, 404 vs.)
fırlattığınız istisnadır. FastAPI bunu HTTP cevabına çevirir.

status: HTTP durum (status) kodlarını kullanıcı dostu isimlerle sağlar.
Örnek: status.HTTP_401_UNAUTHORIZED.

Header, HTTP isteklerinde (request) ve yanıtlarında (response) taşınan üst bilgi 
alanlarıdır.Yani, bir isteğin veya cevabın meta verisidir; içeriğin kendisi değil, 
içeriği veya isteği nasıl işleyeceğini anlatan bilgidir.
"""

from typing import TypedDict, Dict, Any
"""
TypedDict: Python tip belirtiminde kullanılır. Sözlük tipleri için anahtar/alan isimleri 
ve değer tiplerini belirtmeye yarar. Örneğin kullanıcı verisi { "id": int, "email": str } 
gibi bir yapıya tip eklemek istiyorsanız kullanışlıdır."
"""

from miniflow.services import LoginService, UserManagementService
from ..service_providers import get_login_service, get_user_management_service
from .rate_limiters import UserRateLimiter
from miniflow.core.exceptions import UserRateLimitExceededError



bearer_scheme = HTTPBearer(
    scheme_name="Bearer",
    description="JWT Bearer Token Authentication",
    auto_error=True
    # İstek sonrası oluşacak değerler:
    # credentials.scheme -> "Bearer"
    # credentials.credentials -> token string (Bearer <token>)
)


class AuthenticatedUser(TypedDict):
    """Kullanıcı bilgilerini tutan sözlük tipi"""
    user_id: str
    access_token: str


async def authenticate_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    login_service: LoginService = Depends(get_login_service),
) -> AuthenticatedUser:
    access_token = credentials.credentials

    try:
        result = LoginService.validate_access_token(access_token=access_token)
        if not result or not result.get("valid"):
            error_msg = result.get("error", "Invalid session") if result else "Invalid session"
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=error_msg, headers={"WWW-Authenticate": "Bearer"})

        user_id = result.get("user_id") or result.get("record_id") or result.get("id") # user_id
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session: user not found", headers={"WWW-Authenticate": "Bearer"})

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Authentication failed: {str(e)}", headers={"WWW-Authenticate": "Bearer"})

    # 3. Apply user rate limiting
    if not _check_user_rate_limit(user_id):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="User rate limit exceeded", headers={"Retry-After": "60"})
    
    request.state.user_id = user_id
    request.state.auth_type = "jwt"
    
    return AuthenticatedUser(user_id=user_id, access_token=access_token)

async def authenticate_admin(
    request: Request,
    current_user: AuthenticatedUser = Depends(authenticate_user),
) -> AuthenticatedUser:
    """
    Admin kullanıcı doğrulaması.
    
    User model'inde is_superadmin field'ı kontrol edilir.
    is_superadmin=True ise super admin, False ise normal kullanıcıdır.
    """
    from miniflow.database import RepositoryRegistry
    
    # Get session from request state (set by middleware)
    session = getattr(request.state, 'session', None)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database session not available"
        )
    
    # Get user from database
    registry = RepositoryRegistry()
    user_repo = registry.user_repository()
    user = user_repo._get_by_id(session, record_id=current_user["user_id"], raise_not_found=False)
    
    if not user or not user.is_superadmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return current_user

def _check_user_rate_limit(user_id: str) -> bool:
    try:
        limiter = UserRateLimiter()
        limiter.check_limit(user_id)
        return True
    except UserRateLimitExceededError:
        # Rate limit exceeded
        return False
    except Exception:
        # Redis error or other issue - fail open
        return True