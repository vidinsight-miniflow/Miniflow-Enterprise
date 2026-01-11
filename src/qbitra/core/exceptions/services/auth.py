from typing import Optional, Dict, Any
from datetime import datetime
from ..base import QBitraException


class AuthServiceException(QBitraException):
    status_code: int = 400
    error_code: str = "AUTH_ERROR"
    error_message: str = "Authentication error occurred"


class RegistrationEmailAlreadyExistsError(AuthServiceException):
    status_code: int = 409
    error_code: str = "REGISTRATION_EMAIL_EXISTS"
    error_message: str = "Email address already registered"

    def __init__(self, email: str, **kwargs):
        super().__init__(
            error_details={"email": email},
            **kwargs
        )


class RegistrationUsernameAlreadyExistsError(AuthServiceException):
    status_code: int = 409
    error_code: str = "REGISTRATION_USERNAME_EXISTS"
    error_message: str = "Username already taken"

    def __init__(self, username: str, **kwargs):
        super().__init__(
            error_details={"username": username},
            **kwargs
        )


class RegistrationInvalidEmailFormatError(AuthServiceException):
    status_code: int = 400
    error_code: str = "REGISTRATION_INVALID_EMAIL"
    error_message: str = "Invalid email format"

    def __init__(self, email: str, **kwargs):
        super().__init__(
            error_details={"email": email},
            **kwargs
        )


class RegistrationWeakPasswordError(AuthServiceException):
    status_code: int = 400
    error_code: str = "REGISTRATION_WEAK_PASSWORD"
    error_message: str = "Password does not meet strength requirements"

    def __init__(self, errors: list, **kwargs):
        super().__init__(
            error_details={"validation_errors": errors},
            **kwargs
        )


class RegistrationInvalidUsernameError(AuthServiceException):
    status_code: int = 400
    error_code: str = "REGISTRATION_INVALID_USERNAME"
    error_message: str = "Username does not meet requirements"

    def __init__(self, username: str, errors: list, **kwargs):
        super().__init__(
            error_details={"username": username, "validation_errors": errors},
            **kwargs
        )


class EmailVerificationTokenNotFoundError(AuthServiceException):
    status_code: int = 404
    error_code: str = "EMAIL_VERIFICATION_TOKEN_NOT_FOUND"
    error_message: str = "Verification token not found or invalid"


class EmailVerificationTokenInvalidError(AuthServiceException):
    status_code: int = 400
    error_code: str = "EMAIL_VERIFICATION_TOKEN_INVALID"
    error_message: str = "Verification token is invalid"


class EmailAlreadyVerifiedError(AuthServiceException):
    status_code: int = 400
    error_code: str = "EMAIL_ALREADY_VERIFIED"
    error_message: str = "Email address is already verified"

    def __init__(self, email: str, **kwargs):
        super().__init__(
            error_details={"email": email},
            **kwargs
        )


class InvalidCredentialsError(AuthServiceException):
    status_code: int = 401
    error_code: str = "INVALID_CREDENTIALS"
    error_message: str = "Invalid email/username or password"


class EmailNotVerifiedError(AuthServiceException):
    status_code: int = 403
    error_code: str = "EMAIL_NOT_VERIFIED"
    error_message: str = "Email verification required before login"

    def __init__(self, email: str, **kwargs):
        super().__init__(
            error_details={"email": email},
            **kwargs
        )


class AccountLockedError(AuthServiceException):
    status_code: int = 423
    error_code: str = "ACCOUNT_LOCKED"
    error_message: str = "Account is locked"

    def __init__(self, locked_until: Optional[datetime] = None, reason: Optional[str] = None, **kwargs):
        details = {}
        if locked_until:
            details["locked_until"] = locked_until.isoformat()
        if reason:
            details["reason"] = reason
        super().__init__(
            error_details=details,
            **kwargs
        )


class AccountPermanentlyLockedError(AuthServiceException):
    status_code: int = 423
    error_code: str = "ACCOUNT_PERMANENTLY_LOCKED"
    error_message: str = "Account has been permanently locked. Please contact support"


class RateLimitedError(AuthServiceException):
    status_code: int = 429
    error_code: str = "RATE_LIMITED"
    error_message: str = "Too many failed attempts"

    def __init__(self, lockout_duration: int, **kwargs):
        super().__init__(
            error_details={"lockout_duration_minutes": lockout_duration},
            **kwargs
        )


class InvalidTokenError(AuthServiceException):
    status_code: int = 401
    error_code: str = "INVALID_TOKEN"
    error_message: str = "Invalid or expired token"


class SessionNotFoundError(AuthServiceException):
    status_code: int = 404
    error_code: str = "SESSION_NOT_FOUND"
    error_message: str = "Session not found"


class SessionRevokedError(AuthServiceException):
    status_code: int = 401
    error_code: str = "SESSION_REVOKED"
    error_message: str = "Session has been revoked"

