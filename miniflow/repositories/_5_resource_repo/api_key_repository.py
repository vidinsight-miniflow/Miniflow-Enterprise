from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy.sql import select, func

from ..base_repository import BaseRepository
from miniflow.models import ApiKey
from miniflow.utils.helpers.encryption_helper import verify_password


class ApiKeyRepository(BaseRepository[ApiKey]):
    """Repository for ApiKey operations"""
    
    def __init__(self):
        super().__init__(ApiKey)

    @BaseRepository._handle_db_exceptions
    def _get_by_name(
        self,
        session: Session,
        *,
        workspace_id: str,
        name: str,
        include_deleted: bool = False
    ) -> Optional[ApiKey]:
        """Get API key by workspace_id and name"""
        query = select(ApiKey).where(
            ApiKey.workspace_id == workspace_id,
            ApiKey.name == name
        )
        query = self._apply_soft_delete_filter(query, include_deleted)
        return session.execute(query).scalar_one_or_none()

    @BaseRepository._handle_db_exceptions
    def _get_by_key_hash(
        self,
        session: Session,
        *,
        key_hash: str,
        include_deleted: bool = False
    ) -> Optional[ApiKey]:
        """Get API key by key hash"""
        query = select(ApiKey).where(ApiKey.key_hash == key_hash)
        query = self._apply_soft_delete_filter(query, include_deleted)
        return session.execute(query).scalar_one_or_none()

    @BaseRepository._handle_db_exceptions
    def _get_by_api_key(
        self,
        session: Session,
        *,
        full_api_key: str,
        include_deleted: bool = False
    ) -> Optional[ApiKey]:
        """
        Get API key by full API key string.
        This method checks all possible key hashes by trying to verify the key.
        """
        query = select(ApiKey).where(ApiKey.is_active == True)
        query = self._apply_soft_delete_filter(query, include_deleted)
        api_keys = session.execute(query).scalars().all()
        
        for api_key in api_keys:
            if verify_password(full_api_key, api_key.key_hash):
                return api_key
        
        return None

    @BaseRepository._handle_db_exceptions
    def _get_all_by_workspace_id(
        self,
        session: Session,
        workspace_id: str,
        include_deleted: bool = False
    ) -> List[ApiKey]:
        """Get all API keys by workspace_id"""
        query = select(ApiKey).where(ApiKey.workspace_id == workspace_id)
        query = self._apply_soft_delete_filter(query, include_deleted)
        return list(session.execute(query).scalars().all())

    @BaseRepository._handle_db_exceptions
    def _count_by_workspace_id(
        self,
        session: Session,
        workspace_id: str,
        include_deleted: bool = False
    ) -> int:
        """Count API keys by workspace_id"""
        query = select(func.count(ApiKey.id)).where(ApiKey.workspace_id == workspace_id)
        query = self._apply_soft_delete_filter(query, include_deleted)
        return session.execute(query).scalar() or 0

    @BaseRepository._handle_db_exceptions
    def _update_last_used(
        self,
        session: Session,
        api_key_id: str
    ) -> None:
        """Update last used timestamp and increment usage count"""
        api_key = self._get_by_id(session, record_id=api_key_id)
        if api_key:
            api_key.last_used_at = datetime.now(timezone.utc)
            api_key.usage_count += 1

    @BaseRepository._handle_db_exceptions
    def _deactivate(
        self,
        session: Session,
        api_key_id: str
    ) -> None:
        """Deactivate API key"""
        api_key = self._get_by_id(session, record_id=api_key_id)
        if api_key:
            api_key.is_active = False

    @BaseRepository._handle_db_exceptions
    def _activate(
        self,
        session: Session,
        api_key_id: str
    ) -> None:
        """Activate API key"""
        api_key = self._get_by_id(session, record_id=api_key_id)
        if api_key:
            api_key.is_active = True