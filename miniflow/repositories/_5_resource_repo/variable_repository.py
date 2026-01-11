from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.sql import select, func

from ..base_repository import BaseRepository
from miniflow.models import Variable


class VariableRepository(BaseRepository[Variable]):
    """Repository for Variable operations"""
    
    def __init__(self):
        super().__init__(Variable)

    @BaseRepository._handle_db_exceptions
    def _get_by_key(
        self,
        session: Session,
        *,
        workspace_id: str,
        key: str,
        include_deleted: bool = False
    ) -> Optional[Variable]:
        query = select(Variable).where(
            Variable.workspace_id == workspace_id,
            Variable.key == key
        )
        query = self._apply_soft_delete_filter(query, include_deleted)
        return session.execute(query).scalar_one_or_none()

    @BaseRepository._handle_db_exceptions
    def _get_all_by_workspace_id(
        self,
        session: Session,
        workspace_id: str,
        include_deleted: bool = False
    ) -> List[Variable]:
        """Get all variables by workspace_id"""
        query = select(Variable).where(Variable.workspace_id == workspace_id)
        query = self._apply_soft_delete_filter(query, include_deleted)
        return list(session.execute(query).scalars().all())

    @BaseRepository._handle_db_exceptions
    def _count_by_workspace_id(
        self,
        session: Session,
        workspace_id: str,
        include_deleted: bool = False
    ) -> int:
        """Count variables by workspace_id"""
        query = select(func.count(Variable.id)).where(Variable.workspace_id == workspace_id)
        query = self._apply_soft_delete_filter(query, include_deleted)
        return session.execute(query).scalar() or 0

    @BaseRepository._handle_db_exceptions
    def _get_secrets_by_workspace_id(
        self,
        session: Session,
        workspace_id: str,
        include_deleted: bool = False
    ) -> List[Variable]:
        """Get secret variables by workspace_id"""
        query = select(Variable).where(
            Variable.workspace_id == workspace_id,
            Variable.is_secret == True
        )
        query = self._apply_soft_delete_filter(query, include_deleted)
        return list(session.execute(query).scalars().all())