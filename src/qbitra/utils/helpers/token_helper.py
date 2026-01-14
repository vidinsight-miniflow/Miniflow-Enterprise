import secrets
from hmac import compare_digest
from datetime import datetime, timezone, timedelta

from qbitra.core.qbitra_logger import get_logger
from qbitra.core.exceptions import (
    TokenInvalidError,
    TokenGenerationError,
    DataHashingError,
)
from qbitra.utils.helpers.crypto_helper import hash_data
from qbitra.utils.handlers.configuration_handler import ConfigurationHandler


# Helpers katmanı logger'ı (logs/helpers/token_helper/service.log)
_logger = get_logger("token_helper", parent_folder="helpers")


def _now() -> datetime:
    """Get current UTC time."""
    return datetime.now(timezone.utc)


def generate_token(length: int = 32, hash: bool = False) -> str:
    """Generate a secure random token."""
    if length < 1:
        raise TokenGenerationError(
            length=length,
            message=f"Token length must be greater than 0, got {length}"
        )
    
    if length > 512:
        _logger.warning(
            "Token length çok büyük, maksimum değer kullanılıyor",
            extra={"provided_length": length, "max_length": 512}
        )
        length = 512
    
    try:
        _logger.debug("Token oluşturuluyor", extra={"length": length, "hash": hash})
        token = secrets.token_urlsafe(length)
    
        if hash:
            try:
                hashed_token = hash_data(token)
                _logger.debug("Token oluşturuldu ve hash'lendi", extra={"token_length": len(token)})
                return hashed_token
            except DataHashingError as e:
                raise TokenGenerationError(
                    token_type="hashed",
                    length=length,
                    message=f"Token generation failed during hashing: {str(e)}",
                    cause=e
                ) from e
        
        _logger.debug("Token başarıyla oluşturuldu", extra={"token_length": len(token)})
        return token
    except Exception as e:
        _logger.error(
            "Token oluşturma hatası",
            extra={"length": length, "error": str(e)},
            exc_info=True
        )
        raise TokenGenerationError(
            length=length,
            message=f"Token generation failed: {str(e)}",
            cause=e
        ) from e


def generate_token_with_prefix(prefix: str, length: int = 32, hash: bool = False) -> str:
    """Generate a secure random token with a prefix."""
    if not prefix:
        raise TokenGenerationError(
            token_type="prefixed",
            message="Token prefix cannot be empty"
        )
    
    if length < 1:
        raise TokenGenerationError(
            token_type="prefixed",
            length=length,
            message=f"Token length must be greater than 0, got {length}"
        )
    
    new_length = length - len(prefix) - 1
    if new_length <= 0:
        raise TokenInvalidError(
            token_type="prefixed",
            reason="prefix_too_long",
            message=f"Prefix length ({len(prefix)}) is greater than or equal to token length ({length})"
        )
    
    try:
        _logger.debug(
            "Prefix'li token oluşturuluyor",
            extra={"prefix": prefix, "length": length, "actual_length": new_length, "hash": hash}
        )
        # Use token_bytes and b64encode to have better control over length if necessary,
        # but token_urlsafe is standard. Note: it won't be EXACTLY length due to b64 overhead.
        token = f"{prefix}_{secrets.token_urlsafe(new_length)}"
        
        if hash:
            hashed_token = hash_data(token)
            _logger.debug("Prefix'li token oluşturuldu ve hash'lendi", extra={"prefix": prefix, "token_length": len(token)})
            return hashed_token
        
        _logger.debug("Prefix'li token başarıyla oluşturuldu", extra={"prefix": prefix, "token_length": len(token)})
        return token
    except Exception as e:
        _logger.error(
            "Prefix'li token oluşturma hatası",
            extra={"prefix": prefix, "length": length, "error": str(e)},
            exc_info=True
        )
        raise TokenGenerationError(
            token_type="prefixed",
            length=length,
            message=f"Token generation failed: {str(e)}",
            cause=e
        ) from e


def verify_hashed_token(token: str, hashed_token: str) -> bool:
    """Verify if a token matches its hashed version."""
    if not token or not hashed_token:
        return False
    
    try:
        computed_hash = hash_data(token)
        # Use constant-time comparison to prevent timing attacks
        is_valid = compare_digest(computed_hash, hashed_token)
        _logger.debug("Hashed token doğrulama tamamlandı", extra={"is_valid": is_valid})
        return is_valid
    except DataHashingError as e:
        _logger.warning("Hashed token doğrulama hatası: hash işlemi başarısız", extra={"error": str(e)}, exc_info=True)
        return False


