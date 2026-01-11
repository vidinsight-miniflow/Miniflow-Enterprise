"""
Security-related exception classes for QBitra.
These exceptions are used for encryption, decryption, password hashing, and security-related errors.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from .base import QBitraException


class SecurityException(QBitraException):
    """Base exception class for security-related errors."""
    pass


class EncryptionError(SecurityException):
    """Raised when encryption/decryption operations fail."""
    
    status_code = 500
    error_code = "ENCRYPTION_ERROR"
    error_message = "Encryption operation failed"

    def __init__(
        self,
        operation: Optional[str] = None,
        message: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        if not error_details:
            error_details = {}
        if operation:
            error_details["operation"] = operation
        
        if not message:
            if operation:
                message = (
                    f"Encryption operation '{operation}' failed. "
                    "Please check the encryption key and data format."
                )
            else:
                message = (
                    "Encryption operation failed. "
                    "Please check the encryption key and data format."
                )
        
        super().__init__(
            error_message=message,
            error_details=error_details,
            cause=cause
        )


class EncryptionKeyError(SecurityException):
    """Raised when encryption key is invalid, missing, or malformed."""
    
    status_code = 500
    error_code = "ENCRYPTION_KEY_ERROR"
    error_message = "Encryption key error"

    def __init__(
        self,
        key_format: Optional[str] = None,
        key_length: Optional[int] = None,
        message: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        if not error_details:
            error_details = {}
        if key_format:
            error_details["key_format"] = key_format
        if key_length is not None:
            error_details["key_length"] = key_length
        
        if not message:
            if key_format:
                message = (
                    f"Encryption key format error: {key_format}. "
                    "ENCRYPTION_KEY must be a base64 encoded 32-byte key or a 64-character hex string."
                )
            else:
                message = (
                    "Encryption key error. "
                    "ENCRYPTION_KEY must be a base64 encoded 32-byte key or a 64-character hex string."
                )
        
        super().__init__(
            error_message=message,
            error_details=error_details,
            cause=cause
        )


class PasswordHashingError(SecurityException):
    """Raised when password hashing operations fail."""
    
    status_code = 500
    error_code = "PASSWORD_HASHING_ERROR"
    error_message = "Password hashing failed"

    def __init__(
        self,
        rounds: Optional[int] = None,
        message: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        if not error_details:
            error_details = {}
        if rounds is not None:
            error_details["rounds"] = rounds
        
        if not message:
            message = (
                "Password hashing failed. "
                "Please check the password and try again."
            )
        
        super().__init__(
            error_message=message,
            error_details=error_details,
            cause=cause
        )


class PasswordValidationError(SecurityException):
    """Raised when password validation fails."""
    
    status_code = 400
    error_code = "PASSWORD_VALIDATION_ERROR"
    error_message = "Password validation error"

    def __init__(
        self,
        field_name: Optional[str] = None,
        message: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        if not error_details:
            error_details = {}
        if field_name:
            error_details["field_name"] = field_name
        
        if not message:
            if field_name:
                message = (
                    f"Password validation failed for field '{field_name}'. "
                    "Password is required and cannot be empty."
                )
            else:
                message = (
                    "Password validation failed. "
                    "Password is required and cannot be empty."
                )
        
        super().__init__(
            error_message=message,
            error_details=error_details,
            cause=cause
        )


class DecryptionError(EncryptionError):
    """Raised when decryption operations fail (invalid token, wrong key, etc.)."""
    
    status_code = 400
    error_code = "DECRYPTION_ERROR"
    error_message = "Decryption operation failed"

    def __init__(
        self,
        invalid_token: bool = False,
        message: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        if not error_details:
            error_details = {}
        error_details["invalid_token"] = invalid_token
        
        if not message:
            if invalid_token:
                message = (
                    "Decryption failed: Invalid token. "
                    "This usually means the encryption key is wrong or the data is corrupted."
                )
            else:
                message = (
                    "Decryption operation failed. "
                    "Please check the encrypted data and encryption key."
                )
        
        super().__init__(
            operation="decryption",
            message=message,
            error_details=error_details,
            cause=cause
        )


class DataHashingError(SecurityException):
    """Raised when data hashing operations fail."""
    
    status_code = 500
    error_code = "DATA_HASHING_ERROR"
    error_message = "Data hashing failed"

    def __init__(
        self,
        hash_algorithm: Optional[str] = None,
        message: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        if not error_details:
            error_details = {}
        if hash_algorithm:
            error_details["hash_algorithm"] = hash_algorithm
        
        if not message:
            if hash_algorithm:
                message = (
                    f"Data hashing failed using {hash_algorithm} algorithm. "
                    "Please check the data and try again."
                )
            else:
                message = (
                    "Data hashing failed. "
                    "Please check the data and try again."
                )
        
        super().__init__(
            error_message=message,
            error_details=error_details,
            cause=cause
        )


class JWTError(SecurityException):
    """Base exception class for JWT-related errors."""
    pass


class JWTConfigurationError(JWTError):
    """Raised when JWT configuration is missing or invalid."""
    
    status_code = 500
    error_code = "JWT_CONFIGURATION_ERROR"
    error_message = "JWT configuration error"

    def __init__(
        self,
        config_key: Optional[str] = None,
        message: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        if not error_details:
            error_details = {}
        if config_key:
            error_details["config_key"] = config_key
        
        if not message:
            if config_key:
                message = (
                    f"JWT configuration error: {config_key} is missing or invalid. "
                    "Please check your JWT configuration settings."
                )
            else:
                message = (
                    "JWT configuration error. "
                    "Please check your JWT configuration settings."
                )
        
        super().__init__(
            error_message=message,
            error_details=error_details,
            cause=cause
        )


class JWTExpiredError(JWTError):
    """Raised when JWT token has expired."""
    
    status_code = 401
    error_code = "JWT_EXPIRED_ERROR"
    error_message = "JWT token expired"

    def __init__(
        self,
        token_type: Optional[str] = None,
        expired_at: Optional[int] = None,
        message: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        if not error_details:
            error_details = {}
        if token_type:
            error_details["token_type"] = token_type
        if expired_at:
            error_details["expired_at"] = expired_at
        
        if not message:
            if token_type:
                message = (
                    f"{token_type.capitalize()} token has expired. "
                    "Please refresh your token or login again."
                )
            else:
                message = (
                    "JWT token has expired. "
                    "Please refresh your token or login again."
                )
        
        super().__init__(
            error_message=message,
            error_details=error_details,
            cause=cause
        )


class JWTInvalidTokenError(JWTError):
    """Raised when JWT token is invalid."""
    
    status_code = 401
    error_code = "JWT_INVALID_TOKEN_ERROR"
    error_message = "JWT token invalid"

    def __init__(
        self,
        token_type: Optional[str] = None,
        reason: Optional[str] = None,
        message: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        if not error_details:
            error_details = {}
        if token_type:
            error_details["token_type"] = token_type
        if reason:
            error_details["reason"] = reason
        
        if not message:
            if reason:
                message = (
                    f"JWT token is invalid: {reason}. "
                    "Please check your token and try again."
                )
            else:
                message = (
                    "JWT token is invalid. "
                    "Please check your token and try again."
                )
        
        super().__init__(
            error_message=message,
            error_details=error_details,
            cause=cause
        )


class JWTMissingClaimError(JWTError):
    """Raised when required JWT claim is missing."""
    
    status_code = 401
    error_code = "JWT_MISSING_CLAIM_ERROR"
    error_message = "JWT token missing required claim"

    def __init__(
        self,
        claim: Optional[str] = None,
        message: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        if not error_details:
            error_details = {}
        if claim:
            error_details["missing_claim"] = claim
        
        if not message:
            if claim:
                message = (
                    f"JWT token is missing required claim: {claim}. "
                    "Please check your token and try again."
                )
            else:
                message = (
                    "JWT token is missing required claim. "
                    "Please check your token and try again."
                )
        
        super().__init__(
            error_message=message,
            error_details=error_details,
            cause=cause
        )


class JWTTokenTypeError(JWTError):
    """Raised when JWT token type does not match expected type."""
    
    status_code = 401
    error_code = "JWT_TOKEN_TYPE_ERROR"
    error_message = "JWT token type mismatch"

    def __init__(
        self,
        expected_type: Optional[str] = None,
        actual_type: Optional[str] = None,
        message: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        if not error_details:
            error_details = {}
        if expected_type:
            error_details["expected_type"] = expected_type
        if actual_type:
            error_details["actual_type"] = actual_type
        
        if not message:
            if expected_type and actual_type:
                message = (
                    f"JWT token type mismatch. Expected '{expected_type}', got '{actual_type}'. "
                    "Please use the correct token type."
                )
            else:
                message = (
                    "JWT token type mismatch. "
                    "Please use the correct token type."
                )
        
        super().__init__(
            error_message=message,
            error_details=error_details,
            cause=cause
        )


class JWTRevokedError(JWTError):
    """Raised when JWT token has been revoked."""
    
    status_code = 401
    error_code = "JWT_REVOKED_ERROR"
    error_message = "JWT token revoked"

    def __init__(
        self,
        jti: Optional[str] = None,
        message: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        if not error_details:
            error_details = {}
        if jti:
            error_details["jti"] = jti
        
        if not message:
            if jti:
                message = (
                    f"JWT token has been revoked (JTI: {jti}). "
                    "Please login again to get a new token."
                )
            else:
                message = (
                    "JWT token has been revoked. "
                    "Please login again to get a new token."
                )
        
        super().__init__(
            error_message=message,
            error_details=error_details,
            cause=cause
        )


class TokenGenerationError(SecurityException):
    """Raised when token generation fails."""
    
    status_code = 500
    error_code = "TOKEN_GENERATION_ERROR"
    error_message = "Token generation failed"

    def __init__(
        self,
        token_type: Optional[str] = None,
        length: Optional[int] = None,
        message: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        if not error_details:
            error_details = {}
        if token_type:
            error_details["token_type"] = token_type
        if length is not None:
            error_details["length"] = length
        
        if not message:
            if token_type:
                message = (
                    f"Token generation failed for {token_type} token. "
                    "Please try again."
                )
            else:
                message = (
                    "Token generation failed. "
                    "Please try again."
                )
        
        super().__init__(
            error_message=message,
            error_details=error_details,
            cause=cause
        )


class TokenInvalidError(SecurityException):
    """Raised when token is invalid."""
    
    status_code = 400
    error_code = "TOKEN_INVALID_ERROR"
    error_message = "Token invalid"

    def __init__(
        self,
        token_type: Optional[str] = None,
        reason: Optional[str] = None,
        message: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        if not error_details:
            error_details = {}
        if token_type:
            error_details["token_type"] = token_type
        if reason:
            error_details["reason"] = reason
        
        if not message:
            if reason:
                message = (
                    f"Token is invalid: {reason}. "
                    "Please check your token and try again."
                )
            else:
                message = (
                    "Token is invalid. "
                    "Please check your token and try again."
                )
        
        super().__init__(
            error_message=message,
            error_details=error_details,
            cause=cause
        )


class TokenExpiredError(SecurityException):
    """Raised when token has expired."""
    
    status_code = 401
    error_code = "TOKEN_EXPIRED_ERROR"
    error_message = "Token expired"

    def __init__(
        self,
        token_type: Optional[str] = None,
        expired_at: Optional[datetime] = None,
        message: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        if not error_details:
            error_details = {}
        if token_type:
            error_details["token_type"] = token_type
        if expired_at:
            error_details["expired_at"] = expired_at.isoformat() if isinstance(expired_at, datetime) else str(expired_at)
        
        if not message:
            if token_type:
                message = (
                    f"{token_type.capitalize()} token has expired. "
                    "Please generate a new token."
                )
            else:
                message = (
                    "Token has expired. "
                    "Please generate a new token."
                )
        
        super().__init__(
            error_message=message,
            error_details=error_details,
            cause=cause
        )
