from typing import Optional, List
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from qbitra.database.repos.base import BaseRepository, handle_exceptions
from qbitra.models.user_models.auth_session import AuthSession


class AuthSessionRepository(BaseRepository[AuthSession]):
    
    def __init__(self):
        super().__init__(AuthSession)

    @handle_exceptions
    def get_by_access_token_jti(self, session: Session, access_token_jti: str, include_deleted: bool = False) -> Optional[AuthSession]:
        query = select(AuthSession).where(AuthSession.access_token_jti == access_token_jti)
        query = self._soft_delete_filter(query, include_deleted)
        return session.execute(query).scalar_one_or_none()

    @handle_exceptions
    def get_by_refresh_token_jti(self, session: Session, refresh_token_jti: str, include_deleted: bool = False) -> Optional[AuthSession]:
        query = select(AuthSession).where(AuthSession.refresh_token_jti == refresh_token_jti)
        query = self._soft_delete_filter(query, include_deleted)
        return session.execute(query).scalar_one_or_none()

    @handle_exceptions
    def get_all_active_user_sessions(self, session: Session, user_id: str, include_deleted: bool = False) -> List[AuthSession]:
        query = select(AuthSession).where(AuthSession.user_id == user_id, AuthSession.is_revoked == False)
        query = self._soft_delete_filter(query, include_deleted)
        return list(session.execute(query).scalars().all())

    @handle_exceptions
    def revoke_oldest_session(self, session: Session, user_id: str) -> Optional[AuthSession]:
        query = (
            select(AuthSession)
            .where(AuthSession.user_id == user_id, AuthSession.is_revoked == False)
            .order_by(AuthSession.created_at.asc(), AuthSession.id.asc())
            .limit(1)
        )
        query = self._soft_delete_filter(query, include_deleted=False)
        oldest_session = session.execute(query).scalar_one_or_none()

        if oldest_session:
            oldest_session.is_revoked = True
            oldest_session.revoked_at = datetime.now(timezone.utc)
            oldest_session.revoked_by = user_id
            session.flush()

        return oldest_session

    @handle_exceptions
    def revoke_specific_session(self, session: Session, session_id: str, user_id: str) -> Optional[AuthSession]:
        query = (
            select(AuthSession)
            .where(AuthSession.id == session_id)
            .where(AuthSession.user_id == user_id)
            .where(AuthSession.is_revoked == False)
        )
        query = self._soft_delete_filter(query, include_deleted=False)
        auth_session = session.execute(query).scalar_one_or_none()

        if auth_session:
            auth_session.is_revoked = True
            auth_session.revoked_at = datetime.now(timezone.utc)
            auth_session.revoked_by = user_id
            session.flush()

        return auth_session

    @handle_exceptions
    def revoke_sessions(self, session: Session, user_id: str) -> int:
        query = (select(AuthSession).where(AuthSession.user_id == user_id, AuthSession.is_revoked == False))
        query = self._soft_delete_filter(query, include_deleted=False)
        sessions = session.execute(query).scalars().all()

        for auth_session in sessions:
            auth_session.is_revoked = True
            auth_session.revoked_at = datetime.now(timezone.utc)
            auth_session.revoked_by = user_id

        session.flush()
        return len(sessions)