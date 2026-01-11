from ..base import QBitraException


class ServiceException(QBitraException):
    status_code: int = 500
    error_code: str = "SERVICE_ERROR"
    error_message: str = "Service error occurred"


from .auth import (
    AuthServiceException,
    RegistrationEmailAlreadyExistsError,
    RegistrationUsernameAlreadyExistsError,
    RegistrationInvalidEmailFormatError,
    RegistrationWeakPasswordError,
    RegistrationInvalidUsernameError,
    EmailVerificationTokenNotFoundError,
    EmailVerificationTokenInvalidError,
    EmailAlreadyVerifiedError,
    InvalidCredentialsError,
    EmailNotVerifiedError,
    AccountLockedError,
    AccountPermanentlyLockedError,
    RateLimitedError,
    InvalidTokenError,
    SessionNotFoundError,
    SessionRevokedError,
)

__all__ = [
    "ServiceException",
    "AuthServiceException",
    "RegistrationEmailAlreadyExistsError",
    "RegistrationUsernameAlreadyExistsError",
    "RegistrationInvalidEmailFormatError",
    "RegistrationWeakPasswordError",
    "RegistrationInvalidUsernameError",
    "EmailVerificationTokenNotFoundError",
    "EmailVerificationTokenInvalidError",
    "EmailAlreadyVerifiedError",
    "InvalidCredentialsError",
    "EmailNotVerifiedError",
    "AccountLockedError",
    "AccountPermanentlyLockedError",
    "RateLimitedError",
    "InvalidTokenError",
    "SessionNotFoundError",
    "SessionRevokedError",
]
