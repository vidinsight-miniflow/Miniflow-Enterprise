import os
import sys
import pytest
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src'))

from qbitra.services.auth_services import RegistrationService
from qbitra.repositories import RepositoryRegistry
from qbitra.core.exceptions.services import (
    RegistrationEmailAlreadyExistsError,
    RegistrationUsernameAlreadyExistsError,
    RegistrationInvalidEmailFormatError,
    RegistrationWeakPasswordError,
    RegistrationInvalidUsernameError,
    EmailVerificationTokenNotFoundError,
    EmailVerificationTokenInvalidError,
    EmailAlreadyVerifiedError,
)


class TestRegistrationServiceE2E:
    """End-to-end tests for RegistrationService with real-world scenarios."""

    def test_register_user_success(self, manager):
        """Scenario: New user successfully registers with valid data."""
        with manager.engine.session_context(auto_commit=True) as session:
            result = RegistrationService.register_user(
                session,
                username="johndoe",
                email="john.doe@example.com",
                password="SecurePass123!",
                name="John",
                surname="Doe",
                country_code="US",
                phone_number="+15551234567"
            )

            assert result["message"] == "User registered successfully"
            assert "data" in result
            assert result["data"]["username"] == "johndoe"
            assert result["data"]["email"] == "john.doe@example.com"
            assert result["data"]["email_verified"] is False
            assert "email_verification_token" in result["data"]

            user_repo = RepositoryRegistry().user_repository
            user = user_repo.get_by_email(session, email="john.doe@example.com", include_deleted=False)
            assert user is not None
            assert user.username == "johndoe"
            assert user.email_verified is False
            assert user.email_verification_token is not None

    def test_register_user_invalid_email_format(self, manager):
        """Scenario: User tries to register with invalid email format."""
        with manager.engine.session_context(auto_commit=True) as session:
            with pytest.raises(RegistrationInvalidEmailFormatError) as exc_info:
                RegistrationService.register_user(
                    session,
                    username="johndoe",
                    email="invalid-email",
                    password="SecurePass123!",
                    name="John",
                    surname="Doe"
                )
            assert exc_info.value.error_details["email"] == "invalid-email"

    def test_register_user_weak_password(self, manager):
        """Scenario: User tries to register with weak password."""
        with manager.engine.session_context(auto_commit=True) as session:
            with pytest.raises(RegistrationWeakPasswordError) as exc_info:
                RegistrationService.register_user(
                    session,
                    username="johndoe",
                    email="john.doe@example.com",
                    password="123",
                    name="John",
                    surname="Doe"
                )
            assert "validation_errors" in exc_info.value.error_details

    def test_register_user_invalid_username(self, manager):
        """Scenario: User tries to register with invalid username."""
        with manager.engine.session_context(auto_commit=True) as session:
            with pytest.raises(RegistrationInvalidUsernameError) as exc_info:
                RegistrationService.register_user(
                    session,
                    username="ab",
                    email="john.doe@example.com",
                    password="SecurePass123!",
                    name="John",
                    surname="Doe"
                )
            assert exc_info.value.error_details["username"] == "ab"
            assert "validation_errors" in exc_info.value.error_details

    def test_register_user_email_already_exists(self, manager):
        """Scenario: User tries to register with email that already exists."""
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
            with pytest.raises(RegistrationEmailAlreadyExistsError) as exc_info:
                RegistrationService.register_user(
                    session,
                    username="johndoe2",
                    email="john.doe@example.com",
                    password="SecurePass123!",
                    name="John",
                    surname="Doe"
                )
            assert exc_info.value.error_details["email"] == "john.doe@example.com"

    def test_register_user_username_already_exists(self, manager):
        """Scenario: User tries to register with username that already exists."""
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
            with pytest.raises(RegistrationUsernameAlreadyExistsError) as exc_info:
                RegistrationService.register_user(
                    session,
                    username="johndoe",
                    email="john.doe2@example.com",
                    password="SecurePass123!",
                    name="John",
                    surname="Doe"
                )
            assert exc_info.value.error_details["username"] == "johndoe"

    def test_verify_email_success(self, manager):
        """Scenario: User successfully verifies email with valid token."""
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

        with manager.engine.session_context(auto_commit=True) as session:
            result = RegistrationService.verify_email(session, verification_token=verification_token)

            assert result["message"] == "Email verified successfully"
            assert result["data"]["email_verified"] is True
            assert result["data"]["email"] == "john.doe@example.com"

            user_repo = RepositoryRegistry().user_repository
            user = user_repo.get_by_email(session, email="john.doe@example.com", include_deleted=False)
            assert user.email_verified is True
            assert user.email_verified_at is not None
            assert user.email_verification_token is None

    def test_verify_email_token_not_found(self, manager):
        """Scenario: User tries to verify email with non-existent token."""
        with manager.engine.session_context(auto_commit=True) as session:
            with pytest.raises(EmailVerificationTokenNotFoundError):
                RegistrationService.verify_email(session, verification_token="non_existent_token_12345")

    def test_verify_email_already_verified(self, manager):
        """Scenario: User tries to verify email that is already verified."""
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
            with pytest.raises(EmailAlreadyVerifiedError) as exc_info:
                RegistrationService.verify_email(session, verification_token=verification_token)
            assert exc_info.value.error_details["email"] == "john.doe@example.com"

    def test_verify_email_invalid_token(self, manager):
        """Scenario: User tries to verify email with invalid token (wrong hash)."""
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
            with pytest.raises(EmailVerificationTokenInvalidError):
                RegistrationService.verify_email(session, verification_token="invalid_token_12345")

    def test_verify_email_expired_token_auto_resend(self, manager):
        """Scenario: User tries to verify email with expired token, system auto-generates new token."""
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

            user_repo = RepositoryRegistry().user_repository
            user = user_repo.get_by_email(session, email="john.doe@example.com", include_deleted=False)
            user.email_verification_token_expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
            user_repo.update(session, user)

        with manager.engine.session_context(auto_commit=True) as session:
            with pytest.raises(EmailVerificationTokenInvalidError) as exc_info:
                RegistrationService.verify_email(session, verification_token=verification_token)
            
            assert "expired" in exc_info.value.message.lower() or "new" in exc_info.value.message.lower()

            user_repo = RepositoryRegistry().user_repository
            user = user_repo.get_by_email(session, email="john.doe@example.com", include_deleted=False)
            assert user.email_verification_token is not None
            assert user.email_verification_token != verification_token

    def test_resend_verification_email_success(self, manager):
        """Scenario: User successfully requests resend of verification email."""
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
            result = RegistrationService.resend_verification_email(session, email="john.doe@example.com")

            assert result["message"] == "Verification email sent successfully"
            assert result["data"]["email"] == "john.doe@example.com"
            assert result["data"]["email_verified"] is False
            assert "email_verification_token" in result["data"]

            user_repo = RepositoryRegistry().user_repository
            user = user_repo.get_by_email(session, email="john.doe@example.com", include_deleted=False)
            assert user.email_verification_token is not None

    def test_resend_verification_email_not_found(self, manager):
        """Scenario: User tries to resend verification email for non-existent email."""
        with manager.engine.session_context(auto_commit=True) as session:
            result = RegistrationService.resend_verification_email(session, email="nonexistent@example.com")

            assert result["message"] == "E-posta bulunamadı, doğrulama e-postası yeniden gönderilmedi"
            assert result["data"]["email"] == "nonexistent@example.com"
            assert result["data"]["email_verified"] is False

    def test_resend_verification_email_already_verified(self, manager):
        """Scenario: User tries to resend verification email for already verified email."""
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
            with pytest.raises(EmailAlreadyVerifiedError) as exc_info:
                RegistrationService.resend_verification_email(session, email="john.doe@example.com")
            assert exc_info.value.error_details["email"] == "john.doe@example.com"

    def test_complete_registration_flow(self, manager):
        """Scenario: Complete user registration flow from registration to email verification."""
        with manager.engine.session_context(auto_commit=True) as session:
            registration_result = RegistrationService.register_user(
                session,
                username="johndoe",
                email="john.doe@example.com",
                password="SecurePass123!",
                name="John",
                surname="Doe",
                country_code="US",
                phone_number="+15551234567"
            )

            assert registration_result["data"]["email_verified"] is False
            verification_token = registration_result["data"]["email_verification_token"]

            user_repo = RepositoryRegistry().user_repository
            user = user_repo.get_by_email(session, email="john.doe@example.com", include_deleted=False)
            assert user.email_verified is False
            assert user.email_verification_token is not None

        with manager.engine.session_context(auto_commit=True) as session:
            verification_result = RegistrationService.verify_email(session, verification_token=verification_token)

            assert verification_result["data"]["email_verified"] is True

            user_repo = RepositoryRegistry().user_repository
            user = user_repo.get_by_email(session, email="john.doe@example.com", include_deleted=False)
            assert user.email_verified is True
            assert user.email_verified_at is not None
            assert user.email_verification_token is None

    def test_multiple_users_registration(self, manager):
        """Scenario: Multiple users register successfully with different credentials."""
        users_data = [
            {"username": "user1", "email": "user1@example.com", "name": "User", "surname": "One"},
            {"username": "user2", "email": "user2@example.com", "name": "User", "surname": "Two"},
            {"username": "user3", "email": "user3@example.com", "name": "User", "surname": "Three"},
        ]

        for user_data in users_data:
            with manager.engine.session_context(auto_commit=True) as session:
                result = RegistrationService.register_user(
                    session,
                    username=user_data["username"],
                    email=user_data["email"],
                    password="SecurePass123!",
                    name=user_data["name"],
                    surname=user_data["surname"]
                )
                assert result["data"]["username"] == user_data["username"]
                assert result["data"]["email"] == user_data["email"]

        with manager.engine.session_context(auto_commit=True) as session:
            user_repo = RepositoryRegistry().user_repository
            for user_data in users_data:
                user = user_repo.get_by_email(session, email=user_data["email"], include_deleted=False)
                assert user is not None
                assert user.username == user_data["username"]
