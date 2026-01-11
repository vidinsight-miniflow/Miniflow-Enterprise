import base64
import bcrypt
import hashlib
from typing import Optional
from cryptography.fernet import Fernet, InvalidToken

from qbitra.core.qbitra_logger import get_logger
from qbitra.core.exceptions import (
    EncryptionError,
    EncryptionKeyError,
    PasswordHashingError,
    PasswordValidationError,
    DecryptionError,
    DataHashingError,
)
from qbitra.utils.handlers.environment_handler import EnvironmentHandler

# Cache variables for lazy loading
_encryption_key: Optional[bytes] = None
_cipher: Optional[Fernet] = None
_logger = get_logger("utils")


def _validate_encryption_key(key: str):
    try:
        _logger.debug(
            "Encryption key validation başlatılıyor",
            extra={"key_length": len(key) if key else 0}
        )
        
        if isinstance(key, str) and len(key) == 64:
            # Hex string format (64 characters = 32 bytes)
            try:
                key_bytes = bytes.fromhex(key)
                if len(key_bytes) == 32:
                    # Convert hex to base64 (Fernet format)
                    validated_key = base64.urlsafe_b64encode(key_bytes)
                    _logger.debug(
                        "Encryption key hex formatından başarıyla dönüştürüldü",
                        extra={"key_length": len(key), "format": "hex"}
                    )
                    return validated_key
                else:
                    _logger.error(
                        "Encryption key hex string yanlış uzunlukta",
                        extra={
                            "key_length": len(key),
                            "decoded_bytes": len(key_bytes),
                            "expected_bytes": 32
                        }
                    )
                    raise EncryptionKeyError(
                        key_format="hex",
                        key_length=len(key),
                        message=(
                            f"ENCRYPTION_KEY hex string must decode to 32 bytes, "
                            f"got {len(key_bytes)} bytes. "
                            "64 karakter hex string bekleniyor."
                        ),
                        error_details={
                            "key_length": len(key),
                            "decoded_bytes": len(key_bytes),
                            "expected_bytes": 32,
                            "format": "hex"
                        }
                    )
            except ValueError as e:
                _logger.warning(
                    "Encryption key hex formatında değil, base64 olarak deneniyor",
                    extra={"error": str(e), "key_length": len(key)}
                )
                # Not hex, try as base64
                validated_key = key.encode('utf-8') if isinstance(key, str) else key
        else:
            # Base64 encoded key format
            validated_key = key.encode('utf-8') if isinstance(key, str) else key
            _logger.debug(
                "Encryption key base64 formatında kabul edildi",
                extra={"key_length": len(key) if isinstance(key, str) else 0, "format": "base64"}
            )
        
        # Validate Fernet key format
        Fernet(validated_key)
        _logger.debug("Encryption key Fernet formatında doğrulandı")
        return validated_key
        
    except EncryptionKeyError:
        raise
    except Exception as e:
        _logger.error(
            "Encryption key validation başarısız",
            extra={
                "key_length": len(key) if key else 0,
                "error": str(e),
                "error_type": type(e).__name__
            },
            exc_info=True
        )
        raise EncryptionKeyError(
            key_format="unknown",
            key_length=len(key) if key else 0,
            message=(
                f"ENCRYPTION_KEY validation başarısız: {str(e)}. "
                "ENCRYPTION_KEY base64 encoded 32-byte key olmalı veya 64 karakter hex string olmalı."
            ),
            error_details={
                "key_length": len(key) if key else 0,
                "expected_formats": ["base64_encoded_32_byte_key", "64_character_hex_string"]
            },
            cause=e
        ) from e


