from enum import Enum


class LoginStatus(str, Enum):
    """Login attempt status"""
    SUCCESS = "SUCCESS"                                        # Login successful
    FAILED_INVALID_CREDENTIALS = "FAILED_INVALID_CREDENTIALS"  # Wrong password/email
    FAILED_EMAIL_NOT_VERIFIED = "FAILED_EMAIL_NOT_VERIFIED"    # Email not verified
    FAILED_RATE_LIMITED = "FAILED_RATE_LIMITED"                # Too many attempts
    FAILED_ACCOUNT_LOCKED = "FAILED_ACCOUNT_LOCKED"            # Account locked
    FAILED_ACCOUNT_SUSPENDED = "FAILED_ACCOUNT_SUSPENDED"      # Account suspended


class LoginMethod(str, Enum):
    """Login authentication method"""
    PASSWORD = "PASSWORD"           # Email/password login


__all__ = [
    "LoginStatus",
    "LoginMethod",
]
