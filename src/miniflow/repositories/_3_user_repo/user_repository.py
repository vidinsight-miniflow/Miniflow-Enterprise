from typing import Optional

from sqlalchemy import select, or_
from sqlalchemy.orm import Session

from ..base_repository import BaseRepository
from miniflow.models import User


class UserRepository(BaseRepository[User]):
    def __init__(self):
        super().__init__(User)

    @BaseRepository._handle_db_exceptions
    def _get_by_email(self, session: Session, email: str, include_deleted: bool = False) -> Optional[User]:
        query = select(User).where(self.model.email == email)
        query = self._apply_soft_delete_filter(query, include_deleted)
        return session.execute(query).scalar_one_or_none()

    @BaseRepository._handle_db_exceptions
    def _get_by_username(self, session: Session, username: str, include_deleted: bool = False) -> Optional[User]:
        query = select(User).where(self.model.username == username)
        query = self._apply_soft_delete_filter(query, include_deleted)
        return session.execute(query).scalar_one_or_none()

    @BaseRepository._handle_db_exceptions
    def _get_by_email_verification_token(self, session: Session, token: str, include_deleted: bool = False) -> Optional[User]:
        query = select(User).where(self.model.email_verification_token == token)
        query = self._apply_soft_delete_filter(query, include_deleted)
        return session.execute(query).scalar_one_or_none()
    
    @BaseRepository._handle_db_exceptions
    def _get_by_password_reset_token(self, session: Session, token: str, include_deleted: bool = False) -> Optional[User]:
        query = select(User).where(self.model.password_reset_token == token)
        query = self._apply_soft_delete_filter(query, include_deleted)
        return session.execute(query).scalar_one_or_none()

    @BaseRepository._handle_db_exceptions
    def _get_by_email_or_username(self, session: Session, email_or_username: str, include_deleted: bool = False) -> Optional[User]:
        query = select(User).where(or_(self.model.email == email_or_username, self.model.username == email_or_username))
        query = self._apply_soft_delete_filter(query, include_deleted)
        return session.execute(query).scalar_one_or_none()