def is_token_expired(expires_at: datetime) -> bool:
    """Check if a token has expired."""
    if not expires_at:
        return True
        
    try:
        if not isinstance(expires_at, datetime):
            return True
        
        # Create immutable copy to avoid modifying the original parameter
        expires_at_utc = expires_at
        if expires_at_utc.tzinfo is None:
            expires_at_utc = expires_at_utc.replace(tzinfo=timezone.utc)
        
        now = _now()
        is_expired = now > expires_at_utc
        
        _logger.debug(
            "Token expiration kontrolü",
            extra={
                "is_expired": is_expired,
                "expires_at": expires_at_utc.isoformat(),
                "now": now.isoformat()
            }
        )
        
        return is_expired
    except Exception as e:
        _logger.warning("Token expiration kontrolü hatası", extra={"error": str(e)}, exc_info=True)
        return True


# ============================================================================
# SPECIALIZED TOKEN GENERATORS
# ============================================================================

def generate_email_verification_token() -> tuple[str, str]:
    """
    Generate email verification token with prefix.
    
    Returns:
        tuple[str, str]: (original_token, hashed_token)
            - original_token: Token to be sent to user via email
            - hashed_token: Token to be stored in database
    """
    ConfigurationHandler.ensure_loaded()
    
    prefix = ConfigurationHandler.get_value_as_str("Tokens", "email_verification_prefix", fallback="email_verify")
    length = ConfigurationHandler.get_value_as_int("Tokens", "email_verification_length", fallback=32)
    
    _logger.debug("Email verification token oluşturuluyor", extra={"prefix": prefix, "length": length})
    
    # Generate original token (not hashed)
    original_token = generate_token_with_prefix(prefix, length, hash=False)
    
    # Hash the token for database storage
    hashed_token = hash_data(original_token)
    
    return original_token, hashed_token


def generate_password_reset_token() -> tuple[str, str]:
    """
    Generate password reset token with prefix.
    
    Returns:
        tuple[str, str]: (original_token, hashed_token)
            - original_token: Token to be sent to user via email
            - hashed_token: Token to be stored in database
    """
    ConfigurationHandler.ensure_loaded()
    
    prefix = ConfigurationHandler.get_value_as_str("Tokens", "password_reset_prefix", fallback="pwd_reset")
    length = ConfigurationHandler.get_value_as_int("Tokens", "password_reset_length", fallback=32)
    
    _logger.debug("Password reset token oluşturuluyor", extra={"prefix": prefix, "length": length})
    
    # Generate original token (not hashed)
    original_token = generate_token_with_prefix(prefix, length, hash=False)
    
    # Hash the token for database storage
    hashed_token = hash_data(original_token)
    
    return original_token, hashed_token


def generate_workspace_invitation_token() -> str:
    """Generate workspace invitation token with prefix and hash."""
    ConfigurationHandler.ensure_loaded()
    
    prefix = ConfigurationHandler.get_value_as_str("Tokens", "workspace_invite_prefix", fallback="ws_invite")
    length = ConfigurationHandler.get_value_as_int("Tokens", "workspace_invite_length", fallback=48)
    
    _logger.debug("Workspace invitation token oluşturuluyor", extra={"prefix": prefix, "length": length})
    return generate_token_with_prefix(prefix, length, hash=True)


def generate_api_key() -> str:
    """Generate API key token with prefix and hash."""
    ConfigurationHandler.ensure_loaded()
    
    prefix = ConfigurationHandler.get_value_as_str("Tokens", "api_key_prefix", fallback="api_key")
    length = ConfigurationHandler.get_value_as_int("Tokens", "api_key_length", fallback=64)
    
    _logger.debug("API key oluşturuluyor", extra={"prefix": prefix, "length": length})
    return generate_token_with_prefix(prefix, length, hash=True)


# ============================================================================
# TOKEN EXPIRATION HELPERS
# ============================================================================

def get_email_verification_expires_at() -> datetime:
    """Get expiration datetime for email verification token."""
    ConfigurationHandler.ensure_loaded()
    hours = ConfigurationHandler.get_value_as_int("Tokens", "email_verification_expire_hours", fallback=24)
    return _now() + timedelta(hours=hours)


def get_password_reset_expires_at() -> datetime:
    """Get expiration datetime for password reset token."""
    ConfigurationHandler.ensure_loaded()
    hours = ConfigurationHandler.get_value_as_int("Tokens", "password_reset_expire_hours", fallback=1)
    return _now() + timedelta(hours=hours)


def get_workspace_invite_expires_at() -> datetime:
    """Get expiration datetime for workspace invitation token."""
    ConfigurationHandler.ensure_loaded()
    days = ConfigurationHandler.get_value_as_int("Tokens", "workspace_invite_expire_days", fallback=7)
    return _now() + timedelta(days=days)
