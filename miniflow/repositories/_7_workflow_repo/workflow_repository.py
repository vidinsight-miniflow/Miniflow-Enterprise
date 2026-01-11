from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.sql import select, func

from ..base_repository import BaseRepository
from miniflow.models import Workflow
from miniflow.models.enums import WorkflowStatus


class WorkflowRepository(BaseRepository[Workflow]):    
    def __init__(self):
        super().__init__(Workflow)

    @BaseRepository._handle_db_exceptions
    def _get_by_name(
        self,
        session: Session,
        *,
        workspace_id: str,
        name: str,
        include_deleted: bool = False
    ) -> Optional[Workflow]:
        """Get workflow by workspace_id and name"""
        query = select(Workflow).where(
            Workflow.workspace_id == workspace_id,
            Workflow.name == name
        )
        query = self._apply_soft_delete_filter(query, include_deleted)
        return session.execute(query).scalar_one_or_none()

    @BaseRepository._handle_db_exceptions
    def _get_all_by_workspace_id(
        self,
        session: Session,
        workspace_id: str,
        include_deleted: bool = False
    ) -> List[Workflow]:
        """Get all workflows by workspace_id"""
        query = select(Workflow).where(Workflow.workspace_id == workspace_id)
        query = self._apply_soft_delete_filter(query, include_deleted)
        return list(session.execute(query).scalars().all())

    @BaseRepository._handle_db_exceptions
    def _count_by_workspace_id(
        self,
        session: Session,
        workspace_id: str,
        include_deleted: bool = False
    ) -> int:
        """Count workflows by workspace_id"""
        query = select(func.count(Workflow.id)).where(Workflow.workspace_id == workspace_id)
        query = self._apply_soft_delete_filter(query, include_deleted)
        return session.execute(query).scalar() or 0

    @BaseRepository._handle_db_exceptions
    def _get_by_status(
        self,
        session: Session,
        *,
        workspace_id: str,
        status: WorkflowStatus,
        include_deleted: bool = False
    ) -> List[Workflow]:
        """Get workflows by status"""
        query = select(Workflow).where(
            Workflow.workspace_id == workspace_id,
            Workflow.status == status
        )
        query = self._apply_soft_delete_filter(query, include_deleted)
        return list(session.execute(query).scalars().all())

    @BaseRepository._handle_db_exceptions
    def _get_active_workflows(
        self,
        session: Session,
        workspace_id: str,
        include_deleted: bool = False
    ) -> List[Workflow]:
        """Get active workflows"""
        return self._get_by_status(
            session,
            workspace_id=workspace_id,
            status=WorkflowStatus.ACTIVE,
            include_deleted=include_deleted
        )

    @BaseRepository._handle_db_exceptions
    def _update_status(
        self,
        session: Session,
        *,
        workflow_id: str,
        status: WorkflowStatus,
        status_message: Optional[str] = None
    ) -> Optional[Workflow]:
        """Update workflow status"""
        workflow = self._get_by_id(session, record_id=workflow_id)
        if workflow:
            workflow.status = status
            if status_message is not None:
                workflow.status_message = status_message
            return workflow
        return None