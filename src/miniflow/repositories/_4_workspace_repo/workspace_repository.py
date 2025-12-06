from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy import select, and_, func
from sqlalchemy.orm import Session

from ..base_repository import BaseRepository
from miniflow.models import Workspace


class WorkspaceRepository(BaseRepository[Workspace]):
    def __init__(self):
        super().__init__(Workspace)

    @BaseRepository._handle_db_exceptions
    def _get_by_slug(self, session: Session, slug: str, include_deleted: bool = False) -> Optional[Workspace]:
        query = select(Workspace).where(Workspace.slug == slug)
        query = self._apply_soft_delete_filter(query, include_deleted)
        return session.execute(query).scalar_one_or_none()

    @BaseRepository._handle_db_exceptions
    def _get_by_name(self, session: Session, name: str, include_deleted: bool = False) -> Optional[Workspace]:
        query = select(Workspace).where(Workspace.name == name)
        query = self._apply_soft_delete_filter(query, include_deleted)
        return session.execute(query).scalar_one_or_none()
    
    @BaseRepository._handle_db_exceptions
    def _get_by_owner_id(self, session: Session, owner_id: str, include_deleted: bool = False) -> List[Workspace]:
        """Kullanıcının sahip olduğu workspace'leri getirir."""
        query = select(Workspace).where(Workspace.owner_id == owner_id)
        query = self._apply_soft_delete_filter(query, include_deleted)
        return list(session.execute(query).scalars().all())
    
    @BaseRepository._handle_db_exceptions
    def _count_by_plan_id(self, session: Session, plan_id: str, include_deleted: bool = False) -> int:
        """Count workspaces using this plan"""
        query = select(func.count(Workspace.id)).where(Workspace.plan_id == plan_id)
        query = self._apply_soft_delete_filter(query, include_deleted)
        result = session.execute(query).scalar()
        return result or 0

    @BaseRepository._handle_db_exceptions
    def _increment_member_count(self, session: Session, workspace_id: str) -> None:
        """Üye sayısını 1 artırır."""
        workspace = self._get_by_id(session, record_id=workspace_id)
        if workspace:
            workspace.current_member_count += 1

    @BaseRepository._handle_db_exceptions
    def _decrement_member_count(self, session: Session, workspace_id: str) -> None:
        """Üye sayısını 1 azaltır."""
        workspace = self._get_by_id(session, record_id=workspace_id)
        if workspace and workspace.current_member_count > 0:
            workspace.current_member_count -= 1

    @BaseRepository._handle_db_exceptions
    def _increment_workflow_count(self, session: Session, workspace_id: str) -> None:
        """Workflow sayısını 1 artırır."""
        workspace = self._get_by_id(session, record_id=workspace_id)
        if workspace:
            workspace.current_workflow_count += 1

    @BaseRepository._handle_db_exceptions
    def _decrement_workflow_count(self, session: Session, workspace_id: str) -> None:
        """Workflow sayısını 1 azaltır."""
        workspace = self._get_by_id(session, record_id=workspace_id)
        if workspace and workspace.current_workflow_count > 0:
            workspace.current_workflow_count -= 1

    @BaseRepository._handle_db_exceptions
    def _increment_execution_count(self, session: Session, workspace_id: str) -> None:
        """Aylık execution sayısını 1 artırır."""
        workspace = self._get_by_id(session, record_id=workspace_id)
        if workspace:
            workspace.current_month_executions += 1

    @BaseRepository._handle_db_exceptions
    def _increment_storage(self, session: Session, workspace_id: str, size_mb: float) -> None:
        """Depolama kullanımını artırır."""
        workspace = self._get_by_id(session, record_id=workspace_id)
        if workspace:
            workspace.current_storage_mb += size_mb

    @BaseRepository._handle_db_exceptions
    def _decrement_storage(self, session: Session, workspace_id: str, size_mb: float) -> None:
        """Depolama kullanımını azaltır."""
        workspace = self._get_by_id(session, record_id=workspace_id)
        if workspace and workspace.current_storage_mb >= size_mb:
            workspace.current_storage_mb -= size_mb

    @BaseRepository._handle_db_exceptions
    def _suspend_workspace(self, session: Session, workspace_id: str, reason: str) -> None:
        """Workspace'i askıya alır."""
        workspace = self._get_by_id(session, record_id=workspace_id)
        if workspace:
            workspace.is_suspended = True
            workspace.suspension_reason = reason
            workspace.suspended_at = datetime.now(timezone.utc)

    @BaseRepository._handle_db_exceptions
    def _unsuspend_workspace(self, session: Session, workspace_id: str) -> None:
        """Workspace askıya almayı kaldırır."""
        workspace = self._get_by_id(session, record_id=workspace_id)
        if workspace:
            workspace.is_suspended = False
            workspace.suspension_reason = None
            workspace.suspended_at = None

    @BaseRepository._handle_db_exceptions
    def _reset_monthly_counters(self, session: Session, workspace_id: str) -> None:
        """Aylık sayaçları sıfırlar (billing döngüsü yenilendiğinde)."""
        workspace = self._get_by_id(session, record_id=workspace_id)
        if workspace:
            workspace.current_month_executions = 0
            workspace.current_month_concurrent_executions = 0