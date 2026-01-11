from typing import Optional, Dict, Any, List

from miniflow.database import RepositoryRegistry, with_transaction, with_readonly_session
from miniflow.core.exceptions import (
    ResourceNotFoundError,
    ResourceAlreadyExistsError,
    InvalidInputError,
)
from miniflow.core.logger import get_logger
from miniflow.utils.helpers.encryption_helper import encrypt_data, decrypt_data

# Logger instance
logger = get_logger(__name__)


class VariableService:
    """
    Environment variable yönetim servisi.
    
    Workspace environment variable'larının oluşturulması ve yönetimini sağlar.
    NOT: workspace_exists kontrolü middleware'de yapılır.
    """
    _registry = RepositoryRegistry()
    _variable_repo = _registry.variable_repository()
    _workspace_repo = _registry.workspace_repository()

    # ==================================================================================== CREATE ==
    @classmethod
    @with_transaction(manager=None)
    def create_variable(
        cls,
        session,
        *,
        workspace_id: str,
        owner_id: str,
        key: str,
        value: str,
        description: Optional[str] = None,
        is_secret: bool = False,
    ) -> Dict[str, Any]:
        """
        Environment variable oluşturur.
        
        Args:
            workspace_id: Workspace ID'si
            owner_id: Sahip kullanıcı ID'si
            key: Variable anahtarı (workspace içinde benzersiz)
            value: Variable değeri
            description: Açıklama (opsiyonel)
            is_secret: Gizli mi? (True ise şifrelenir)
            
        Returns:
            {"id": str}
        """
        # Validasyonlar
        if not key or not key.strip():
            raise InvalidInputError(
                field_name="key",
                message="Variable key cannot be empty"
            )
        if value is None:
            raise InvalidInputError(
                field_name="value",
                message="Variable value cannot be None"
            )
        
        # Benzersizlik kontrolü
        existing = cls._variable_repo._get_by_key(
            session, 
            workspace_id=workspace_id, 
            key=key
        )
        if existing:
            raise ResourceAlreadyExistsError(
                resource_name="Variable",
                conflicting_field="key",
                message=f"Variable with key '{key}' already exists in workspace {workspace_id}"
            )
        
        # Şifreleme (secret ise)
        stored_value = encrypt_data(value) if is_secret else value
        
        # Variable oluştur
        variable = cls._variable_repo._create(
            session,
            workspace_id=workspace_id,
            owner_id=owner_id,
            key=key,
            value=stored_value,
            description=description,
            is_secret=is_secret,
            created_by=owner_id
        )
        
        return {"id": variable.id}

    # ==================================================================================== READ ==
    @classmethod
    @with_readonly_session(manager=None)
    def get_variable(
        cls,
        session,
        *,
        variable_id: str,
        decrypt_secret: bool = False,
    ) -> Dict[str, Any]:
        """
        Variable detaylarını getirir.
        
        Args:
            variable_id: Variable ID'si
            decrypt_secret: Secret değeri çöz (varsayılan: False)
            
        Returns:
            Variable detayları
        """
        variable = cls._variable_repo._get_by_id(session, record_id=variable_id, raise_not_found=True)
        
        # Değer
        if variable.is_secret:
            if decrypt_secret:
                value = decrypt_data(variable.value)
            else:
                value = "********"
        else:
            value = variable.value
        
        return {
            "id": variable.id,
            "workspace_id": variable.workspace_id,
            "owner_id": variable.owner_id,
            "key": variable.key,
            "value": value,
            "description": variable.description,
            "is_secret": variable.is_secret,
            "created_at": variable.created_at.isoformat() if variable.created_at else None
        }

    @classmethod
    @with_readonly_session(manager=None)
    def get_variable_by_key(
        cls,
        session,
        *,
        workspace_id: str,
        key: str,
        decrypt_secret: bool = False,
    ) -> Dict[str, Any]:
        """
        Key ile variable getirir.
        
        Args:
            workspace_id: Workspace ID'si
            key: Variable anahtarı
            decrypt_secret: Secret değeri çöz (varsayılan: False)
            
        Returns:
            Variable detayları
        """
        variable = cls._variable_repo._get_by_key(
            session, 
            workspace_id=workspace_id, 
            key=key
        )
        
        if not variable:
            raise ResourceNotFoundError(
                resource_name="Variable",
                resource_id=key
            )
        
        # Değer
        if variable.is_secret:
            if decrypt_secret:
                value = decrypt_data(variable.value)
            else:
                value = "********"
        else:
            value = variable.value
        
        return {
            "id": variable.id,
            "workspace_id": variable.workspace_id,
            "key": variable.key,
            "value": value,
            "description": variable.description,
            "is_secret": variable.is_secret
        }

    @classmethod
    @with_readonly_session(manager=None)
    def get_workspace_variables(
        cls,
        session,
        *,
        workspace_id: str,
    ) -> Dict[str, Any]:
        """
        Workspace'in tüm variable'larını listeler.
        
        Args:
            workspace_id: Workspace ID'si
            
        Returns:
            {"workspace_id": str, "variables": List[Dict], "count": int}
        """
        variables = cls._variable_repo._get_all_by_workspace_id(
            session, 
            workspace_id=workspace_id
        )
        
        return {
            "workspace_id": workspace_id,
            "variables": [
                {
                    "id": v.id,
                    "key": v.key,
                    "value": "********" if v.is_secret else v.value,
                    "description": v.description,
                    "is_secret": v.is_secret,
                    "created_at": v.created_at.isoformat() if v.created_at else None
                }
                for v in variables
            ],
            "count": len(variables)
        }

    # ==================================================================================== UPDATE ==
    @classmethod
    @with_transaction(manager=None)
    def update_variable(
        cls,
        session,
        *,
        variable_id: str,
        key: Optional[str] = None,
        value: Optional[str] = None,
        description: Optional[str] = None,
        is_secret: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Variable günceller.
        
        Args:
            variable_id: Variable ID'si
            key: Yeni anahtar (opsiyonel)
            value: Yeni değer (opsiyonel)
            description: Yeni açıklama (opsiyonel)
            is_secret: Yeni gizlilik durumu (opsiyonel)
            
        Returns:
            Güncellenmiş variable bilgileri
        """
        variable = cls._variable_repo._get_by_id(session, record_id=variable_id, raise_not_found=True)
        
        update_data = {}
        
        # Key değişikliği
        if key is not None and key != variable.key:
            if not key.strip():
                raise InvalidInputError(
                    field_name="key",
                    message="Variable key cannot be empty"
                )
            # Benzersizlik kontrolü
            existing = cls._variable_repo._get_by_key(
                session, 
                workspace_id=variable.workspace_id, 
                key=key
            )
            if existing and existing.id != variable_id:
                raise ResourceAlreadyExistsError(
                    resource_name="Variable",
                    conflicting_field="key",
                    message=f"Variable with key '{key}' already exists in workspace {variable.workspace_id}"
                )
            update_data["key"] = key
        
        # is_secret değişikliği
        is_secret_changed = is_secret is not None and is_secret != variable.is_secret
        if is_secret_changed:
            update_data["is_secret"] = is_secret
            # Mevcut değeri yeniden şifrele/çöz
            if variable.is_secret and not is_secret:
                # Secret'tan plain'e
                current_value = decrypt_data(variable.value)
                update_data["value"] = current_value
            elif not variable.is_secret and is_secret:
                # Plain'den secret'a
                update_data["value"] = encrypt_data(variable.value)
        
        # Value değişikliği
        if value is not None:
            # Güncel is_secret durumuna göre şifrele
            current_is_secret = update_data.get("is_secret", variable.is_secret)
            update_data["value"] = encrypt_data(value) if current_is_secret else value
        
        if description is not None:
            update_data["description"] = description
        
        if update_data:
            cls._variable_repo._update(session, record_id=variable_id, **update_data)
        
        return cls.get_variable(variable_id=variable_id)

    # ==================================================================================== DELETE ==
    @classmethod
    @with_transaction(manager=None)
    def delete_variable(
        cls,
        session,
        *,
        variable_id: str,
    ) -> Dict[str, Any]:
        """
        Variable siler.
        
        Args:
            variable_id: Variable ID'si
            
        Returns:
            {"success": True, "deleted_id": str}
        """
        variable = cls._variable_repo._get_by_id(session, record_id=variable_id, raise_not_found=True)
        
        cls._variable_repo._delete(session, record_id=variable_id)
        
        return {
            "success": True,
            "deleted_id": variable_id
        }

