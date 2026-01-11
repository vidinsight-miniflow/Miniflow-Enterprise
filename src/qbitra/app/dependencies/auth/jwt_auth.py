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

from qbitra.services import LoginService
from ..service_providers import get_login_service


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
    is_admin: bool


async def authenticate_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    login_service: LoginService = Depends(get_login_service),
) -> AuthenticatedUser:
    access_token = credentials.credentials

    try:
        result = login_service.validate_access_token(access_token=access_token)
        result_data = result.get("data", {}) if result else {}
        if not result_data.get("valid"):
            error_msg = result_data.get("error", "Invalid session")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=error_msg, headers={"WWW-Authenticate": "Bearer"})

        user_id = result_data.get("user_id")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session: user not found", headers={"WWW-Authenticate": "Bearer"})

        is_admin = result_data.get("is_admin", False)

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Authentication failed: {str(e)}", headers={"WWW-Authenticate": "Bearer"})

    request.state.user_id = user_id
    request.state.auth_type = "jwt"
    request.state.is_admin = is_admin
    
    return AuthenticatedUser(user_id=user_id, access_token=access_token, is_admin=is_admin)


async def authenticate_admin(
    current_user: AuthenticatedUser = Depends(authenticate_user),
) -> AuthenticatedUser:
    """
    Admin kullanıcı doğrulaması.
    
    JWT token içindeki is_admin claim'i kontrol edilir.
    Database query yapılmaz, performans için token'dan okunur.
    """    
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return current_user