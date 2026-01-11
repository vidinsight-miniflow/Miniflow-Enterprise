import pytest
import secrets
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

from qbitra.utils.helpers import token_helper
from qbitra.core.exceptions import (
    TokenExpiredError,
    TokenInvalidError,
    TokenGenerationError,
)

def test_generate_token_basic():
    """Test basic token generation with length and hash options."""
    # Default length (32 bytes -> urlsafe string will be longer)
    token = token_helper.generate_token()
    assert isinstance(token, str)
    assert len(token) > 32
    
    # Custom length
    token_16 = token_helper.generate_token(length=16)
    assert len(token_16) < len(token)
    
    # Hashed token
    hashed_token = token_helper.generate_token(hash=True)
    # SHA-256 hex is 64 chars
    assert len(hashed_token) == 64
    assert all(c in "0123456789abcdef" for c in hashed_token)

def test_generate_token_invalid_length():
    """Test error handling for invalid token lengths."""
    with pytest.raises(TokenGenerationError) as exc:
        token_helper.generate_token(length=0)
    assert "greater than 0" in str(exc.value)
    
    # Too large length should be capped at 512
    with patch("secrets.token_urlsafe", wraps=secrets.token_urlsafe) as mock_secrets:
        token_helper.generate_token(length=1000)
        mock_secrets.assert_called_with(512)

def test_generate_token_with_prefix():
    """Test token generation with a custom prefix."""
    prefix = "TEST"
    token = token_helper.generate_token_with_prefix(prefix, length=32)
    
    assert token.startswith("TEST_")
    # token_urlsafe(n) returns approx 4/3 * n bytes. 
    # For new_length = 32 - 4 - 1 = 27, it will be around 36 chars.
    assert len(token) > 32 
    
    # Hashed prefixed token
    hashed = token_helper.generate_token_with_prefix(prefix, hash=True)
    assert len(hashed) == 64

def test_generate_token_with_prefix_invalid():
    """Test error handling for prefixed tokens."""
    # Empty prefix
    with pytest.raises(TokenGenerationError):
        token_helper.generate_token_with_prefix("", length=32)
    
    # Prefix too long for total length
    with pytest.raises(TokenInvalidError) as exc:
        token_helper.generate_token_with_prefix("VERY_LONG_PREFIX", length=5)
    assert "prefix_too_long" in exc.value.error_details.get("reason", "")

def test_verify_hashed_token():
    """Test verification of raw tokens against their hashes."""
    from qbitra.utils.helpers.crypto_helper import hash_data
    
    raw_token = "secret-token-123"
    hashed_token = hash_data(raw_token)
    
    assert token_helper.verify_hashed_token(raw_token, hashed_token) is True
    assert token_helper.verify_hashed_token("wrong-token", hashed_token) is False
    assert token_helper.verify_hashed_token("", hashed_token) is False
    assert token_helper.verify_hashed_token(raw_token, "") is False

def test_is_token_expired():
    """Test token expiration logic with UTC awareness."""
    fixed_now = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    
    with patch.object(token_helper, "_now", return_value=fixed_now):
        # Not expired (future)
        future = fixed_now + timedelta(minutes=10)
        assert token_helper.is_token_expired(future) is False
        
        # Expired (past)
        past = fixed_now - timedelta(minutes=10)
        assert token_helper.is_token_expired(past) is True
        
        # Exact time (now == expires_at) -> not expired (now > expires_at is False)
        assert token_helper.is_token_expired(fixed_now) is False
        
        # Just expired (1 second ago)
        just_expired = fixed_now - timedelta(seconds=1)
        assert token_helper.is_token_expired(just_expired) is True

def test_is_token_expired_timezone_handling():
    """Test that naive datetimes are correctly handled by converting to UTC."""
    fixed_now = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    naive_future = datetime(2026, 1, 1, 12, 10, 0)  # Naive (10 minutes later)
    naive_past = datetime(2026, 1, 1, 11, 50, 0)  # Naive (10 minutes earlier)
    
    with patch.object(token_helper, "_now", return_value=fixed_now):
        # Function handles naive by replacing with UTC
        assert token_helper.is_token_expired(naive_future) is False  # Future -> not expired
        assert token_helper.is_token_expired(naive_past) is True  # Past -> expired
        
        # Verify original parameter is not modified (immutable copy)
        assert naive_future.tzinfo is None  # Original should still be naive
        assert naive_past.tzinfo is None  # Original should still be naive

def test_is_token_expired_invalid_input():
    """Test error handling for invalid expiration inputs."""
    assert token_helper.is_token_expired(None) is True
    assert token_helper.is_token_expired("not-a-datetime") is True

