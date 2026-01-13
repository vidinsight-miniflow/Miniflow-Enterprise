from typing import Optional

from sqlalchemy import select, or_
from sqlalchemy.orm import Session

from qbitra.infrastructure.database.repos.extra import ExtraRepository
from qbitra.infrastructure.database.repos.base import handle_exceptions
from qbitra.domain.models.user_models.user import User
from qbitra.utils.helpers.token_helper import verify_hashed_token


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
        """
        Get user by email verification token.
        Since token is stored as hash, we need to check all users with tokens.
        """
        query = select(User).where(User.email_verification_token.isnot(None))
        query = self._soft_delete_filter(query, include_deleted)
        users = session.execute(query).scalars().all()
        
        for user in users:
            if user.email_verification_token and verify_hashed_token(token, user.email_verification_token):
                return user
        
        return None
    
    @handle_exceptions
    def get_by_password_reset_token(self, session: Session, token: str, include_deleted: bool = False) -> Optional[User]:
        """
        Get user by password reset token.
        Since token is stored as hash, we need to check all users with tokens.
        """
        query = select(User).where(User.password_reset_token.isnot(None))
        query = self._soft_delete_filter(query, include_deleted)
        users = session.execute(query).scalars().all()
        
        for user in users:
            if user.password_reset_token and verify_hashed_token(token, user.password_reset_token):
                return user
        
        return None

    @handle_exceptions
    def get_by_email_or_username(self, session: Session, email_or_username: str, include_deleted: bool = False) -> Optional[User]:
        query = select(User).where(or_(User.email == email_or_username, User.username == email_or_username))
        query = self._soft_delete_filter(query, include_deleted)
        return session.execute(query).scalar_one_or_none()