def _get_encryption_key() -> bytes:
    global _encryption_key
    
    if _encryption_key is None:
        _logger.debug("Encryption key cache'de yok, environment'dan okunuyor")
        
        try:
            key = EnvironmentHandler.get_value_as_str("ENCRYPTION_KEY", default=None)
        except Exception as e:
            _logger.warning(
                "ENCRYPTION_KEY environment variable okunamadı, geçici anahtar üretilecek",
                extra={"error": str(e), "error_type": type(e).__name__},
                exc_info=True
            )
            key = None

        if key:
            _logger.info(
                "ENCRYPTION_KEY bulundu, validation yapılıyor",
                extra={"key_length": len(key)}
            )
            try:
                _encryption_key = _validate_encryption_key(key)
                # Final validation with Fernet
                Fernet(_encryption_key)
                _logger.info(
                    "ENCRYPTION_KEY başarıyla yüklendi ve doğrulandı",
                    extra={"key_length": len(key)}
                )
            except EncryptionKeyError:
                raise
            except Exception as e:
                _logger.error(
                    "ENCRYPTION_KEY Fernet validation başarısız",
                    extra={"error": str(e), "error_type": type(e).__name__},
                    exc_info=True
                )
                raise EncryptionKeyError(
                    key_format="fernet_validation",
                    key_length=len(key),
                    message=f"ENCRYPTION_KEY Fernet validation başarısız: {str(e)}",
                    error_details={"key_length": len(key)},
                    cause=e
                ) from e
        else:
            _logger.warning(
                "ENCRYPTION_KEY ayarlanmamış, geçici anahtar üretiliyor",
                extra={"warning": "Production için ENCRYPTION_KEY ortam değişkenini ayarlayın"}
            )
            new_key = Fernet.generate_key()
            _logger.warning(
                "Geçici encryption key üretildi",
                extra={"key_preview": new_key.decode()[:20] + "..."}
            )
            _encryption_key = new_key
    
    return _encryption_key


def _get_cipher() -> Fernet:
    global _cipher
    
    if _cipher is None:
        _logger.debug("Fernet cipher instance oluşturuluyor")
        _cipher = Fernet(_get_encryption_key())
        _logger.debug("Fernet cipher instance başarıyla oluşturuldu")
    
    return _cipher


def encrypt_data(plain_text: str) -> str:
    if not plain_text:
        _logger.debug("Boş plain_text şifreleniyor, boş string döndürülüyor")
        return ""
    
    try:
        _logger.debug(
            "Veri şifreleniyor",
            extra={"data_length": len(plain_text)}
        )
        encrypted_bytes = _get_cipher().encrypt(plain_text.encode('utf-8'))
        encrypted_text = encrypted_bytes.decode('utf-8')
        _logger.debug(
            "Veri başarıyla şifrelendi",
            extra={
                "data_length": len(plain_text),
                "encrypted_length": len(encrypted_text)
            }
        )
        return encrypted_text
    except Exception as e:
        _logger.error(
            "Veri şifreleme hatası",
            extra={
                "data_length": len(plain_text),
                "error": str(e),
                "error_type": type(e).__name__
            },
            exc_info=True
        )
        raise EncryptionError(
            operation="encryption",
            message=f"Veri şifreleme başarısız: {str(e)}",
            error_details={"data_length": len(plain_text)},
            cause=e
        ) from e

    
def decrypt_data(encrypted_text: str) -> str:
    if not encrypted_text:
        _logger.debug("Boş encrypted_text deşifreleniyor, boş string döndürülüyor")
        return ""
    
    try:
        _logger.debug(
            "Veri deşifreleniyor",
            extra={"encrypted_length": len(encrypted_text)}
        )
        decrypted_bytes = _get_cipher().decrypt(encrypted_text.encode('utf-8'))
        decrypted_text = decrypted_bytes.decode('utf-8')
        _logger.debug(
            "Veri başarıyla deşifrelendi",
            extra={
                "encrypted_length": len(encrypted_text),
                "decrypted_length": len(decrypted_text)
            }
        )
        return decrypted_text
    except InvalidToken as e:
        _logger.error(
            "Veri deşifreleme hatası: Geçersiz token (yanlış key veya bozuk veri)",
            extra={
                "encrypted_length": len(encrypted_text),
                "error": str(e),
                "error_type": "InvalidToken"
            },
            exc_info=True
        )
        raise DecryptionError(
            invalid_token=True,
            message=(
                "Veri deşifreleme başarısız: Geçersiz token. "
                "Bu genellikle yanlış encryption key veya bozuk veri anlamına gelir."
            ),
            error_details={
                "encrypted_length": len(encrypted_text),
                "error_type": "InvalidToken"
            },
            cause=e
        ) from e
    except Exception as e:
        _logger.error(
            "Veri deşifreleme hatası",
            extra={
                "encrypted_length": len(encrypted_text),
                "error": str(e),
                "error_type": type(e).__name__
            },
            exc_info=True
        )
        raise DecryptionError(
            invalid_token=False,
            message=f"Veri deşifreleme başarısız: {str(e)}",
            error_details={"encrypted_length": len(encrypted_text)},
            cause=e
        ) from e

    
