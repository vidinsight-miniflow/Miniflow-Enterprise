from typing import Optional, List
from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from ..base_repository import BaseRepository
from ...models.workspace_models.workspace_member_model import WorkspaceMember


class WorkspaceMemberRepository(BaseRepository[WorkspaceMember]):
    def __init__(self):
        super().__init__(WorkspaceMember)

    @BaseRepository._handle_db_exceptions
    def _get_by_workspace_id_and_user_id(self, session: Session, workspace_id: str, user_id: str, include_deleted: bool = False) -> Optional[WorkspaceMember]:
        query = select(WorkspaceMember).where(WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.user_id == user_id)
        query = self._apply_soft_delete_filter(query, include_deleted)
        return session.execute(query).scalar_one_or_none()

    @BaseRepository._handle_db_exceptions
    def _get_owned_workspaces_by_user_id(self, session: Session, user_id: str, include_deleted: bool = False) -> List[WorkspaceMember]:
        query = select(WorkspaceMember).where(WorkspaceMember.user_id == user_id, WorkspaceMember.role_name.lower() == "owner")
        query = self._apply_soft_delete_filter(query, include_deleted)
        return list(session.execute(query).scalars().all()) 

    @BaseRepository._handle_db_exceptions
    def _get_memberships_by_user_id(self, session: Session, user_id: str, include_deleted: bool = False) -> List[WorkspaceMember]:
        query = select(WorkspaceMember).where(WorkspaceMember.user_id == user_id, WorkspaceMember.role_name.lower() != "owner")
        query = self._apply_soft_delete_filter(query, include_deleted)
        return list(session.execute(query).scalars().all()) 