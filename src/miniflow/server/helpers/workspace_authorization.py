from fastapi import Depends, HTTPException, status, Path
"""
Depends: FastAPI'de dependency injection (bağımlılık enjeksiyonu) yapmak için kullanılır.
Bir route veya fonksiyon parametresine eklediğinizde, FastAPI otomatik olarak dependency fonksiyonunu 
çağırır ve sonucunu parametreye geçirir.

HTTPException: Bir isteği hata ile sonlandırmak için kullanılır. 
Fırlatıldığında FastAPI otomatik olarak HTTP response döner.
Örnek: 401 Unauthorized, 404 Not Found gibi durumlar.

status: HTTP durum (status) kodlarını daha okunabilir sabitler ile kullanmanızı sağlar.
Örnek: status.HTTP_401_UNAUTHORIZED, status.HTTP_404_NOT_FOUND

Path: Route path parametrelerini tanımlamak, validasyon ve metadata eklemek için kullanılır.
Örnek: 
    user_id: int = Path(..., description="User ID")
Burada '...' parametrenin zorunlu olduğunu, description ise Swagger dokümantasyonunda açıklama olarak görünmesini sağlar.
"""

import re

from .authorization import AuthUser, authenticate_user
from ...core.exceptions import AppException
from ...services import WorkspaceService, WorkspaceMemberService
from ..dependencies import get_workspace_service, get_workspace_member_service


