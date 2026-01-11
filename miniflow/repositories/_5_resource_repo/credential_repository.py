from typing import List, Union, Optional
from datetime import datetime, timezone
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from ..base_repository import BaseRepository
from miniflow.models import Credential
from miniflow.models.enums import CredentialType


class CredentialRepository(BaseRepository[Credential]):
    def __init__(self):
        super().__init__(Credential)

    @BaseRepository._handle_db_exceptions
    def _get_by_name(
        self,
        session: Session,
        *,
        workspace_id: str,
        name: str,
        include_deleted: bool = False
    ) -> Optional[Credential]:
        """Get credential by workspace_id and name."""
        query = select(Credential).where(
            Credential.workspace_id == workspace_id,
            Credential.name == name
        )
        query = self._apply_soft_delete_filter(query, include_deleted)
        return session.execute(query).scalar_one_or_none()

    @BaseRepository._handle_db_exceptions
    def _get_all_by_workspace_id(
        self,
        session: Session,
        workspace_id: str,
        include_deleted: bool = False
    ) -> List[Credential]:
        """Get all credentials by workspace_id"""
        query = select(Credential).where(Credential.workspace_id == workspace_id)
        query = self._apply_soft_delete_filter(query, include_deleted)
        return list(session.execute(query).scalars().all())

    @BaseRepository._handle_db_exceptions
    def _get_by_type(
        self,
        session: Session,
        *,
        workspace_id: str,
        credential_type: CredentialType,
        include_deleted: bool = False
    ) -> List[Credential]:
        """Get credentials by type"""
        query = select(Credential).where(
            Credential.workspace_id == workspace_id,
            Credential.credential_type == credential_type
        )
        query = self._apply_soft_delete_filter(query, include_deleted)
        return list(session.execute(query).scalars().all())

    @BaseRepository._handle_db_exceptions
    def _count_by_workspace_id(
        self,
        session: Session,
        workspace_id: str,
        include_deleted: bool = False
    ) -> int:
        """Count credentials by workspace_id"""
        query = select(func.count(Credential.id)).where(Credential.workspace_id == workspace_id)
        query = self._apply_soft_delete_filter(query, include_deleted)
        return session.execute(query).scalar() or 0

    @BaseRepository._handle_db_exceptions
    def _update_last_used(
        self,
        session: Session,
        credential_id: str
    ) -> None:
        """Update last used timestamp"""
        credential = self._get_by_id(session, record_id=credential_id)
        if credential:
            credential.last_used_at = datetime.now(timezone.utc)

    @BaseRepository._handle_db_exceptions
    def _deactivate(
        self,
        session: Session,
        credential_id: str
    ) -> None:
        """Deactivate credential"""
        credential = self._get_by_id(session, record_id=credential_id)
        if credential:
            credential.is_active = False

    @BaseRepository._handle_db_exceptions
    def _activate(
        self,
        session: Session,
        credential_id: str
    ) -> None:
        """Activate credential"""
        credential = self._get_by_id(session, record_id=credential_id)
        if credential:
            credential.is_active = True
