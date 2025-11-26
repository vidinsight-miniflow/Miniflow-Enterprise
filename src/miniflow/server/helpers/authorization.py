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

from ...services import AuthenticationService, ApiKeyService
from ..dependencies import get_auth_service, get_api_key_service


security_scheme = HTTPBearer(
    scheme_name="Bearer",
    description="JWT Bearer Token Authentication",
    auto_error=True
    # İstek sonrası oluşacak değerler:
    # credentials.scheme -> "Bearer"
    # credentials.credentials -> token string (Bearer <token>)
)


class AuthUser(TypedDict):
    """Kullanıcı bilgilerini tutan sözlük tipi"""
    user_id: str
    access_token: str


class ApiKeyUser(TypedDict):
    """API key bilgilerini tutan sözlük tipi"""
    workspace_id: str
    api_key: str
    permissions: Dict[str, Any]


async def authenticate_user(
    request: Request,
    credential_response: HTTPAuthorizationCredentials = Depends(security_scheme),
    auth_service: AuthenticationService = Depends(get_auth_service)
) -> AuthUser:
    """
    ACCESS TOKEN'ı valide eder ve kullanıcı bilgilerini döndürür.
    Ayrıca request.state'e user_id'yi set eder (rate limit middleware için).
    
    Optimizasyon: Eğer state'de zaten user_id varsa ve token aynıysa,
    tekrar validation yapmaz (aynı request içinde birden fazla dependency kullanımı için).
    """
    
    access_token = credential_response.credentials

    # Optimizasyon: Eğer state'de zaten user_id varsa ve token aynıysa, tekrar validation yapma
    # (Aynı request içinde birden fazla dependency kullanımı için performans iyileştirmesi)
    if hasattr(request.state, 'user_id') and hasattr(request.state, '_validated_token'):
        if request.state._validated_token == access_token:
            return AuthUser(
                user_id=request.state.user_id,
                access_token=request.state._validated_token
            )

    try:
        result = auth_service.validate_session(access_token=access_token)
        if not result or not result['valid']:
            error_msg = result.get('error', 'Invalid session') if result else 'Invalid session'
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=error_msg)
        
        user_id = result.get('user_id')
        
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")
        
        # Rate limit middleware için request.state'e user_id set et
        request.state.user_id = user_id
        # Token'ı da kaydet (aynı request içinde tekrar validation yapmamak için)
        request.state._validated_token = access_token
        
        return AuthUser(user_id=user_id, access_token=access_token)
    except HTTPException:
        # Re-raise HTTPException as-is
        raise
    except Exception as e:
        # For other exceptions, convert to HTTPException
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


async def authenticate_api_key(
    request: Request,
    api_key: str = Header(..., description="API Key", alias="X-API-KEY"),
    api_key_service: ApiKeyService = Depends(get_api_key_service),
) -> ApiKeyUser:
    """
    X-API-KEY header'ındaki API key'i valide eder ve workspace_id'yi döndürür.
    Ayrıca request.state'e workspace_id'yi set eder (rate limit middleware için).
    
    Optimizasyon: Eğer state'de zaten workspace_id varsa ve api_key aynıysa,
    tekrar validation yapmaz (aynı request içinde birden fazla dependency kullanımı için).
    """

    if not api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API key missing")

    # Optimizasyon: Eğer state'de zaten workspace_id varsa ve api_key aynıysa, tekrar validation yapma
    # (Aynı request içinde birden fazla dependency kullanımı için performans iyileştirmesi)
    if hasattr(request.state, 'workspace_id') and hasattr(request.state, '_validated_api_key'):
        if request.state._validated_api_key == api_key:
            return ApiKeyUser(
                workspace_id=request.state.workspace_id,
                api_key=request.state._validated_api_key,
                permissions=request.state._api_key_permissions
            )

    try:
        result = api_key_service.validate_api_key(full_api_key=api_key)

        if not result or not result["valid"]:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=result.get("error", "Invalid API key"))
        
        workspace_id = result.get("workspace_id")
        permissions = result.get("permissions")

        if not workspace_id or not permissions:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
        
        # Rate limit middleware için request.state'e workspace_id set et
        request.state.workspace_id = workspace_id
        # API key'i de kaydet (aynı request içinde tekrar validation yapmamak için)
        request.state._validated_api_key = api_key
        request.state._api_key_permissions = permissions
        
        return ApiKeyUser(workspace_id=workspace_id, api_key=api_key, permissions=permissions)
    except HTTPException:
        # Re-raise HTTPException as-is
        raise
    except Exception as e:
        # For other exceptions, convert to HTTPException
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


"""
# KULLANIM AMACI:
--------------------------------
- `authenticate_user`:
    JWT (Access Token) ile gelen kullanıcıyı doğrular.
    Authorization header: "Authorization: Bearer <token>"
    Başarılı olursa `AuthUser` tipinde kullanıcı bilgilerini döndürür.
    Hatalı veya geçersiz token durumunda HTTP 401 döner.

- `authenticate_api_key`:
    API key ile gelen isteği doğrular.
    Header: "X-API-KEY: <api_key>"
    Başarılı olursa `ApiKeyUser` tipinde workspace ve izin bilgilerini döndürür.
    Hatalı veya eksik API key durumunda HTTP 401 döner.


# NASIL KULLANILIR?
--------------------------------
FastAPI route’larında `Depends` ile dependency olarak eklenir:

```python
from fastapi import APIRouter, Depends
from .auth_dependencies import authenticate_user, authenticate_api_key

router = APIRouter()

# JWT ile korunan endpoint
@router.get("/user/profile")
async def profile(user=Depends(authenticate_user)):
    return {
        "user_id": user["user_id"], 
        "access_token": user["access_token"]
    }

# API key ile korunan endpoint
@router.get("/workspace/projects")
async def list_projects(api_user=Depends(authenticate_api_key)):
    return {
        "workspace_id": api_user["workspace_id"],
        "permissions": api_user["permissions"]
    }
```


# DÖNEN DEĞERLER:
--------------------------------
- AuthUser (dict / TypedDict):
    - user_id: str → Doğrulanan kullanıcının benzersiz ID'si
    -access_token: str → Kullanıcının geçerli access token’ı

- ApiKeyUser (dict / TypedDict):
    - workspace_id: str → API key’in bağlı olduğu workspace ID
    - api_key: str → Kullanılan API key değeri
    - permissions: dict → Workspace veya API key’in izinleri


# Neden Bu Değerler Dönüyor?
--------------------------------
- user_id → uygulama içerisinde kullanıcıyı tanımlamak için
- access_token → token tabanlı işlemler ve refresh mekanizması için
- api_key → loglama, kullanım takibi veya debug için
- workspace_id → API key’in hangi workspace’e ait olduğunu bilmek için
- permissions → API key’in hangi işlemleri yapabileceğini kontrol etmek için

"""