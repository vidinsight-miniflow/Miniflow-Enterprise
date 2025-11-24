from typing import Optional, List
from sqlalchemy import select, and_
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from ..base_repository import BaseRepository
from ...models.workspace_models.workspace_invitation_model import WorkspaceInvitation
from ...models.enums import InvitationStatus


class WorkspaceInvitationRepository(BaseRepository[WorkspaceInvitation]):
    def __init__(self):
        super().__init__(WorkspaceInvitation)

    @BaseRepository._handle_db_exceptions
    def _get_pending_by_user_id(self, session: Session, user_id: str, include_deleted: bool = False) -> List[WorkspaceInvitation]:
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
        workspace_id: str,
        user_id: str,
        include_deleted: bool = False
    ) -> Optional[WorkspaceInvitation]:
        query = select(WorkspaceInvitation).where(
            and_(
                WorkspaceInvitation.workspace_id == workspace_id,
                WorkspaceInvitation.invitee_id == user_id
            )
        )
        query = self._apply_soft_delete_filter(query, include_deleted)
        return session.execute(query).scalar_one_or_none()