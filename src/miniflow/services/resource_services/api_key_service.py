from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import secrets

from src.miniflow.database import RepositoryRegistry, with_transaction, with_readonly_session
from src.miniflow.database.utils.pagination_params import PaginationParams
from src.miniflow.core.exceptions import (
    ResourceNotFoundError,
    ResourceAlreadyExistsError,
    InvalidInputError,
)
from src.miniflow.utils.helpers.encryption_helper import hash_password, verify_password


default_permissions = {
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
    def __init__(self):
        self._registry = RepositoryRegistry()
        self._api_key_repo = self._registry.api_key_repository
        self._workspace_repo = self._registry.workspace_repository
        self._plan_repo = self._registry.workspace_plans_repository
        self._user_repo = self._registry.user_repository

    @with_readonly_session(manager=None)
    def validate_api_key(self, session, *, full_api_key: str) -> Optional[Dict[str, Any]]:
        """
        Validate API key and return workspace info if valid
        """

        record = self._api_key_repo._get_by_api_key(session, full_api_key=full_api_key, include_deleted=False)
        if not record:
            return None
        
        # Check if API key is active and not expired
        if not record.is_active:
            return None
        
        if record.expires_at and record.expires_at < datetime.now(timezone.utc):
            return None
        
        workspace_id = record.workspace_id
        workspace = self._workspace_repo._get_by_id(session, record_id=workspace_id, include_deleted=False)
        if not workspace:
            return None
        
        # Check workspace is active and not suspended
        if not workspace.is_active or workspace.is_suspended:
            return None
        
        return {
            "valid": True,
            "workspace_id": workspace.id,
            "workspace_plan_id": workspace.plan_id,
            "permissions": record.permissions,
            "api_key_id": record.id,
        }

    @with_transaction(manager=None)
    def create_api_key(
        self,
        session,
        *,
        workspace_id: str,
        owner_id: str,
        name: str,
        key_prefix: str = "sk_live_",
        description: Optional[str] = None,
        permissions: Optional[Dict[str, Any]] = None,
        expires_at: Optional[datetime] = None,
        tags: Optional[List[str]] = None,
        allowed_ips: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        # Validate inputs
        if not name or not name.strip():
            raise InvalidInputError(field_name="name", message="API key name cannot be empty")
        
        # Validate workspace exists
        workspace = self._workspace_repo._get_by_id(session, record_id=workspace_id, include_deleted=False)
        if not workspace:
            raise ResourceNotFoundError(resource_name="workspace", resource_id=workspace_id)
        
        # Validate user exists
        user = self._user_repo._get_by_id(session, record_id=owner_id, include_deleted=False)
        if not user:
            raise ResourceNotFoundError(resource_name="user", resource_id=owner_id)
        
        # Check API key limit
        if workspace.current_api_key_count >= workspace.api_key_limit:
            raise InvalidInputError(
                field_name="workspace_id",
                message=f"API key limit reached. Maximum: {workspace.api_key_limit}, Current: {workspace.current_api_key_count}"
            )
        
        # Check if name already exists in workspace
        existing = self._api_key_repo._get_by_name(
            session, workspace_id=workspace_id, name=name, include_deleted=False
        )
        if existing:
            raise ResourceAlreadyExistsError(
                resource_name="api_key",
                conflicting_field="name",
                message=f"API key with name '{name}' already exists in this workspace"
            )
        
        # Generate API key
        api_key_secret = secrets.token_urlsafe(32)
        full_api_key = f"{key_prefix}{api_key_secret}"
        key_hash = hash_password(full_api_key)
        
        # Ensure key hash is unique (very unlikely collision, but check anyway)
        max_retries = 5
        retry_count = 0
        while self._api_key_repo._get_by_key_hash(session, key_hash=key_hash, include_deleted=False) and retry_count < max_retries:
            api_key_secret = secrets.token_urlsafe(32)
            full_api_key = f"{key_prefix}{api_key_secret}"
            key_hash = hash_password(full_api_key)
            retry_count += 1
        
        if retry_count >= max_retries:
            raise InvalidInputError(
                field_name="api_key",
                message="Failed to generate unique API key after multiple attempts"
            )
        
        # Create API key
        api_key = self._api_key_repo._create(
            session,
            workspace_id=workspace_id,
            owner_id=owner_id,
            name=name,
            key_prefix=key_prefix,
            key_hash=key_hash,
            description=description,
            permissions=permissions or default_permissions,
            tags=tags or [],
            allowed_ips=allowed_ips or [],
            is_active=True,
            expires_at=expires_at,
            created_by=owner_id,
        )
        
        # Update workspace API key count
        workspace.current_api_key_count += 1
        session.flush()
        
        return {
            "api_key": full_api_key,
            "id": api_key.id,
        }

    @with_readonly_session(manager=None)
    def get_api_key(
        self,
        session,
        *,
        api_key_id: str,
        workspace_id: str
    ) -> Dict[str, Any]:
        """Get API key by ID (masked)"""
        api_key = self._api_key_repo._get_by_id(session, record_id=api_key_id, include_deleted=False)
        if not api_key:
            raise ResourceNotFoundError(resource_name="api_key", resource_id=api_key_id)
        
        if api_key.workspace_id != workspace_id:
            raise ResourceNotFoundError(
                resource_name="api_key",
                message="API key not found in this workspace"
            )
        
        return {
            "id": api_key.id,
            "api_key": api_key.key_prefix + "****",
            "name": api_key.name,
            "description": api_key.description,
            "is_active": api_key.is_active,
            "expires_at": api_key.expires_at,
            "last_used_at": api_key.last_used_at,
            "usage_count": api_key.usage_count,
            "allowed_ips": api_key.allowed_ips,
            "tags": api_key.tags,
            "permissions": api_key.permissions,
        }

    @with_transaction(manager=None)
    def update_api_key(
        self,
        session,
        *,
        api_key_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        permissions: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        allowed_ips: Optional[List[str]] = None,
        is_active: Optional[bool] = None,
        expires_at: Optional[datetime] = None,
        updated_by: str,
    ) -> Dict[str, Any]:
        """Update API key"""
        api_key = self._api_key_repo._get_by_id(session, record_id=api_key_id, include_deleted=False)
        if not api_key:
            raise ResourceNotFoundError(resource_name="api_key", resource_id=api_key_id)
        
        # Validate name if provided and different
        if name is not None and name != api_key.name:
            if not name or not name.strip():
                raise InvalidInputError(field_name="name", message="API key name cannot be empty")
            
            # Check if new name already exists in workspace
            existing = self._api_key_repo._get_by_name(
                session, workspace_id=api_key.workspace_id, name=name, include_deleted=False
            )
            if existing and existing.id != api_key_id:
                raise ResourceAlreadyExistsError(
                    resource_name="api_key",
                    conflicting_field="name",
                    message=f"API key with name '{name}' already exists in this workspace"
                )
        
        # Update fields
        update_data = {}
        if name is not None:
            update_data["name"] = name
        if description is not None:
            update_data["description"] = description
        if permissions is not None:
            update_data["permissions"] = permissions
        if tags is not None:
            update_data["tags"] = tags
        if allowed_ips is not None:
            update_data["allowed_ips"] = allowed_ips
        if is_active is not None:
            update_data["is_active"] = is_active
        if expires_at is not None:
            update_data["expires_at"] = expires_at
        
        update_data["updated_by"] = updated_by
        
        updated_api_key = self._api_key_repo._update(session, record_id=api_key_id, **update_data)
        
        return {
            "id": updated_api_key.id,
            "api_key": updated_api_key.key_prefix + "****",
            "name": updated_api_key.name,
            "description": updated_api_key.description,
            "is_active": updated_api_key.is_active,
            "expires_at": updated_api_key.expires_at,
            "last_used_at": updated_api_key.last_used_at,
            "usage_count": updated_api_key.usage_count,
            "allowed_ips": updated_api_key.allowed_ips,
            "tags": updated_api_key.tags,
            "permissions": updated_api_key.permissions,
        }

    @with_transaction(manager=None)
    def delete_api_key(
        self,
        session,
        *,
        api_key_id: str,
    ) -> Dict[str, Any]:
        """Delete API key"""
        api_key = self._api_key_repo._get_by_id(session, record_id=api_key_id, include_deleted=False)
        if not api_key:
            raise ResourceNotFoundError(resource_name="api_key", resource_id=api_key_id)
        
        workspace = self._workspace_repo._get_by_id(session, record_id=api_key.workspace_id, include_deleted=False)
        if not workspace:
            raise ResourceNotFoundError(resource_name="workspace", resource_id=api_key.workspace_id)
        
        self._api_key_repo._delete(session, record_id=api_key_id)
        
        # Update workspace API key count
        workspace.current_api_key_count = max(0, workspace.current_api_key_count - 1)
        session.flush()
        
        return {
            "deleted": True,
            "api_key_id": api_key_id
        }

    @with_readonly_session(manager=None)
    def get_all_api_keys(
        self,
        session,
        *,
        workspace_id: str,
        page: int = 1,
        page_size: int = 100,
        order_by: Optional[str] = None,
        order_desc: bool = False,
        include_deleted: bool = False
    ) -> Dict[str, Any]:
        """Get all API keys with pagination"""
        # Validate workspace exists
        workspace = self._workspace_repo._get_by_id(session, record_id=workspace_id, include_deleted=False)
        if not workspace:
            raise ResourceNotFoundError(resource_name="workspace", resource_id=workspace_id)
        
        pagination_params = PaginationParams(
            page=page,
            page_size=page_size,
            order_by=order_by or "created_at",
            order_desc=order_desc,
            include_deleted=include_deleted
        )
        pagination_params.validate()
        
        result = self._api_key_repo._paginate(
            session,
            pagination_params=pagination_params,
            workspace_id=workspace_id
        )
        
        items = []
        for api_key in result.items:
            items.append({
                "id": api_key.id,
                "api_key": api_key.key_prefix + "****",
                "name": api_key.name,
                "description": api_key.description,
                "is_active": api_key.is_active,
                "expires_at": api_key.expires_at,
                "last_used_at": api_key.last_used_at,
                "usage_count": api_key.usage_count,
                "allowed_ips": api_key.allowed_ips,
                "tags": api_key.tags,
                "permissions": api_key.permissions,
            })
        
        return {
            "items": items,
            "metadata": result.metadata.to_dict()
        }

