from typing import Optional, List
from sqlalchemy import select, and_, func
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from ..base_repository import BaseRepository
from miniflow.models import WorkspaceInvitation
from miniflow.models.enums import InvitationStatus


class WorkspaceInvitationRepository(BaseRepository[WorkspaceInvitation]):
    def __init__(self):
        super().__init__(WorkspaceInvitation)

    @BaseRepository._handle_db_exceptions
    def _get_pending_by_user_id(self, session: Session, user_id: str, include_deleted: bool = False) -> List[WorkspaceInvitation]:
        """Kullanıcının bekleyen davetlerini getirir."""
        query = select(WorkspaceInvitation).where(
            and_(
                WorkspaceInvitation.invitee_id == user_id,
                WorkspaceInvitation.status == InvitationStatus.PENDING
            )
        )
        query = self._apply_soft_delete_filter(query, include_deleted)
        return list(session.execute(query).scalars().all())

    @BaseRepository._handle_db_exceptions
    def _get_by_workspace_id_and_user_id(
        self,
        session: Session,
        *,
        workspace_id: str,
        user_id: str,
        include_deleted: bool = False
    ) -> Optional[WorkspaceInvitation]:
        """Workspace ve kullanıcı ID'sine göre davet getirir."""
        query = select(WorkspaceInvitation).where(
            and_(
                WorkspaceInvitation.workspace_id == workspace_id,
                WorkspaceInvitation.invitee_id == user_id
            )
        )
        query = self._apply_soft_delete_filter(query, include_deleted)
        return session.execute(query).scalar_one_or_none()

    @BaseRepository._handle_db_exceptions
    def _get_all_by_workspace_id(self, session: Session, workspace_id: str, include_deleted: bool = False) -> List[WorkspaceInvitation]:
        """Workspace'in tüm davetlerini getirir."""
        query = select(WorkspaceInvitation).where(WorkspaceInvitation.workspace_id == workspace_id)
        query = self._apply_soft_delete_filter(query, include_deleted)
        return list(session.execute(query).scalars().all())

    @BaseRepository._handle_db_exceptions
    def _get_pending_by_workspace_id(self, session: Session, workspace_id: str, include_deleted: bool = False) -> List[WorkspaceInvitation]:
        """Workspace'in bekleyen davetlerini getirir."""
        query = select(WorkspaceInvitation).where(
            and_(
                WorkspaceInvitation.workspace_id == workspace_id,
                WorkspaceInvitation.status == InvitationStatus.PENDING
            )
        )
        query = self._apply_soft_delete_filter(query, include_deleted)
        return list(session.execute(query).scalars().all())

    @BaseRepository._handle_db_exceptions
    def _count_pending_by_workspace_id(self, session: Session, workspace_id: str, include_deleted: bool = False) -> int:
        """Workspace'in bekleyen davet sayısını döndürür."""
        query = select(func.count(WorkspaceInvitation.id)).where(
            and_(
                WorkspaceInvitation.workspace_id == workspace_id,
                WorkspaceInvitation.status == InvitationStatus.PENDING
            )
        )
        query = self._apply_soft_delete_filter(query, include_deleted)
        result = session.execute(query).scalar()
        return result or 0

    @BaseRepository._handle_db_exceptions
    def _delete_all_by_workspace_id(self, session: Session, workspace_id: str) -> int:
        """Workspace'in tüm davetlerini siler."""
        invitations = self._get_all_by_workspace_id(session, workspace_id=workspace_id)
        count = 0
        for invitation in invitations:
            self._delete(session, record_id=invitation.id)
            count += 1
        return count