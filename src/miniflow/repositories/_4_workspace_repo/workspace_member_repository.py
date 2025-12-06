from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy import select, and_, func
from sqlalchemy.orm import Session

from ..base_repository import BaseRepository
from miniflow.models import WorkspaceMember


class WorkspaceMemberRepository(BaseRepository[WorkspaceMember]):
    def __init__(self):
        super().__init__(WorkspaceMember)

    @BaseRepository._handle_db_exceptions
    def _get_by_workspace_id_and_user_id(self, session: Session, *, workspace_id: str, user_id: str, include_deleted: bool = False) -> Optional[WorkspaceMember]:
        query = select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id, 
            WorkspaceMember.user_id == user_id
        )
        query = self._apply_soft_delete_filter(query, include_deleted)
        return session.execute(query).scalar_one_or_none()

    @BaseRepository._handle_db_exceptions
    def _get_all_by_workspace_id(self, session: Session, workspace_id: str, include_deleted: bool = False) -> List[WorkspaceMember]:
        """Workspace'in tüm üyelerini getirir."""
        query = select(WorkspaceMember).where(WorkspaceMember.workspace_id == workspace_id)
        query = self._apply_soft_delete_filter(query, include_deleted)
        return list(session.execute(query).scalars().all())

    @BaseRepository._handle_db_exceptions
    def _get_owned_workspaces_by_user_id(self, session: Session, user_id: str, include_deleted: bool = False) -> List[WorkspaceMember]:
        query = select(WorkspaceMember).where(
            WorkspaceMember.user_id == user_id, 
            func.lower(WorkspaceMember.role_name) == "owner"
        )
        query = self._apply_soft_delete_filter(query, include_deleted)
        return list(session.execute(query).scalars().all()) 

    @BaseRepository._handle_db_exceptions
    def _get_memberships_by_user_id(self, session: Session, user_id: str, include_deleted: bool = False) -> List[WorkspaceMember]:
        query = select(WorkspaceMember).where(
            WorkspaceMember.user_id == user_id, 
            func.lower(WorkspaceMember.role_name) != "owner"
        )
        query = self._apply_soft_delete_filter(query, include_deleted)
        return list(session.execute(query).scalars().all())

    @BaseRepository._handle_db_exceptions
    def _get_all_by_user_id(self, session: Session, user_id: str, include_deleted: bool = False) -> List[WorkspaceMember]:
        """Kullanıcının tüm workspace üyeliklerini getirir (owner dahil)."""
        query = select(WorkspaceMember).where(WorkspaceMember.user_id == user_id)
        query = self._apply_soft_delete_filter(query, include_deleted)
        return list(session.execute(query).scalars().all())
    
    @BaseRepository._handle_db_exceptions
    def _count_by_role_id(self, session: Session, role_id: str, include_deleted: bool = False) -> int:
        """Count workspace members using this role"""
        query = select(func.count(WorkspaceMember.id)).where(WorkspaceMember.role_id == role_id)
        query = self._apply_soft_delete_filter(query, include_deleted)
        result = session.execute(query).scalar()
        return result or 0

    @BaseRepository._handle_db_exceptions
    def _count_by_workspace_id(self, session: Session, workspace_id: str, include_deleted: bool = False) -> int:
        """Workspace'deki üye sayısını döndürür."""
        query = select(func.count(WorkspaceMember.id)).where(WorkspaceMember.workspace_id == workspace_id)
        query = self._apply_soft_delete_filter(query, include_deleted)
        result = session.execute(query).scalar()
        return result or 0

    @BaseRepository._handle_db_exceptions
    def _update_last_accessed(self, session: Session, member_id: str) -> None:
        """Üyenin son erişim zamanını günceller."""
        member = self._get_by_id(session, record_id=member_id)
        if member:
            member.last_accessed_at = datetime.now(timezone.utc)

    @BaseRepository._handle_db_exceptions
    def _update_role(self, session: Session, *, member_id: str, role_id: str, role_name: str) -> Optional[WorkspaceMember]:
        """Üyenin rolünü günceller."""
        member = self._get_by_id(session, record_id=member_id)
        if member:
            member.role_id = role_id
            member.role_name = role_name
            return member
        return None

    @BaseRepository._handle_db_exceptions
    def _delete_all_by_workspace_id(self, session: Session, workspace_id: str) -> int:
        """Workspace'in tüm üyelerini siler."""
        members = self._get_all_by_workspace_id(session, workspace_id=workspace_id)
        count = 0
        for member in members:
            self._delete(session, record_id=member.id)
            count += 1
        return count