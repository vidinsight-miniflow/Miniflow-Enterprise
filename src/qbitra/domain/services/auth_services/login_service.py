import secrets
from typing import Dict, Any
from datetime import datetime, timezone

from qbitra.domain.repositories import RepositoryRegistry
from qbitra.infrastructure.database import with_transaction, with_readonly_session
from qbitra.domain.models.enums import LoginStatus, LoginMethod
from qbitra.core.qbitra_logger import get_logger
from qbitra.utils.helpers.crypto_helper import verify_password
from qbitra.utils.helpers.jwt_helper import (
    create_access_token,
    create_refresh_token,
    validate_access_token,
    validate_refresh_token,
)
from qbitra.utils.handlers.configuration_handler import ConfigurationHandler
from qbitra.core.exceptions.services import (
    InvalidCredentialsError,
    EmailNotVerifiedError,
    InvalidTokenError,
    SessionNotFoundError,
)

# Domain servis logger'ı (logs/services/Auth Service/service.log)
logger = get_logger("Auth Service", parent_folder="services")


class LoginService:
    _user_repo = RepositoryRegistry().user_repository
    _auth_session_repo = RepositoryRegistry().auth_session_repository
    _login_history_repo = RepositoryRegistry().login_history_repository

    @classmethod
    def _get_max_active_sessions(cls):
        """Lazy initialization of max_active_sessions from config."""
        try:
            return ConfigurationHandler.get_value_as_int("AUTH", "max_active_sessions", fallback=5)
        except Exception:
            return 5  # Fallback if config not initialized

    @classmethod
    @with_transaction(manager=None)
    def login(cls, session, *, email_or_username: str, password: str) -> Dict[str, Any]:
        logger.info("Login attempt", extra={"email_or_username": email_or_username})

        user = cls._user_repo.get_by_email_or_username(session, email_or_username=email_or_username, include_deleted=False)
        if not user:
            logger.warning("Login failed: User not found", extra={"email_or_username": email_or_username})
            raise InvalidCredentialsError()

        if not user.email_verified:
            logger.warning("Login failed: Email not verified", extra={"user_id": user.id, "email": user.email})
            cls._login_history_repo.create(
                session,
                user_id=user.id,
                status=LoginStatus.FAILED_EMAIL_NOT_VERIFIED,
                login_method=LoginMethod.PASSWORD,
            )
            raise EmailNotVerifiedError(email=user.email)

        if not verify_password(password, user.password):
            logger.warning("Login failed: Invalid password", extra={"user_id": user.id, "email": user.email})
            cls._login_history_repo.create(
                session,
                user_id=user.id,
                status=LoginStatus.FAILED_INVALID_CREDENTIALS,
                login_method=LoginMethod.PASSWORD,
            )
            raise InvalidCredentialsError()

        access_token_jti = secrets.token_urlsafe(32)
        refresh_token_jti = secrets.token_urlsafe(32)

        # Add is_admin to JWT token for authorization checks without database query
        access_token, access_token_expires_at = create_access_token(
            user_id=user.id, 
            access_token_jti=access_token_jti,
            additional_claims={"is_admin": user.is_admin}
        )
        refresh_token, refresh_token_expires_at = create_refresh_token(user_id=user.id, refresh_token_jti=refresh_token_jti)

        active_sessions = cls._auth_session_repo.get_all_active_user_sessions(session, user_id=user.id)
        if len(active_sessions) >= cls._get_max_active_sessions():
            cls._auth_session_repo.revoke_oldest_session(session, user_id=user.id)

        auth_session = cls._auth_session_repo.create(
            session,
            user_id=user.id,
            access_token_jti=access_token_jti,
            access_token_expires_at=access_token_expires_at,
            refresh_token_jti=refresh_token_jti,
            refresh_token_expires_at=refresh_token_expires_at,
        )

        cls._login_history_repo.create(
            session,
            user_id=user.id,
            session_id=auth_session.id,
            status=LoginStatus.SUCCESS,
            login_method=LoginMethod.PASSWORD,
        )

        logger.info("Login successful", extra={"user_id": user.id, "username": user.username, "email": user.email})

        return {
            "message": "Login successful",
            "data": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "access_token": access_token,
                "refresh_token": refresh_token,
            }
        }

    @classmethod
    @with_transaction(manager=None)
    def logout(cls, session, *, access_token: str) -> Dict[str, Any]:
        is_valid, payload = validate_access_token(access_token)
        if not is_valid:
            raise InvalidTokenError()

        access_token_jti = payload['jti']
        auth_session = cls._auth_session_repo.get_by_access_token_jti(session, access_token_jti=access_token_jti)

        if not auth_session or auth_session.is_revoked:
            raise SessionNotFoundError()

        cls._auth_session_repo.revoke_specific_session(session, session_id=auth_session.id, user_id=payload['user_id'])

        return {
            "message": "Logged out successfully",
            "data": {"success": True}
        }

    @classmethod
    @with_transaction(manager=None)
    def logout_all(cls, session, *, user_id: str) -> Dict[str, Any]:
        num_revoked = cls._auth_session_repo.revoke_sessions(session, user_id=user_id)

        return {
            "message": "All sessions revoked successfully",
            "data": {
                "success": True,
                "sessions_revoked": num_revoked
            }
        }

    @classmethod
    @with_readonly_session(manager=None)
    def validate_access_token(cls, session, *, access_token: str) -> Dict[str, Any]:
        is_valid, payload = validate_access_token(access_token)
        if not is_valid:
            return {
                "message": "Token validation failed",
                "data": {"valid": False, "error": str(payload)}
            }

        auth_session = cls._auth_session_repo.get_by_access_token_jti(
            session, 
            access_token_jti=payload['jti'], 
            include_deleted=False
        )

        if not auth_session or auth_session.is_revoked:
            return {
                "message": "Token validation failed",
                "data": {"valid": False, "error": "Session not found or revoked"}
            }

        # Extract is_admin from JWT payload (added during token creation)
        is_admin = payload.get("is_admin", False)

        return {
            "message": "Token validation successful",
            "data": {
                "valid": True, 
                "user_id": auth_session.user_id, 
                "is_admin": is_admin,
                "session_id": auth_session.id  # Session ID'yi ekle
            }
        }

    @classmethod
    @with_transaction(manager=None)
    def refresh_tokens(cls, session, *, refresh_token: str) -> Dict[str, Any]:
        is_valid, payload = validate_refresh_token(refresh_token)
        if not is_valid:
            raise InvalidTokenError()

        auth_session = cls._auth_session_repo.get_by_refresh_token_jti(
            session, 
            refresh_token_jti=payload['jti'], 
            include_deleted=False
        )

        if not auth_session or auth_session.is_revoked:
            raise SessionNotFoundError()

        user = cls._user_repo.get(session, record_id=payload['user_id'], include_deleted=False)
        if not user or not user.email_verified or user.is_locked:
            raise InvalidCredentialsError()

        new_access_token_jti = secrets.token_urlsafe(32)
        new_refresh_token_jti = secrets.token_urlsafe(32)

        # Add is_admin to new access token (user info is already loaded from database)
        new_access_token, new_access_token_expires_at = create_access_token(
            user_id=user.id, 
            access_token_jti=new_access_token_jti,
            additional_claims={"is_admin": user.is_admin}
        )
        new_refresh_token, new_refresh_token_expires_at = create_refresh_token(user_id=user.id, refresh_token_jti=new_refresh_token_jti)

        auth_session.access_token_jti = new_access_token_jti
        auth_session.access_token_expires_at = new_access_token_expires_at
        auth_session.refresh_token_jti = new_refresh_token_jti
        auth_session.refresh_token_expires_at = new_refresh_token_expires_at
        auth_session.refresh_token_last_used_at = datetime.now(timezone.utc)
        session.flush()

        return {
            "message": "Tokens refreshed successfully",
            "data": {
                "id": user.id,
                "access_token": new_access_token,
                "refresh_token": new_refresh_token
            }
        }
