import pytest
import base64
import bcrypt
import hashlib
from cryptography.fernet import Fernet, InvalidToken
from unittest.mock import patch, MagicMock

from qbitra.utils.helpers import crypto_helper
from qbitra.utils.handlers.environment_handler import EnvironmentHandler
from qbitra.core.exceptions import (
    EncryptionError,
    EncryptionKeyError,
    PasswordHashingError,
    PasswordValidationError,
    DecryptionError,
    DataHashingError,
)

@pytest.fixture(autouse=True)
def reset_crypto_cache():
    """Reset the module-level cache variables in crypto_helper."""
    crypto_helper._encryption_key = None
    crypto_helper._cipher = None
    yield

def test_validate_encryption_key_hex():
    """Test validation of 64-character hex encryption key."""
    # 32 bytes = 256 bits = 64 hex characters
    valid_hex = "0" * 64
    validated = crypto_helper._validate_encryption_key(valid_hex)
    assert isinstance(validated, bytes)
    # Fernet key should be base64-encoded 32 bytes
    decoded = base64.urlsafe_b64decode(validated)
    assert len(decoded) == 32
    assert decoded == bytes.fromhex(valid_hex)

def test_validate_encryption_key_base64():
    """Test validation of standard Fernet base64 encryption key."""
    valid_b64 = Fernet.generate_key().decode()
    validated = crypto_helper._validate_encryption_key(valid_b64)
    assert validated == valid_b64.encode()

def test_validate_encryption_key_invalid_length():
    """Test validation failure for invalid key length."""
    invalid_hex = "0" * 32 # Only 16 bytes
    with pytest.raises(EncryptionKeyError) as exc:
        crypto_helper._validate_encryption_key(invalid_hex)
    assert "64 karakter hex string olmalı" in str(exc.value)

def test_get_encryption_key_from_env():
    """Test loading encryption key from environment."""
    key = Fernet.generate_key().decode()
    with patch.object(EnvironmentHandler, "get_value_as_str", return_value=key):
        loaded_key = crypto_helper._get_encryption_key()
        assert loaded_key == key.encode()

def test_get_encryption_key_fallback():
    """Test generating a temporary key when env is missing."""
    with patch.object(EnvironmentHandler, "get_value_as_str", return_value=None):
        loaded_key = crypto_helper._get_encryption_key()
        assert loaded_key is not None
        assert len(base64.urlsafe_b64decode(loaded_key)) == 32

def test_encrypt_decrypt_roundtrip():
    """Test data encryption and decryption with various characters."""
    # Special characters and emoji
    test_strings = [
        "Simple String",
        "Türkçe Karakterler: çşğüıö ÇŞĞÜİÖ",
        "DeepNest Emoji: 😀🚀🔥",
        "Special Symbols: !@#$%^&*()_+=-[]{};':\",./<>?|\\",
        "Long String: " + "A" * 1000,
        "" # Empty string
    ]
    
    # Ensure key is initialized
    crypto_helper._get_encryption_key()
    
    for text in test_strings:
        encrypted = crypto_helper.encrypt_data(text)
        if text == "":
            assert encrypted == ""
            continue
        
        assert encrypted != text
        decrypted = crypto_helper.decrypt_data(encrypted)
        assert decrypted == text

def test_decryption_error_invalid_token():
    """Test DecryptionError when token is tampered or wrong key used."""
    crypto_helper._get_encryption_key()
    encrypted = crypto_helper.encrypt_data("Secret")
    
    # Tamper with data
    tampered = encrypted[:-5] + "XXXXX"
    with pytest.raises(DecryptionError) as exc:
        crypto_helper.decrypt_data(tampered)
    assert exc.value.error_details["invalid_token"] is True

def test_decryption_with_wrong_key():
    """Test DecryptionError when using a different key."""
    key1 = Fernet.generate_key()
    key2 = Fernet.generate_key()
    
    data = "Confidential"
    cipher1 = Fernet(key1)
    encrypted = cipher1.encrypt(data.encode()).decode()
    
    # Setup helper with key2
    crypto_helper._encryption_key = key2
    crypto_helper._cipher = Fernet(key2)
    
    with pytest.raises(DecryptionError):
        crypto_helper.decrypt_data(encrypted)

def test_hash_password_success():
    """Test password hashing and verification."""
    password = "MySecurePassword123!@#"
    hashed = crypto_helper.hash_password(password)
    
    assert hashed != password
    assert crypto_helper.verify_password(password, hashed) is True
    assert crypto_helper.verify_password("WrongPassword", hashed) is False

def test_hash_password_invalid_rounds():
    """Test password hashing with invalid rounds (should fallback to 12)."""
    password = "test"
    with patch("bcrypt.gensalt", wraps=bcrypt.gensalt) as mock_salt:
        crypto_helper.hash_password(password, rounds=1) # Too low
        mock_salt.assert_called_with(rounds=12)
        
        crypto_helper.hash_password(password, rounds=40) # Too high
        mock_salt.assert_called_with(rounds=12)

def test_hash_password_empty():
    """Test error for empty password."""
    with pytest.raises(PasswordValidationError):
        crypto_helper.hash_password("")

def test_hash_data_sha256():
    """Test SHA-256 data hashing."""
    data = "QBitra Data"
    expected = hashlib.sha256(data.encode()).hexdigest()
    
    assert crypto_helper.hash_data(data) == expected
    assert crypto_helper.hash_data("") == ""

def test_hash_data_special_chars():
    """Test data hashing with special characters."""
    data = "çşğ 😀"
    hashed = crypto_helper.hash_data(data)
    assert len(hashed) == 64 # Hex length for SHA-256
    assert all(c in "0123456789abcdef" for c in hashed)

def test_get_encryption_key_auto_generation():
    """Test that a new key is generated if environment variable is missing."""
    with patch.object(EnvironmentHandler, "get_value_as_str", return_value=None):
        # Result should be a valid Fernet key
        loaded_key = crypto_helper._get_encryption_key()
        assert loaded_key is not None
        Fernet(loaded_key) # Should not raise

def test_verify_password_edge_cases():
    """Test password verification with invalid or empty inputs."""
    # Hashed version of 'password'
    hashed = bcrypt.hashpw(b"password", bcrypt.gensalt()).decode()
    
    assert crypto_helper.verify_password(None, hashed) is False
    assert crypto_helper.verify_password("", hashed) is False
    assert crypto_helper.verify_password("password", None) is False
    assert crypto_helper.verify_password("password", "") is False
    assert crypto_helper.verify_password("password", "completely_garbage_hash") is False

def test_validate_encryption_key_non_hex_64_chars():
    """Test validation with a 64-character string that is not hex."""
    invalid_hex = "Z" * 64 # 64 chars, but 'Z' is not hex
    # This should fall back to base64 and fail Fernet validation if not valid base64
    with pytest.raises(EncryptionKeyError) as exc:
        crypto_helper._validate_encryption_key(invalid_hex)
    assert "validation başarısız" in str(exc.value)

def test_encrypt_decrypt_large_data():
    """Test encryption and decryption of larger payloads."""
    large_data = "QBitra rocks! " * 10000 # ~140KB
    crypto_helper._get_encryption_key()
    
    encrypted = crypto_helper.encrypt_data(large_data)
    decrypted = crypto_helper.decrypt_data(encrypted)
    assert decrypted == large_data
