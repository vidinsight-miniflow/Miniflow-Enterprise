from typing import Optional, List

from sqlalchemy import select, or_, func, and_
from sqlalchemy.orm import Session

from qbitra.database.repos.extra import ExtraRepository
from qbitra.database.repos.base import handle_exceptions
from qbitra.models.user_models.user import User


class UserRepository(ExtraRepository[User]):
    
    def __init__(self):
        super().__init__(User)

    @handle_exceptions
    def get_by_email(self, session: Session, email: str, include_deleted: bool = False) -> Optional[User]:
        query = select(User).where(User.email == email)
        query = self._soft_delete_filter(query, include_deleted)
        return session.execute(query).scalar_one_or_none()

    @handle_exceptions
    def get_by_username(self, session: Session, username: str, include_deleted: bool = False) -> Optional[User]:
        query = select(User).where(User.username == username)
        query = self._soft_delete_filter(query, include_deleted)
        return session.execute(query).scalar_one_or_none()

    @handle_exceptions
    def get_by_email_verification_token(self, session: Session, token: str, include_deleted: bool = False) -> Optional[User]:
        query = select(User).where(User.email_verification_token == token)
        query = self._soft_delete_filter(query, include_deleted)
        return session.execute(query).scalar_one_or_none()
    
    @handle_exceptions
    def get_by_password_reset_token(self, session: Session, token: str, include_deleted: bool = False) -> Optional[User]:
        query = select(User).where(User.password_reset_token == token)
        query = self._soft_delete_filter(query, include_deleted)
        return session.execute(query).scalar_one_or_none()

    @handle_exceptions
    def get_by_email_or_username(self, session: Session, email_or_username: str, include_deleted: bool = False) -> Optional[User]:
        query = select(User).where(or_(User.email == email_or_username, User.username == email_or_username))
        query = self._soft_delete_filter(query, include_deleted)
        return session.execute(query).scalar_one_or_none()