def hash_password(password: str, rounds: int = 12) -> str:
    if not password:
        _logger.error("Password hash işlemi için boş password verildi")
        raise PasswordValidationError(
            field_name="password",
            message="Password hash işlemi için password gerekli"
        )
    
    if rounds < 4 or rounds > 31:
        _logger.warning(
            "Geçersiz bcrypt rounds değeri, varsayılan değer kullanılıyor",
            extra={"provided_rounds": rounds, "default_rounds": 12}
        )
        rounds = 12
    
    try:
        _logger.debug(
            "Password hash işlemi başlatılıyor",
            extra={"rounds": rounds, "password_length": len(password)}
        )
        salt = bcrypt.gensalt(rounds=rounds)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        hashed_str = hashed.decode('utf-8')
        _logger.debug(
            "Password başarıyla hash'lendi",
            extra={"rounds": rounds, "hash_length": len(hashed_str)}
        )
        return hashed_str
    except Exception as e:
        _logger.error(
            "Password hash işlemi başarısız",
            extra={
                "rounds": rounds,
                "password_length": len(password),
                "error": str(e),
                "error_type": type(e).__name__
            },
            exc_info=True
        )
        raise PasswordHashingError(
            rounds=rounds,
            message=f"Password hash işlemi başarısız: {str(e)}",
            error_details={"rounds": rounds},
            cause=e
        ) from e

    
def verify_password(password: str, hashed_password: str) -> bool:
    if not password or not hashed_password:
        _logger.debug(
            "Password doğrulama için eksik parametre",
            extra={
                "has_password": bool(password),
                "has_hashed_password": bool(hashed_password)
            }
        )
        return False
    try:
        _logger.debug("Password doğrulama işlemi başlatılıyor")
        is_valid = bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
        _logger.debug(
            "Password doğrulama tamamlandı",
            extra={"is_valid": is_valid}
        )
        return is_valid
    except Exception as e:
        _logger.warning(
            "Password doğrulama hatası",
            extra={
                "error": str(e),
                "error_type": type(e).__name__
            },
            exc_info=True
        )
        return False


def hash_data(data: str) -> str:
    if not data:
        _logger.debug("Boş data hash'leniyor, boş string döndürülüyor")
        return ""
    
    try:
        _logger.debug(
            "Data hash işlemi başlatılıyor",
            extra={"data_length": len(data)}
        )
        hash_value = hashlib.sha256(data.encode('utf-8')).hexdigest()
        _logger.debug(
            "Data başarıyla hash'lendi",
            extra={
                "data_length": len(data),
                "hash_length": len(hash_value)
            }
        )
        return hash_value
    except Exception as e:
        _logger.error(
            "Data hash işlemi başarısız",
            extra={
                "data_length": len(data),
                "error": str(e),
                "error_type": type(e).__name__
            },
            exc_info=True
        )
        raise DataHashingError(
            hash_algorithm="SHA-256",
            message=f"Data hash işlemi başarısız: {str(e)}",
            error_details={"data_length": len(data)},
            cause=e
        ) from e
