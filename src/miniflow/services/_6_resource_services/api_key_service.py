from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import secrets

from miniflow.database import RepositoryRegistry, with_transaction, with_readonly_session
from miniflow.core.exceptions import (
    ResourceNotFoundError,
    ResourceAlreadyExistsError,
    BusinessRuleViolationError,
    InvalidInputError,
)
from miniflow.core.logger import get_logger
from miniflow.utils.helpers.encryption_helper import hash_password

# Logger instance
logger = get_logger(__name__)

# Varsayılan API key izinleri
DEFAULT_PERMISSIONS = {
    "workflows": {
        "execute": True,
        "read": True,
        "write": False,
        "delete": False
    },
    "credentials": {
        "read": True,
        "write": False,
        "delete": False
    },
    "databases": {
        "read": True,
        "write": False,
        "delete": False
    },
    "variables": {
        "read": True,
        "write": False,
        "delete": False
    },
    "files": {
        "read": True,
        "write": False,
        "delete": False
    }
}


class ApiKeyService:
    """
    API Key yönetim servisi.
    
    Workspace API key'lerinin oluşturulması, doğrulanması ve yönetimini sağlar.
    NOT: workspace_exists kontrolü middleware'de yapılır.
    """
    _registry = RepositoryRegistry()
    _api_key_repo = _registry.api_key_repository()
    _workspace_repo = _registry.workspace_repository()

    # ==================================================================================== VALIDATE ==
    @classmethod
    @with_readonly_session(manager=None)
    def validate_api_key(
        cls,
        session,
        *,
        full_api_key: str,
        client_ip: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        API key'i doğrular ve workspace bilgisini döner.
        
        Args:
            full_api_key: Tam API key string'i
            client_ip: Client IP adresi (IP whitelist kontrolü için)
            
        Returns:
            {
                "valid": True,
                "workspace_id": str,
                "api_key_id": str,
                "permissions": Dict,
                "workspace_plan_id": str
            }
            
        Raises:
            BusinessRuleViolationError: Geçersiz, inactive veya expired API key
        """
        api_key = cls._api_key_repo._get_by_api_key(session, full_api_key=full_api_key)
        
        if not api_key:
            raise BusinessRuleViolationError(
                rule_name="invalid_api_key",
                rule_detail="API key format is invalid",
                message="Invalid API key"
            )
        
        # Aktif mi?
        if not api_key.is_active:
            raise BusinessRuleViolationError(
                rule_name="api_key_inactive",
                rule_detail=f"API key {api_key_id} is inactive",
                message="API key is inactive"
            )
        
        # Süresi dolmuş mu?
        if api_key.expires_at:
            expires_at = api_key.expires_at
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if expires_at < datetime.now(timezone.utc):
                raise BusinessRuleViolationError(
                    rule_name="api_key_expired",
                    rule_detail=f"API key {api_key_id} expired at {expires_at.isoformat()}",
                    message="API key has expired"
                )
        
        # IP whitelist kontrolü
        if api_key.allowed_ips and len(api_key.allowed_ips) > 0:
            if not client_ip:
                raise BusinessRuleViolationError(
                    rule_name="ip_required",
                    rule_detail=f"API key {api_key_id} requires client IP address",
                    message="Client IP address is required for this API key"
                )
            if client_ip not in api_key.allowed_ips:
                raise BusinessRuleViolationError(
                    rule_name="ip_not_allowed",
                    rule_detail=f"IP address {client_ip} is not in allowed IPs list for API key {api_key_id}",
                    message=f"IP address {client_ip} is not allowed for this API key"
                )
        
        # Workspace aktif mi?
        workspace = cls._workspace_repo._get_by_id(session, record_id=api_key.workspace_id)
        if not workspace:
            raise BusinessRuleViolationError(
                rule_name="workspace_not_found",
                rule_detail=f"Workspace {api_key.workspace_id} not found for API key {api_key_id}",
                message="Workspace not found"
            )
        
        if workspace.is_suspended:
            raise BusinessRuleViolationError(
                rule_name="workspace_suspended",
                rule_detail=f"Workspace {api_key.workspace_id} is suspended: {workspace.suspension_reason or 'No reason provided'}",
                message="Workspace is suspended"
            )
        
        # Kullanım güncelle
        cls._api_key_repo._update_last_used(session, api_key_id=api_key.id)
        
        return {
            "valid": True,
            "workspace_id": api_key.workspace_id,
            "api_key_id": api_key.id,
            "permissions": api_key.permissions,
            "workspace_plan_id": workspace.plan_id if hasattr(workspace, 'plan_id') else None
        }

    # ==================================================================================== CREATE ==
    @classmethod
    @with_transaction(manager=None)
    def create_api_key(
        cls,
        session,
        *,
        workspace_id: str,
        owner_id: str,
        name: str,
        description: Optional[str] = None,
        permissions: Optional[Dict[str, Any]] = None,
        expires_at: Optional[datetime] = None,
        tags: Optional[List[str]] = None,
        allowed_ips: Optional[List[str]] = None,
        key_prefix: str = "sk_live_",
    ) -> Dict[str, Any]:
        """
        Yeni API key oluşturur.
        
        Args:
            workspace_id: Workspace ID'si
            owner_id: Sahip kullanıcı ID'si
            name: API key adı (workspace içinde benzersiz)
            description: Açıklama (opsiyonel)
            permissions: İzinler (opsiyonel, varsayılan kullanılır)
            expires_at: Son kullanma tarihi (opsiyonel)
            tags: Etiketler (opsiyonel)
            allowed_ips: İzin verilen IP'ler (opsiyonel)
            key_prefix: Key prefix (varsayılan: sk_live_)
            
        Returns:
            {
                "id": str,
                "api_key": str  # Sadece oluşturulurken gösterilir!
            }
            
        Raises:
            InvalidInputError: Geçersiz name
            ResourceAlreadyExistsError: Name zaten mevcut
            BusinessRuleViolationError: API key limiti aşıldı
        """
        # Name validasyonu
        if not name or not name.strip():
            raise InvalidInputError(
                field_name="name",
                message="API key name cannot be empty"
            )
        
        # Workspace kontrolü
        workspace = cls._workspace_repo._get_by_id(session, record_id=workspace_id)
        if not workspace:
            raise ResourceNotFoundError(
                resource_name="Workspace",
                resource_id=workspace_id
            )
        
        # Limit kontrolü (0, -1 veya None = unlimited)
        api_key_limit = workspace.api_key_limit
        if api_key_limit is not None and api_key_limit > 0:
            if workspace.current_api_key_count >= api_key_limit:
                raise BusinessRuleViolationError(
                    rule_name="api_key_limit_reached",
                    rule_detail=f"Workspace {workspace_id} has {workspace.current_api_key_count} API keys, limit is {api_key_limit}",
                    message=f"API key limit reached. Maximum: {api_key_limit}"
                )
        
        # Benzersizlik kontrolü
        existing = cls._api_key_repo._get_by_name(session, workspace_id=workspace_id, name=name)
        if existing:
            raise ResourceAlreadyExistsError(
                resource_name="ApiKey",
                conflicting_field="name",
                message=f"API key with name '{name}' already exists in workspace {workspace_id}"
            )
        
        # API key oluştur
        api_key_secret = secrets.token_urlsafe(32)
        full_api_key = f"{key_prefix}{api_key_secret}"
        key_hash = hash_password(full_api_key)
        
        # Hash benzersizliği kontrolü (çok düşük ihtimal ama güvenlik için)
        max_retries = 5
        retry_count = 0
        while cls._api_key_repo._get_by_key_hash(session, key_hash=key_hash) and retry_count < max_retries:
            api_key_secret = secrets.token_urlsafe(32)
            full_api_key = f"{key_prefix}{api_key_secret}"
            key_hash = hash_password(full_api_key)
            retry_count += 1
        
        if retry_count >= max_retries:
            raise BusinessRuleViolationError(
                rule_name="key_generation_failed",
                rule_detail=f"Failed to generate unique API key after {retry_count} retries (max: {max_retries})",
                message="Failed to generate unique API key"
            )
        
        # API key kaydet
        api_key = cls._api_key_repo._create(
            session,
            workspace_id=workspace_id,
            owner_id=owner_id,
            name=name,
            key_prefix=key_prefix,
            key_hash=key_hash,
            description=description,
            permissions=permissions or DEFAULT_PERMISSIONS,
            tags=tags or [],
            allowed_ips=allowed_ips or [],
            is_active=True,
            expires_at=expires_at,
            created_by=owner_id
        )
        
        # Workspace API key count güncelle
        cls._workspace_repo._update(
            session,
            record_id=workspace_id,
            current_api_key_count=workspace.current_api_key_count + 1
        )
        
        return {
            "id": api_key.id,
            "api_key": full_api_key  # Sadece oluşturulurken gösterilir!
        }

    # ==================================================================================== READ ==
    @classmethod
    @with_readonly_session(manager=None)
    def get_api_key(
        cls,
        session,
        *,
        api_key_id: str,
    ) -> Dict[str, Any]:
        """
        API key detaylarını getirir (key maskelenmiş).
        
        Args:
            api_key_id: API key ID'si
            
        Returns:
            API key detayları (key_hash hariç, prefix + **** gösterilir)
        """
        api_key = cls._api_key_repo._get_by_id(session, record_id=api_key_id)
        
        if not api_key:
            raise ResourceNotFoundError(
                resource_name="ApiKey",
                resource_id=api_key_id
            )
        
        return {
            "id": api_key.id,
            "workspace_id": api_key.workspace_id,
            "owner_id": api_key.owner_id,
            "name": api_key.name,
            "api_key_masked": f"{api_key.key_prefix}****",
            "description": api_key.description,
            "permissions": api_key.permissions,
            "is_active": api_key.is_active,
            "expires_at": api_key.expires_at.isoformat() if api_key.expires_at else None,
            "last_used_at": api_key.last_used_at.isoformat() if api_key.last_used_at else None,
            "usage_count": api_key.usage_count,
            "allowed_ips": api_key.allowed_ips,
            "tags": api_key.tags,
            "created_at": api_key.created_at.isoformat() if api_key.created_at else None
        }

    @classmethod
    @with_readonly_session(manager=None)
    def get_workspace_api_keys(
        cls,
        session,
        *,
        workspace_id: str,
    ) -> Dict[str, Any]:
        """
        Workspace'in tüm API key'lerini listeler.
        
        Args:
            workspace_id: Workspace ID'si
            
        Returns:
            {"workspace_id": str, "api_keys": List[Dict], "count": int}
        """
        api_keys = cls._api_key_repo._get_all_by_workspace_id(session, workspace_id=workspace_id)
        
        return {
            "workspace_id": workspace_id,
            "api_keys": [
                {
                    "id": key.id,
                    "name": key.name,
                    "api_key_masked": f"{key.key_prefix}****",
                    "description": key.description,
                    "is_active": key.is_active,
                    "expires_at": key.expires_at.isoformat() if key.expires_at else None,
                    "last_used_at": key.last_used_at.isoformat() if key.last_used_at else None,
                    "usage_count": key.usage_count
                }
                for key in api_keys
            ],
            "count": len(api_keys)
        }

    # ==================================================================================== UPDATE ==
    @classmethod
    @with_transaction(manager=None)
    def update_api_key(
        cls,
        session,
        *,
        api_key_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        permissions: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        allowed_ips: Optional[List[str]] = None,
        expires_at: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        API key bilgilerini günceller.
        
        NOT: key_hash değiştirilemez, yeni key oluşturulmalı.
        
        Args:
            api_key_id: API key ID'si
            name: Yeni ad (opsiyonel)
            description: Yeni açıklama (opsiyonel)
            permissions: Yeni izinler (opsiyonel)
            tags: Yeni etiketler (opsiyonel)
            allowed_ips: Yeni IP listesi (opsiyonel)
            expires_at: Yeni son kullanma tarihi (opsiyonel)
            
        Returns:
            Güncellenmiş API key bilgileri
        """
        api_key = cls._api_key_repo._get_by_id(session, record_id=api_key_id)
        
        if not api_key:
            raise ResourceNotFoundError(
                resource_name="ApiKey",
                resource_id=api_key_id
            )
        
        update_data = {}
        
        # Name değişikliği
        if name is not None and name != api_key.name:
            if not name.strip():
                raise InvalidInputError(
                    field_name="name",
                    message="API key name cannot be empty"
                )
            # Benzersizlik kontrolü
            existing = cls._api_key_repo._get_by_name(
                session, 
                workspace_id=api_key.workspace_id, 
                name=name
            )
            if existing and existing.id != api_key_id:
                raise ResourceAlreadyExistsError(
                    resource_name="ApiKey",
                    conflicting_field="name",
                    message=f"API key with name '{name}' already exists in workspace {workspace_id}"
                )
            update_data["name"] = name
        
        if description is not None:
            update_data["description"] = description
        if permissions is not None:
            update_data["permissions"] = permissions
        if tags is not None:
            update_data["tags"] = tags
        if allowed_ips is not None:
            update_data["allowed_ips"] = allowed_ips
        if expires_at is not None:
            update_data["expires_at"] = expires_at
        
        if update_data:
            cls._api_key_repo._update(session, record_id=api_key_id, **update_data)
        
        return cls.get_api_key(api_key_id=api_key_id)

    # ==================================================================================== ACTIVATE/DEACTIVATE ==
    @classmethod
    @with_transaction(manager=None)
    def deactivate_api_key(
        cls,
        session,
        *,
        api_key_id: str,
    ) -> Dict[str, Any]:
        """
        API key'i deaktive eder.
        
        Args:
            api_key_id: API key ID'si
            
        Returns:
            {"success": True}
        """
        api_key = cls._api_key_repo._get_by_id(session, record_id=api_key_id)
        
        if not api_key:
            raise ResourceNotFoundError(
                resource_name="ApiKey",
                resource_id=api_key_id
            )
        
        cls._api_key_repo._deactivate(session, api_key_id=api_key_id)
        
        return {"success": True, "is_active": False}

    @classmethod
    @with_transaction(manager=None)
    def activate_api_key(
        cls,
        session,
        *,
        api_key_id: str,
    ) -> Dict[str, Any]:
        """
        API key'i aktive eder.
        
        Args:
            api_key_id: API key ID'si
            
        Returns:
            {"success": True}
        """
        api_key = cls._api_key_repo._get_by_id(session, record_id=api_key_id)
        
        if not api_key:
            raise ResourceNotFoundError(
                resource_name="ApiKey",
                resource_id=api_key_id
            )
        
        cls._api_key_repo._activate(session, api_key_id=api_key_id)
        
        return {"success": True, "is_active": True}

    # ==================================================================================== DELETE ==
    @classmethod
    @with_transaction(manager=None)
    def delete_api_key(
        cls,
        session,
        *,
        api_key_id: str,
    ) -> Dict[str, Any]:
        """
        API key'i siler.
        
        Args:
            api_key_id: API key ID'si
            
        Returns:
            {"success": True, "deleted_id": str}
        """
        api_key = cls._api_key_repo._get_by_id(session, record_id=api_key_id)
        
        if not api_key:
            raise ResourceNotFoundError(
                resource_name="ApiKey",
                resource_id=api_key_id
            )
        
        workspace_id = api_key.workspace_id
        
        # API key sil
        cls._api_key_repo._delete(session, record_id=api_key_id)
        
        # Workspace count güncelle
        workspace = cls._workspace_repo._get_by_id(session, record_id=workspace_id)
        if workspace:
            cls._workspace_repo._update(
                session,
                record_id=workspace_id,
                current_api_key_count=max(0, workspace.current_api_key_count - 1)
            )
        
        return {
            "success": True,
            "deleted_id": api_key_id
        }

