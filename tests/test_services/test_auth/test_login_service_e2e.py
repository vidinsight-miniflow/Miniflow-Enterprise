import pytest
from datetime import datetime, timezone

from qbitra.services.auth_services import LoginService, RegistrationService
from qbitra.repositories import RepositoryRegistry
from qbitra.core.exceptions.services import (
    InvalidCredentialsError,
    EmailNotVerifiedError,
    InvalidTokenError,
    SessionNotFoundError,
)


class TestLoginServiceE2E:
    """End-to-end tests for LoginService with real-world scenarios."""

    def test_login_success(self, manager):
        """Scenario: User successfully logs in with valid credentials."""
        with manager.engine.session_context(auto_commit=True) as session:
            registration_result = RegistrationService.register_user(
                session,
                username="johndoe",
                email="john.doe@example.com",
                password="SecurePass123!",
                name="John",
                surname="Doe"
            )
            user_id = registration_result["data"]["id"]
            verification_token = registration_result["data"]["email_verification_token"]
            RegistrationService.verify_email(session, verification_token=verification_token)

        with manager.engine.session_context(auto_commit=True) as session:
            result = LoginService.login(
                session,
                email_or_username="john.doe@example.com",
                password="SecurePass123!"
            )

            assert result["message"] == "Login successful"
            assert result["data"]["id"] == user_id
            assert result["data"]["username"] == "johndoe"
            assert result["data"]["email"] == "john.doe@example.com"
            assert "access_token" in result["data"]
            assert "refresh_token" in result["data"]

            auth_session_repo = RepositoryRegistry().auth_session_repository
            login_history_repo = RepositoryRegistry().login_history_repository
            
            sessions = auth_session_repo.get_all_active_user_sessions(session, user_id=user_id, include_deleted=False)
            assert len(sessions) == 1
            assert sessions[0].user_id == user_id

    def test_login_with_username(self, manager):
        """Scenario: User successfully logs in using username instead of email."""
        with manager.engine.session_context(auto_commit=True) as session:
            registration_result = RegistrationService.register_user(
                session,
                username="johndoe",
                email="john.doe@example.com",
                password="SecurePass123!",
                name="John",
                surname="Doe"
            )
            verification_token = registration_result["data"]["email_verification_token"]
            RegistrationService.verify_email(session, verification_token=verification_token)

        with manager.engine.session_context(auto_commit=True) as session:
            result = LoginService.login(
                session,
                email_or_username="johndoe",
                password="SecurePass123!"
            )

            assert result["message"] == "Login successful"
            assert result["data"]["username"] == "johndoe"

    def test_login_invalid_credentials_user_not_found(self, manager):
        """Scenario: User tries to login with non-existent email/username."""
        with manager.engine.session_context(auto_commit=True) as session:
            with pytest.raises(InvalidCredentialsError):
                LoginService.login(
                    session,
                    email_or_username="nonexistent@example.com",
                    password="SecurePass123!"
                )

    def test_login_invalid_password(self, manager):
        """Scenario: User tries to login with wrong password."""
        with manager.engine.session_context(auto_commit=True) as session:
            registration_result = RegistrationService.register_user(
                session,
                username="johndoe",
                email="john.doe@example.com",
                password="SecurePass123!",
                name="John",
                surname="Doe"
            )
            verification_token = registration_result["data"]["email_verification_token"]
            RegistrationService.verify_email(session, verification_token=verification_token)

        with manager.engine.session_context(auto_commit=True) as session:
            with pytest.raises(InvalidCredentialsError):
                LoginService.login(
                    session,
                    email_or_username="john.doe@example.com",
                    password="WrongPassword123!"
                )

    def test_login_email_not_verified(self, manager):
        """Scenario: User tries to login before verifying email."""
        with manager.engine.session_context(auto_commit=True) as session:
            RegistrationService.register_user(
                session,
                username="johndoe",
                email="john.doe@example.com",
                password="SecurePass123!",
                name="John",
                surname="Doe"
            )

        with manager.engine.session_context(auto_commit=True) as session:
            with pytest.raises(EmailNotVerifiedError) as exc_info:
                LoginService.login(
                    session,
                    email_or_username="john.doe@example.com",
                    password="SecurePass123!"
                )
            assert exc_info.value.error_details["email"] == "john.doe@example.com"

    def test_logout_success(self, manager):
        """Scenario: User successfully logs out."""
        with manager.engine.session_context(auto_commit=True) as session:
            registration_result = RegistrationService.register_user(
                session,
                username="johndoe",
                email="john.doe@example.com",
                password="SecurePass123!",
                name="John",
                surname="Doe"
            )
            verification_token = registration_result["data"]["email_verification_token"]
            RegistrationService.verify_email(session, verification_token=verification_token)

            login_result = LoginService.login(
                session,
                email_or_username="john.doe@example.com",
                password="SecurePass123!"
            )
            access_token = login_result["data"]["access_token"]

        with manager.engine.session_context(auto_commit=True) as session:
            result = LoginService.logout(session, access_token=access_token)

            assert result["message"] == "Logged out successfully"
            assert result["data"]["success"] is True

    def test_logout_invalid_token(self, manager):
        """Scenario: User tries to logout with invalid token."""
        with manager.engine.session_context(auto_commit=True) as session:
            with pytest.raises(InvalidTokenError):
                LoginService.logout(session, access_token="invalid_token_12345")

    def test_logout_all_sessions(self, manager):
        """Scenario: User logs out from all active sessions."""
        with manager.engine.session_context(auto_commit=True) as session:
            registration_result = RegistrationService.register_user(
                session,
                username="johndoe",
                email="john.doe@example.com",
                password="SecurePass123!",
                name="John",
                surname="Doe"
            )
            user_id = registration_result["data"]["id"]
            verification_token = registration_result["data"]["email_verification_token"]
            RegistrationService.verify_email(session, verification_token=verification_token)

            LoginService.login(
                session,
                email_or_username="john.doe@example.com",
                password="SecurePass123!"
            )
            LoginService.login(
                session,
                email_or_username="john.doe@example.com",
                password="SecurePass123!"
            )

        with manager.engine.session_context(auto_commit=True) as session:
            auth_session_repo = RepositoryRegistry().auth_session_repository
            sessions_before = auth_session_repo.get_all_active_user_sessions(session, user_id=user_id, include_deleted=False)
            assert len(sessions_before) == 2

            result = LoginService.logout_all(session, user_id=user_id)

            assert result["message"] == "All sessions revoked successfully"
            assert result["data"]["success"] is True
            assert result["data"]["sessions_revoked"] == 2

            sessions_after = auth_session_repo.get_all_active_user_sessions(session, user_id=user_id, include_deleted=False)
            assert len(sessions_after) == 0

    def test_validate_access_token_success(self, manager):
        """Scenario: Access token validation succeeds."""
        with manager.engine.session_context(auto_commit=True) as session:
            registration_result = RegistrationService.register_user(
                session,
                username="johndoe",
                email="john.doe@example.com",
                password="SecurePass123!",
                name="John",
                surname="Doe"
            )
            verification_token = registration_result["data"]["email_verification_token"]
            RegistrationService.verify_email(session, verification_token=verification_token)

            login_result = LoginService.login(
                session,
                email_or_username="john.doe@example.com",
                password="SecurePass123!"
            )
            access_token = login_result["data"]["access_token"]

        with manager.engine.session_context(auto_commit=True) as session:
            result = LoginService.validate_access_token(session, access_token=access_token)

            assert result["message"] == "Token validation successful"
            assert result["data"]["valid"] is True
            assert result["data"]["user_id"] is not None

    def test_validate_access_token_invalid(self, manager):
        """Scenario: Access token validation fails with invalid token."""
        with manager.engine.session_context(auto_commit=True) as session:
            result = LoginService.validate_access_token(session, access_token="invalid_token_12345")

            assert result["message"] == "Token validation failed"
            assert result["data"]["valid"] is False
            assert "error" in result["data"]

    def test_validate_access_token_revoked_session(self, manager):
        """Scenario: Access token validation fails because session is revoked."""
        with manager.engine.session_context(auto_commit=True) as session:
            registration_result = RegistrationService.register_user(
                session,
                username="johndoe",
                email="john.doe@example.com",
                password="SecurePass123!",
                name="John",
                surname="Doe"
            )
            verification_token = registration_result["data"]["email_verification_token"]
            RegistrationService.verify_email(session, verification_token=verification_token)

            login_result = LoginService.login(
                session,
                email_or_username="john.doe@example.com",
                password="SecurePass123!"
            )
            access_token = login_result["data"]["access_token"]
            LoginService.logout(session, access_token=access_token)

        with manager.engine.session_context(auto_commit=True) as session:
            result = LoginService.validate_access_token(session, access_token=access_token)

            assert result["message"] == "Token validation failed"
            assert result["data"]["valid"] is False
            assert "revoked" in result["data"]["error"].lower() or "not found" in result["data"]["error"].lower()

    def test_refresh_tokens_success(self, manager):
        """Scenario: User successfully refreshes tokens."""
        with manager.engine.session_context(auto_commit=True) as session:
            registration_result = RegistrationService.register_user(
                session,
                username="johndoe",
                email="john.doe@example.com",
                password="SecurePass123!",
                name="John",
                surname="Doe"
            )
            verification_token = registration_result["data"]["email_verification_token"]
            RegistrationService.verify_email(session, verification_token=verification_token)

            login_result = LoginService.login(
                session,
                email_or_username="john.doe@example.com",
                password="SecurePass123!"
            )
            refresh_token = login_result["data"]["refresh_token"]

        with manager.engine.session_context(auto_commit=True) as session:
            result = LoginService.refresh_tokens(session, refresh_token=refresh_token)

            assert result["message"] == "Tokens refreshed successfully"
            assert result["data"]["id"] is not None
            assert "access_token" in result["data"]
            assert "refresh_token" in result["data"]
            assert result["data"]["access_token"] != login_result["data"]["access_token"]
            assert result["data"]["refresh_token"] != refresh_token

    def test_refresh_tokens_invalid_token(self, manager):
        """Scenario: User tries to refresh tokens with invalid refresh token."""
        with manager.engine.session_context(auto_commit=True) as session:
            with pytest.raises(InvalidTokenError):
                LoginService.refresh_tokens(session, refresh_token="invalid_token_12345")

    def test_refresh_tokens_revoked_session(self, manager):
        """Scenario: User tries to refresh tokens but session is revoked."""
        with manager.engine.session_context(auto_commit=True) as session:
            registration_result = RegistrationService.register_user(
                session,
                username="johndoe",
                email="john.doe@example.com",
                password="SecurePass123!",
                name="John",
                surname="Doe"
            )
            verification_token = registration_result["data"]["email_verification_token"]
            RegistrationService.verify_email(session, verification_token=verification_token)

            login_result = LoginService.login(
                session,
                email_or_username="john.doe@example.com",
                password="SecurePass123!"
            )
            access_token = login_result["data"]["access_token"]
            refresh_token = login_result["data"]["refresh_token"]
            LoginService.logout(session, access_token=access_token)

        with manager.engine.session_context(auto_commit=True) as session:
            with pytest.raises(SessionNotFoundError):
                LoginService.refresh_tokens(session, refresh_token=refresh_token)

    def test_max_active_sessions_limit(self, manager):
        """Scenario: When max active sessions limit is reached, oldest session is revoked."""
        with manager.engine.session_context(auto_commit=True) as session:
            registration_result = RegistrationService.register_user(
                session,
                username="johndoe",
                email="john.doe@example.com",
                password="SecurePass123!",
                name="John",
                surname="Doe"
            )
            user_id = registration_result["data"]["id"]
            verification_token = registration_result["data"]["email_verification_token"]
            RegistrationService.verify_email(session, verification_token=verification_token)

            auth_session_repo = RepositoryRegistry().auth_session_repository

            for i in range(6):
                LoginService.login(
                    session,
                    email_or_username="john.doe@example.com",
                    password="SecurePass123!"
                )

        with manager.engine.session_context(auto_commit=True) as session:
            sessions = auth_session_repo.get_all_active_user_sessions(session, user_id=user_id, include_deleted=False)
            assert len(sessions) == 5

    def test_complete_login_flow(self, manager):
        """Scenario: Complete login flow from registration to logout."""
        with manager.engine.session_context(auto_commit=True) as session:
            registration_result = RegistrationService.register_user(
                session,
                username="johndoe",
                email="john.doe@example.com",
                password="SecurePass123!",
                name="John",
                surname="Doe"
            )
            verification_token = registration_result["data"]["email_verification_token"]
            RegistrationService.verify_email(session, verification_token=verification_token)

            login_result = LoginService.login(
                session,
                email_or_username="john.doe@example.com",
                password="SecurePass123!"
            )
            access_token = login_result["data"]["access_token"]
            refresh_token = login_result["data"]["refresh_token"]

            validation_result = LoginService.validate_access_token(session, access_token=access_token)
            assert validation_result["data"]["valid"] is True

            refresh_result = LoginService.refresh_tokens(session, refresh_token=refresh_token)
            assert "access_token" in refresh_result["data"]

            new_access_token = refresh_result["data"]["access_token"]
            LoginService.logout(session, access_token=new_access_token)

            final_validation = LoginService.validate_access_token(session, access_token=new_access_token)
            assert final_validation["data"]["valid"] is False
