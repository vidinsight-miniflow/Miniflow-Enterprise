from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import json

from miniflow.database import RepositoryRegistry, with_transaction, with_readonly_session
from miniflow.models.enums import CredentialType
from miniflow.core.exceptions import (
    ResourceNotFoundError,
    ResourceAlreadyExistsError,
    BusinessRuleViolationError,
    InvalidInputError,
)
from miniflow.core.logger import get_logger
from miniflow.utils.helpers.encryption_helper import encrypt_data, decrypt_data

# Logger instance
logger = get_logger(__name__)

class CredentialService:
    """
    Credential yönetim servisi.
    
    API credentials ve secrets'ların güvenli şekilde saklanmasını sağlar.
    NOT: workspace_exists kontrolü middleware'de yapılır.
    NOT: Credential verisi oluşturulduktan sonra DEĞİŞTİRİLEMEZ (sadece name, description)
    """
    _registry = RepositoryRegistry()
    _credential_repo = _registry.credential_repository()
    _workspace_repo = _registry.workspace_repository()

    # ==================================================================================== HELPERS ==
    @staticmethod
    def _encrypt_credential_data(data: Dict[str, Any]) -> str:
        """Credential verisini şifreler."""
        json_str = json.dumps(data, ensure_ascii=False)
        return encrypt_data(json_str)

    @staticmethod
    def _decrypt_credential_data(encrypted_data: str) -> Dict[str, Any]:
        """Şifrelenmiş credential verisini çözer."""
        try:
            if isinstance(encrypted_data, dict):
                return encrypted_data
            decrypted = decrypt_data(encrypted_data)
            return json.loads(decrypted)
        except Exception:
            return {}

    # ==================================================================================== CREATE API KEY ==
    @classmethod
    @with_transaction(manager=None)
    def create_api_key_credential(
        cls,
        session,
        *,
        workspace_id: str,
        owner_id: str,
        name: str,
        api_key: str,
        provider: str,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        expires_at: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        API Key tipi credential oluşturur.
        
        Örnek kullanım alanları:
        - OpenAI API Key
        - Google Maps API Key
        - Sendgrid API Key
        
        Args:
            workspace_id: Workspace ID'si
            owner_id: Sahip kullanıcı ID'si
            name: Credential adı (workspace içinde benzersiz)
            api_key: API key değeri
            provider: Provider adı (OPENAI, GOOGLE, SENDGRID, vb.)
            description: Açıklama (opsiyonel)
            tags: Etiketler (opsiyonel)
            expires_at: Son kullanma tarihi (opsiyonel)
            
        Returns:
            {"id": str}
        """
        # Validasyonlar
        if not name or not name.strip():
            raise InvalidInputError(
                field_name="name",
                message="Credential name cannot be empty"
            )
        if not api_key or not api_key.strip():
            raise InvalidInputError(
                field_name="api_key",
                message="API key cannot be empty"
            )
        if not provider or not provider.strip():
            raise InvalidInputError(
                field_name="provider",
                message="Provider cannot be empty"
            )
        
        # Benzersizlik kontrolü
        existing = cls._credential_repo._get_by_name(
            session, 
            workspace_id=workspace_id, 
            name=name
        )
        if existing:
            raise ResourceAlreadyExistsError(
                resource_name="Credential",
                conflicting_field="name",
                message=f"Credential with name '{name}' already exists in workspace {workspace_id}"
            )
        
        # Credential verisi
        credential_data = {
            "api_key": api_key
        }
        encrypted_data = cls._encrypt_credential_data(credential_data)
        
        # Credential oluştur
        credential = cls._credential_repo._create(
            session,
            workspace_id=workspace_id,
            owner_id=owner_id,
            name=name,
            credential_type=CredentialType.API_KEY,
            credential_provider=provider.upper(),
            description=description,
            credential_data=encrypted_data,
            is_active=True,
            expires_at=expires_at,
            tags=tags or [],
            created_by=owner_id
        )
        
        return {"id": credential.id}

    # ==================================================================================== CREATE SLACK ==
    @classmethod
    @with_transaction(manager=None)
    def create_slack_credential(
        cls,
        session,
        *,
        workspace_id: str,
        owner_id: str,
        name: str,
        bot_token: str,
        signing_secret: Optional[str] = None,
        app_token: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        expires_at: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Slack credential oluşturur.
        
        Args:
            workspace_id: Workspace ID'si
            owner_id: Sahip kullanıcı ID'si
            name: Credential adı (workspace içinde benzersiz)
            bot_token: Slack Bot Token (xoxb-...)
            signing_secret: Signing Secret (opsiyonel)
            app_token: App-Level Token (xapp-..., opsiyonel)
            description: Açıklama (opsiyonel)
            tags: Etiketler (opsiyonel)
            expires_at: Son kullanma tarihi (opsiyonel)
            
        Returns:
            {"id": str}
        """
        # Validasyonlar
        if not name or not name.strip():
            raise InvalidInputError(
                field_name="name",
                message="Credential name cannot be empty"
            )
        if not bot_token or not bot_token.strip():
            raise InvalidInputError(
                field_name="bot_token",
                message="Bot token cannot be empty"
            )
        
        # Bot token formatı kontrolü
        if not bot_token.startswith("xoxb-"):
            raise InvalidInputError(
                field_name="bot_token",
                message="Invalid bot token format. Should start with 'xoxb-'"
            )
        
        # Benzersizlik kontrolü
        existing = cls._credential_repo._get_by_name(
            session, 
            workspace_id=workspace_id, 
            name=name
        )
        if existing:
            raise ResourceAlreadyExistsError(
                resource_name="Credential",
                conflicting_field="name",
                message=f"Credential with name '{name}' already exists in workspace {workspace_id}"
            )
        
        # Credential verisi
        credential_data = {
            "bot_token": bot_token,
        }
        if signing_secret:
            credential_data["signing_secret"] = signing_secret
        if app_token:
            credential_data["app_token"] = app_token
        
        encrypted_data = cls._encrypt_credential_data(credential_data)
        
        # Credential oluştur
        credential = cls._credential_repo._create(
            session,
            workspace_id=workspace_id,
            owner_id=owner_id,
            name=name,
            credential_type=CredentialType.SLACK,
            credential_provider="SLACK",
            description=description,
            credential_data=encrypted_data,
            is_active=True,
            expires_at=expires_at,
            tags=tags or [],
            created_by=owner_id
        )
        
        return {"id": credential.id}

    # ==================================================================================== READ ==
    @classmethod
    @with_readonly_session(manager=None)
    def get_credential(
        cls,
        session,
        *,
        credential_id: str,
        include_secret: bool = False,
    ) -> Dict[str, Any]:
        """
        Credential detaylarını getirir.
        
        Args:
            credential_id: Credential ID'si
            include_secret: Gizli verileri dahil et (varsayılan: False)
            
        Returns:
            Credential detayları
        """
        credential = cls._credential_repo._get_by_id(session, record_id=credential_id)
        
        if not credential:
            raise ResourceNotFoundError(
                resource_name="Credential",
                resource_id=credential_id
            )
        
        result = {
            "id": credential.id,
            "workspace_id": credential.workspace_id,
            "owner_id": credential.owner_id,
            "name": credential.name,
            "credential_type": credential.credential_type.value if credential.credential_type else None,
            "credential_provider": credential.credential_provider,
            "description": credential.description,
            "is_active": credential.is_active,
            "expires_at": credential.expires_at.isoformat() if credential.expires_at else None,
            "last_used_at": credential.last_used_at.isoformat() if credential.last_used_at else None,
            "tags": credential.tags,
            "created_at": credential.created_at.isoformat() if credential.created_at else None
        }
        
        # Gizli verileri dahil et (workflow execution için)
        if include_secret:
            result["credential_data"] = cls._decrypt_credential_data(credential.credential_data)
        
        return result

    @classmethod
    @with_readonly_session(manager=None)
    def get_workspace_credentials(
        cls,
        session,
        *,
        workspace_id: str,
        credential_type: Optional[CredentialType] = None,
    ) -> Dict[str, Any]:
        """
        Workspace'in tüm credential'larını listeler.
        
        Args:
            workspace_id: Workspace ID'si
            credential_type: Filtre için credential tipi (opsiyonel)
            
        Returns:
            {"workspace_id": str, "credentials": List[Dict], "count": int}
        """
        if credential_type:
            credentials = cls._credential_repo._get_by_type(
                session, 
                workspace_id=workspace_id, 
                credential_type=credential_type
            )
        else:
            credentials = cls._credential_repo._get_all_by_workspace_id(
                session, 
                workspace_id=workspace_id
            )
        
        return {
            "workspace_id": workspace_id,
            "credentials": [
                {
                    "id": cred.id,
                    "name": cred.name,
                    "credential_type": cred.credential_type.value if cred.credential_type else None,
                    "credential_provider": cred.credential_provider,
                    "description": cred.description,
                    "is_active": cred.is_active,
                    "expires_at": cred.expires_at.isoformat() if cred.expires_at else None,
                    "last_used_at": cred.last_used_at.isoformat() if cred.last_used_at else None,
                    "tags": cred.tags
                }
                for cred in credentials
            ],
            "count": len(credentials)
        }

    # ==================================================================================== UPDATE ==
    @classmethod
    @with_transaction(manager=None)
    def update_credential(
        cls,
        session,
        *,
        credential_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Credential meta bilgilerini günceller.
        
        NOT: credential_data DEĞİŞTİRİLEMEZ! Yeni credential oluşturun.
        
        Args:
            credential_id: Credential ID'si
            name: Yeni ad (opsiyonel)
            description: Yeni açıklama (opsiyonel)
            tags: Yeni etiketler (opsiyonel)
            
        Returns:
            Güncellenmiş credential bilgileri
        """
        credential = cls._credential_repo._get_by_id(session, record_id=credential_id)
        
        if not credential:
            raise ResourceNotFoundError(
                resource_name="Credential",
                resource_id=credential_id
            )
        
        update_data = {}
        
        # Name değişikliği
        if name is not None and name != credential.name:
            if not name.strip():
                raise InvalidInputError(
                    field_name="name",
                    message="Credential name cannot be empty"
                )
            # Benzersizlik kontrolü
            existing = cls._credential_repo._get_by_name(
                session, 
                workspace_id=credential.workspace_id, 
                name=name
            )
            if existing and existing.id != credential_id:
                raise ResourceAlreadyExistsError(
                    resource_name="Credential",
                    conflicting_field="name",
                    message=f"Credential with name '{name}' already exists in workspace {workspace_id}"
                )
            update_data["name"] = name
        
        if description is not None:
            update_data["description"] = description
        if tags is not None:
            update_data["tags"] = tags
        
        if update_data:
            cls._credential_repo._update(session, record_id=credential_id, **update_data)
        
        return cls.get_credential(credential_id=credential_id)

    # ==================================================================================== ACTIVATE/DEACTIVATE ==
    @classmethod
    @with_transaction(manager=None)
    def deactivate_credential(
        cls,
        session,
        *,
        credential_id: str,
    ) -> Dict[str, Any]:
        """
        Credential'ı deaktive eder.
        
        Args:
            credential_id: Credential ID'si
            
        Returns:
            {"success": True}
        """
        credential = cls._credential_repo._get_by_id(session, record_id=credential_id)
        
        if not credential:
            raise ResourceNotFoundError(
                resource_name="Credential",
                resource_id=credential_id
            )
        
        cls._credential_repo._deactivate(session, credential_id=credential_id)
        
        return {"success": True, "is_active": False}

    @classmethod
    @with_transaction(manager=None)
    def activate_credential(
        cls,
        session,
        *,
        credential_id: str,
    ) -> Dict[str, Any]:
        """
        Credential'ı aktive eder.
        
        Args:
            credential_id: Credential ID'si
            
        Returns:
            {"success": True}
        """
        credential = cls._credential_repo._get_by_id(session, record_id=credential_id)
        
        if not credential:
            raise ResourceNotFoundError(
                resource_name="Credential",
                resource_id=credential_id
            )
        
        cls._credential_repo._activate(session, credential_id=credential_id)
        
        return {"success": True, "is_active": True}

    # ==================================================================================== DELETE ==
    @classmethod
    @with_transaction(manager=None)
    def delete_credential(
        cls,
        session,
        *,
        credential_id: str,
    ) -> Dict[str, Any]:
        """
        Credential'ı siler.
        
        Args:
            credential_id: Credential ID'si
            
        Returns:
            {"success": True, "deleted_id": str}
        """
        credential = cls._credential_repo._get_by_id(session, record_id=credential_id)
        
        if not credential:
            raise ResourceNotFoundError(
                resource_name="Credential",
                resource_id=credential_id
            )
        
        cls._credential_repo._delete(session, record_id=credential_id)
        
        return {
            "success": True,
            "deleted_id": credential_id
        }

    # ==================================================================================== USAGE TRACKING ==
    @classmethod
    @with_transaction(manager=None)
    def mark_as_used(
        cls,
        session,
        *,
        credential_id: str,
    ) -> None:
        """
        Credential kullanıldığını işaretler (last_used_at günceller).
        
        Args:
            credential_id: Credential ID'si
        """
        cls._credential_repo._update_last_used(session, credential_id=credential_id)

