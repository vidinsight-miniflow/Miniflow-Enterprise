from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy import select, func, delete
from sqlalchemy.orm import Session

from ..base_repository import BaseRepository
from miniflow.models import AuthSession


class AuthSessionRepository(BaseRepository[AuthSession]):
    def __init__(self):
        super().__init__(AuthSession)

    @BaseRepository._handle_db_exceptions
    def _get_by_access_token_jti(self, session: Session, access_token_jti: str, include_deleted: bool = False) -> Optional[AuthSession]:
        query = select(AuthSession).where(AuthSession.access_token_jti == access_token_jti)
        query = self._apply_soft_delete_filter(query, include_deleted)
        return session.execute(query).scalar_one_or_none()
    
    @BaseRepository._handle_db_exceptions
    def _get_by_refresh_token_jti(self, session: Session, refresh_token_jti: str, include_deleted: bool = False) -> Optional[AuthSession]:
        query = select(AuthSession).where(AuthSession.refresh_token_jti == refresh_token_jti)
        query = self._apply_soft_delete_filter(query, include_deleted)
        return session.execute(query).scalar_one_or_none()

    @BaseRepository._handle_db_exceptions
    def _get_all_active_user_sessions(self, session: Session, user_id: str, include_deleted: bool = False) -> List[AuthSession]:
        query = select(AuthSession).where(AuthSession.user_id == user_id, AuthSession.is_revoked == False)
        query = self._apply_soft_delete_filter(query, include_deleted)
        return session.execute(query).scalars().all()

    @BaseRepository._handle_db_exceptions
    def _revoke_oldest_session(self, session: Session, user_id: str) -> Optional[AuthSession]:
        query = (
            select(AuthSession)
            .where(AuthSession.user_id == user_id, AuthSession.is_revoked == False)
            .order_by(AuthSession.created_at.asc(), AuthSession.id.asc())
            .limit(1)
        )
        query = self._apply_soft_delete_filter(query, include_deleted=False)
        oldest_session = session.execute(query).scalar_one_or_none()
        
        if oldest_session:
            oldest_session.is_revoked = True
            oldest_session.revoked_at = datetime.now(timezone.utc)
            oldest_session.revoked_by = user_id
        
        return oldest_session

    @BaseRepository._handle_db_exceptions
    def _revoke_specific_session(self, session: Session, session_id: str, user_id: str) -> Optional[AuthSession]:
        query = (
            select(AuthSession)
            .where(AuthSession.id == session_id)
            .where(AuthSession.user_id == user_id)
            .where(AuthSession.is_revoked == False)
        )
        query = self._apply_soft_delete_filter(query, include_deleted=False)
        auth_session = session.execute(query).scalar_one_or_none()
        
        if auth_session:
            auth_session.is_revoked = True
            auth_session.revoked_at = datetime.now(timezone.utc)
            auth_session.revoked_by = user_id
        
        return auth_session

    @BaseRepository._handle_db_exceptions
    def _revoke_sessions(self, session: Session, user_id: str) -> int:
        query = (
            select(AuthSession)
            .where(AuthSession.user_id == user_id, AuthSession.is_revoked == False)
        )
        query = self._apply_soft_delete_filter(query, include_deleted=False)
        sessions = session.execute(query).scalars().all()
        
        for auth_session in sessions:
            auth_session.is_revoked = True
            auth_session.revoked_at = datetime.now(timezone.utc)
            auth_session.revoked_by = user_id
        
        return len(sessions)