from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy.sql import select, func

from ..base_repository import BaseRepository
from miniflow.models import Execution
from miniflow.models.enums import ExecutionStatus


class ExecutionRepository(BaseRepository[Execution]):
    """Repository for managing workflow executions"""
    
    def __init__(self):
        super().__init__(Execution)

    @BaseRepository._handle_db_exceptions
    def _get_all_by_workspace_id(
        self,
        session: Session,
        workspace_id: str,
        include_deleted: bool = False
    ) -> List[Execution]:
        """Get all executions by workspace_id"""
        query = select(Execution).where(Execution.workspace_id == workspace_id)
        query = self._apply_soft_delete_filter(query, include_deleted)
        return list(session.execute(query).scalars().all())

    @BaseRepository._handle_db_exceptions
    def _get_all_by_workflow_id(
        self,
        session: Session,
        workflow_id: str,
        include_deleted: bool = False
    ) -> List[Execution]:
        """Get all executions by workflow_id"""
        query = select(Execution).where(Execution.workflow_id == workflow_id)
        query = self._apply_soft_delete_filter(query, include_deleted)
        return list(session.execute(query).scalars().all())

    @BaseRepository._handle_db_exceptions
    def _get_by_status(
        self,
        session: Session,
        *,
        workspace_id: str,
        status: ExecutionStatus,
        include_deleted: bool = False
    ) -> List[Execution]:
        """Get executions by status"""
        query = select(Execution).where(
            Execution.workspace_id == workspace_id,
            Execution.status == status
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
        """Count executions by workspace_id"""
        query = select(func.count(Execution.id)).where(Execution.workspace_id == workspace_id)
        query = self._apply_soft_delete_filter(query, include_deleted)
        return session.execute(query).scalar() or 0

    @BaseRepository._handle_db_exceptions
    def _count_by_status(
        self,
        session: Session,
        *,
        workspace_id: str,
        status: ExecutionStatus,
        include_deleted: bool = False
    ) -> int:
        """Count executions by status"""
        query = select(func.count(Execution.id)).where(
            Execution.workspace_id == workspace_id,
            Execution.status == status
        )
        query = self._apply_soft_delete_filter(query, include_deleted)
        return session.execute(query).scalar() or 0

    @BaseRepository._handle_db_exceptions
    def _update_status(
        self,
        session: Session,
        *,
        execution_id: str,
        status: ExecutionStatus,
        ended_at: Optional[datetime] = None,
        results: Optional[dict] = None
    ) -> Optional[Execution]:
        """Update execution status"""
        execution = self._get_by_id(session, record_id=execution_id)
        if execution:
            execution.status = status
            if ended_at is not None:
                execution.ended_at = ended_at
            if results is not None:
                execution.results = results
            return execution
        return None

    @BaseRepository._handle_db_exceptions
    def _get_pending_executions(
        self,
        session: Session,
        include_deleted: bool = False
    ) -> List[Execution]:
        """Get all pending executions"""
        query = select(Execution).where(Execution.status == ExecutionStatus.PENDING)
        query = self._apply_soft_delete_filter(query, include_deleted)
        return list(session.execute(query).scalars().all())

    @BaseRepository._handle_db_exceptions
    def _get_running_executions(
        self,
        session: Session,
        include_deleted: bool = False
    ) -> List[Execution]:
        """Get all running executions"""
        query = select(Execution).where(Execution.status == ExecutionStatus.RUNNING)
        query = self._apply_soft_delete_filter(query, include_deleted)
        return list(session.execute(query).scalars().all())