async def extract_workspace_id(workspace_id: str = Path(..., alias="workspace_id")) -> str:
    if not re.match(r'^WSP-[A-F0-9]{16}$', workspace_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid workspace ID format")
    return workspace_id


async def require_valid_workspace(
    workspace_id: str = Depends(extract_workspace_id),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
    check_suspended: bool = True,
) -> str:
    """
    Workspace ID'yi doğrular ve suspended durumunu kontrol eder.
    """
    try:
        workspace_service.validate_workspace(workspace_id=workspace_id, check_suspended=check_suspended)
        return workspace_id
    except (HTTPException, AppException):
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

async def validate_workspace_member(
    workspace_id: str = Depends(extract_workspace_id),
    current_user: AuthUser = Depends(authenticate_user),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
    workspace_member_service: WorkspaceMemberService = Depends(get_workspace_member_service),
    check_suspended: bool = True,
) -> str:
    """
    Workspace erişimini kontrol eder ve suspended durumunu kontrol eder.
    """
    try:
        workspace_service.validate_workspace(workspace_id=workspace_id, check_suspended=check_suspended)
        workspace_member_service.validate_workspace_member(workspace_id=workspace_id, user_id=current_user["user_id"])
        return workspace_id
    except (HTTPException, AppException):
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

async def validate_workspace_member_allow_suspended(
    workspace_id: str = Depends(extract_workspace_id),
    current_user: AuthUser = Depends(authenticate_user),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
    workspace_member_service: WorkspaceMemberService = Depends(get_workspace_member_service),
) -> str:
    """
    Workspace erişimini kontrol eder ve suspended durumunu kontrol etmez.
    """
    return await validate_workspace_member(
        workspace_id=workspace_id,
        current_user=current_user,
        workspace_service=workspace_service,
        workspace_member_service=workspace_member_service,
        check_suspended=False,
    )

"""
# KULLANIM AMACI:
--------------------------------
- `extract_workspace_id`:
    Path parametresinden workspace ID'yi çıkarır ve format doğrulaması yapar.
    Beklenen format: WSP-[16 haneli hexadecimal] (örn: WSP-A1B2C3D4E5F67890)
    Geçersiz format durumunda HTTP 400 döner.

- `require_valid_workspace`:
    Workspace'in sistemde var olduğunu ve aktif (suspended değil) olduğunu doğrular.
    Varsayılan olarak suspended workspace'lere izin vermez.
    Workspace bulunamazsa veya suspended ise HTTP 404 veya 403 döner.

- `validate_workspace_member`:
    Kullanıcının workspace'e erişim yetkisi olduğunu doğrular.
    Hem workspace'in geçerliliğini hem de kullanıcının üyeliğini kontrol eder.
    Varsayılan olarak suspended workspace'lere izin vermez.
    Yetkisiz erişim durumunda HTTP 403 döner.

- `validate_workspace_member_allow_suspended`:
    Suspended workspace'lere de erişim sağlayan özel versiyon.
    Workspace'i suspend/unsuspend etmek için gerekli endpoint'lerde kullanılır.
    Normal şartlarda suspended workspace'lere erişilemeyeceği için bu özel fonksiyon gereklidir.


# NASIL KULLANILIR?
--------------------------------
FastAPI route'larında `Depends` ile dependency olarak eklenir:
```python
from fastapi import APIRouter, Depends
from .workspace_middleware import (
    extract_workspace_id,
    require_valid_workspace, 
    validate_workspace_member,
    validate_workspace_member_allow_suspended
)

router = APIRouter()

# Sadece workspace ID formatı kontrolü
@router.get("/workspaces/{workspace_id}/public-info")
async def get_public_info(workspace_id: str = Depends(extract_workspace_id)):
    return {"workspace_id": workspace_id}

# Workspace var mı ve aktif mi kontrolü (üyelik kontrolü YOK)
@router.get("/workspaces/{workspace_id}/status")
async def check_status(workspace_id: str = Depends(require_valid_workspace)):
    return {"status": "active"}

# Tam yetkilendirme: Workspace + Üyelik kontrolü
@router.get("/workspaces/{workspace_id}/flows")
async def list_flows(workspace_id: str = Depends(validate_workspace_member)):
    return {"workspace_id": workspace_id, "flows": [...]}

# Suspended workspace'lere izin veren versiyon
@router.post("/workspaces/{workspace_id}/unsuspend")
async def unsuspend(workspace_id: str = Depends(validate_workspace_member_allow_suspended)):
    # Suspended workspace'i açmak için bu endpoint'e erişebilmeliyiz
    return {"message": "Workspace unsuspended"}
```


# DÖNEN DEĞERLER:
--------------------------------
Tüm fonksiyonlar `str` tipinde workspace_id döner:
    - workspace_id: str → Doğrulanmış ve geçerli workspace ID'si (örn: "WSP-A1B2C3D4E5F67890")


# Neden Sadece workspace_id Dönüyor?
--------------------------------
- workspace_id → sonraki işlemlerde workspace'i tanımlamak için yeterli
- Diğer workspace detayları (name, plan, limits vb.) → gerektiğinde WorkspaceService ile alınır
- Bu yaklaşım "separation of concerns" prensibine uyar:
    • Middleware: Sadece doğrulama ve yetkilendirme
    • Service: İş mantığı ve veri işleme
- Memory efficient: Gereksiz veri taşınmaz, sadece ID geçilir


# Hangi Fonksiyon Ne Zaman Kullanılmalı?
--------------------------------
1. `extract_workspace_id`: 
   → Public endpoint'ler veya sadece ID format kontrolü gerektiğinde
   → Örnek: /workspaces/{workspace_id}/public-stats

2. `require_valid_workspace`:
   → Workspace varlığı önemli ama üyelik kontrolü gerekmediğinde
   → Örnek: Admin paneli, system-level işlemler

3. `validate_workspace_member`:
   → Normal kullanıcı endpoint'lerinde (EN ÇOĞU BURASI)
   → Hem workspace hem üyelik kontrolü gerektiğinde
   → Örnek: /workspaces/{workspace_id}/flows, /workspaces/{workspace_id}/variables

4. `validate_workspace_member_allow_suspended`:
   → Sadece suspend/unsuspend endpoint'lerinde
   → Suspended workspace üzerinde işlem yapılması gerektiğinde
   → Örnek: /workspaces/{workspace_id}/suspend, /workspaces/{workspace_id}/unsuspend


# HATA DURUMLARI:
--------------------------------
- HTTP 400 Bad Request:
    → Workspace ID format hatası (extract_workspace_id)
    → Örnek: "WSP-INVALID" veya "123456"

- HTTP 404 Not Found:
    → Workspace bulunamadı (require_valid_workspace, validate_workspace_member)
    
- HTTP 403 Forbidden:
    → Workspace suspended (require_valid_workspace, validate_workspace_member)
    → Kullanıcı workspace üyesi değil (validate_workspace_member)
    
- HTTP 401 Unauthorized:
    → JWT token geçersiz veya eksik (authenticate_user dependency'den)

- HTTP 500 Internal Server Error:
    → Beklenmeyen sistem hatası


# GÜVENLİK KATMANLARI:
--------------------------------
Middleware'ler şu sırayla kontrol yapar:

1. JWT Authentication (authenticate_user) → Kullanıcı kimliği
2. Workspace ID Format (extract_workspace_id) → ID geçerliliği  
3. Workspace Existence (require_valid_workspace) → Workspace var mı?
4. Workspace Status (check_suspended=True) → Suspended mı?
5. Membership Check (validate_workspace_member) → Kullanıcı üye mi?

Bu katmanlı yapı sayesinde:
    ✓ Erken doğrulama: Hatalı istekler hemen reddedilir
    ✓ Performans: Gereksiz veritabanı sorguları önlenir
    ✓ Güvenlik: Her katman bağımsız kontrol sağlar
"""

def require_role_or_permission():
    # TODO: Implement this
    pass


"""
"""

def check_feature_enabled():
    # TODO: Implement this
    pass

def check_rate_limit():
    # TODO: Implement this
    pass

def require_rate_limit():
    # TODO: Implement this
    pass


"""
"""