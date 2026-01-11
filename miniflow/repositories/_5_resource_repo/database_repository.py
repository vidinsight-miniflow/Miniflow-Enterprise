from typing import List, Union, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy.sql import select, func

from ..base_repository import BaseRepository
from miniflow.models import Database
from miniflow.models.enums import DatabaseType


class DatabaseRepository(BaseRepository[Database]):
    """Repository for Database operations"""
    
    def __init__(self):
        super().__init__(Database)

    @BaseRepository._handle_db_exceptions
    def _get_by_name(
        self,
        session: Session,
        *,
        workspace_id: str,
        name: str,
        include_deleted: bool = False
    ) -> Optional[Database]:
        query = select(Database).where(
            Database.workspace_id == workspace_id,
            Database.name == name
        )
        query = self._apply_soft_delete_filter(query, include_deleted)
        return session.execute(query).scalar_one_or_none()

    @BaseRepository._handle_db_exceptions
    def _get_all_by_workspace_id(
        self,
        session: Session,
        workspace_id: str,
        include_deleted: bool = False
    ) -> List[Database]:
        """Get all databases by workspace_id"""
        query = select(Database).where(Database.workspace_id == workspace_id)
        query = self._apply_soft_delete_filter(query, include_deleted)
        return list(session.execute(query).scalars().all())

    @BaseRepository._handle_db_exceptions
    def _count_by_workspace_id(
        self,
        session: Session,
        workspace_id: str,
        include_deleted: bool = False
    ) -> int:
        """Count databases by workspace_id"""
        query = select(func.count(Database.id)).where(Database.workspace_id == workspace_id)
        query = self._apply_soft_delete_filter(query, include_deleted)
        return session.execute(query).scalar() or 0

    @BaseRepository._handle_db_exceptions
    def _get_by_type(
        self,
        session: Session,
        *,
        workspace_id: str,
        database_type: DatabaseType,
        include_deleted: bool = False
    ) -> List[Database]:
        """Get databases by type"""
        query = select(Database).where(
            Database.workspace_id == workspace_id,
            Database.database_type == database_type
        )
        query = self._apply_soft_delete_filter(query, include_deleted)
        return list(session.execute(query).scalars().all())

    @BaseRepository._handle_db_exceptions
    def _update_test_status(
        self,
        session: Session,
        database_id: str,
        status: str
    ) -> None:
        """Update test status"""
        database = self._get_by_id(session, record_id=database_id)
        if database:
            database.last_tested_at = datetime.now(timezone.utc)
            database.last_test_status = status

    @BaseRepository._handle_db_exceptions
    def _deactivate(
        self,
        session: Session,
        database_id: str
    ) -> None:
        """Deactivate database"""
        database = self._get_by_id(session, record_id=database_id)
        if database:
            database.is_active = False

    @BaseRepository._handle_db_exceptions
    def _activate(
        self,
        session: Session,
        database_id: str
    ) -> None:
        """Activate database"""
        database = self._get_by_id(session, record_id=database_id)
        if database:
            database.is_active = True