def test_token_generation_unexpected_error():
    """Test catch-all exception handling in token generation."""
    with patch("secrets.token_urlsafe", side_effect=RuntimeError("Generic Error")):
        with pytest.raises(TokenGenerationError) as exc:
            token_helper.generate_token()
        assert "Token generation failed" in str(exc.value)

# ============================================================================
# SPECIALIZED TOKEN GENERATOR TESTS
# ============================================================================

from qbitra.utils.handlers.configuration_handler import ConfigurationHandler

def test_generate_email_verification_token():
    """Test specialized email verification token generation."""
    with patch.object(ConfigurationHandler, "get_value_as_str", return_value="custom_email") as mock_str, \
         patch.object(ConfigurationHandler, "get_value_as_int", return_value=40) as mock_int, \
         patch.object(ConfigurationHandler, "ensure_loaded"):
        
        original_token, hashed_token = token_helper.generate_email_verification_token()
        # Original token should have prefix
        assert original_token.startswith("custom_email_")
        # Hashed token should be 64 characters (SHA-256 hex)
        assert len(hashed_token) == 64
        # Verify they match
        assert token_helper.verify_hashed_token(original_token, hashed_token) is True
        mock_str.assert_any_call("Tokens", "email_verification_prefix", fallback="email_verify")
        mock_int.assert_any_call("Tokens", "email_verification_length", fallback=32)

def test_generate_password_reset_token():
    """Test specialized password reset token generation."""
    with patch.object(ConfigurationHandler, "get_value_as_str", return_value="pwd") as mock_str, \
         patch.object(ConfigurationHandler, "get_value_as_int", return_value=32) as mock_int, \
         patch.object(ConfigurationHandler, "ensure_loaded"):
        
        original_token, hashed_token = token_helper.generate_password_reset_token()
        # Original token should have prefix
        assert original_token.startswith("pwd_")
        # Hashed token should be 64 characters (SHA-256 hex)
        assert len(hashed_token) == 64
        # Verify they match
        assert token_helper.verify_hashed_token(original_token, hashed_token) is True
        mock_str.assert_any_call("Tokens", "password_reset_prefix", fallback="pwd_reset")

def test_generate_workspace_invitation_token():
    """Test specialized workspace invitation token generation."""
    with patch.object(ConfigurationHandler, "get_value_as_str", return_value="invite") as mock_str, \
         patch.object(ConfigurationHandler, "get_value_as_int", return_value=48) as mock_int, \
         patch.object(ConfigurationHandler, "ensure_loaded"):
        
        token = token_helper.generate_workspace_invitation_token()
        assert len(token) == 64

def test_generate_api_key():
    """Test specialized API key generation."""
    with patch.object(ConfigurationHandler, "get_value_as_str", return_value="api") as mock_str, \
         patch.object(ConfigurationHandler, "get_value_as_int", return_value=64) as mock_int, \
         patch.object(ConfigurationHandler, "ensure_loaded"):
        
        token = token_helper.generate_api_key()
        assert len(token) == 64

# ============================================================================
# SPECIALIZED EXPIRATION HELPER TESTS
# ============================================================================

def test_get_email_verification_expires_at():
    """Test specialized email expiration calculation."""
    fixed_now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    with patch.object(token_helper, "_now", return_value=fixed_now), \
         patch.object(ConfigurationHandler, "get_value_as_int", return_value=12) as mock_int, \
         patch.object(ConfigurationHandler, "ensure_loaded"):
        
        expires_at = token_helper.get_email_verification_expires_at()
        assert expires_at == fixed_now + timedelta(hours=12)
        mock_int.assert_called_with("Tokens", "email_verification_expire_hours", fallback=24)

def test_get_password_reset_expires_at():
    """Test specialized password reset expiration calculation."""
    fixed_now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    with patch.object(token_helper, "_now", return_value=fixed_now), \
         patch.object(ConfigurationHandler, "get_value_as_int", return_value=2) as mock_int, \
         patch.object(ConfigurationHandler, "ensure_loaded"):
        
        expires_at = token_helper.get_password_reset_expires_at()
        assert expires_at == fixed_now + timedelta(hours=2)
        mock_int.assert_called_with("Tokens", "password_reset_expire_hours", fallback=1)

def test_get_workspace_invite_expires_at():
    """Test specialized workspace invitation expiration calculation."""
    fixed_now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    with patch.object(token_helper, "_now", return_value=fixed_now), \
         patch.object(ConfigurationHandler, "get_value_as_int", return_value=30) as mock_int, \
         patch.object(ConfigurationHandler, "ensure_loaded"):
        
        expires_at = token_helper.get_workspace_invite_expires_at()
        assert expires_at == fixed_now + timedelta(days=30)
        mock_int.assert_called_with("Tokens", "workspace_invite_expire_days", fallback=7)
