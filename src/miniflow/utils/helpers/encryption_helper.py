import bcrypt
import hashlib
import base64
from typing import Optional
from cryptography.fernet import Fernet

from ..handlers import EnvironmentHandler
from miniflow.core.exceptions import InvalidInputError, InternalError


# Cache variables for lazy loading
_encryption_key: Optional[bytes] = None
_cipher: Optional[Fernet] = None


def _get_encryption_key() -> bytes:
    global _encryption_key
    
    if _encryption_key is None:
        key = EnvironmentHandler.get("ENCRYPTION_KEY")

        if key:
            try:
                # Eğer hex string ise (64 karakter hex), bytes'a çevir ve base64 encode et
                if isinstance(key, str) and len(key) == 64:
                    try:
                        # Hex string kontrolü
                        key_bytes = bytes.fromhex(key)
                        if len(key_bytes) == 32:
                            # Base64 encode et (Fernet key formatı)
                            _encryption_key = base64.urlsafe_b64encode(key_bytes)
                        else:
                            raise ValueError("ENCRYPTION_KEY hex string must decode to 32 bytes")
                    except ValueError:
                        # Hex değilse, base64 encoded key olarak kabul et
                        _encryption_key = key.encode() if isinstance(key, str) else key
                else:
                    # Base64 encoded key olarak kabul et
                    _encryption_key = key.encode() if isinstance(key, str) else key
                
                # Fernet key formatını doğrula
                Fernet(_encryption_key)
            except Exception as e:
                print(f"\n[ERROR] ENCRYPTION_KEY formatı geçersiz: {str(e)}")
                print("[ERROR] ENCRYPTION_KEY base64 encoded 32-byte key olmalı veya 64 karakter hex string olmalı.")
                raise InternalError(
                    component_name="encryption_helper",
                    message=f"Invalid ENCRYPTION_KEY format: {str(e)}"
                )
        else:
            print("\n[WARNING] ENCRYPTION_KEY ayarlanmamış. Geçici anahtar üretiliyor.")
            print("[WARNING] Production için ENCRYPTION_KEY ortam değişkenini ayarlayın.")
            new_key = Fernet.generate_key()
            print(f"[WARNING] Oluşturulan yeni encryption key {new_key.decode()}")
            _encryption_key = new_key
    
    return _encryption_key


def _get_cipher() -> Fernet:
    global _cipher
    
    if _cipher is None:
        _cipher = Fernet(_get_encryption_key())
    
    return _cipher


def encrypt_data(plain_text: str) -> str:
    if not plain_text:
        return ""
    
    try:
        encrypted_bytes = _get_cipher().encrypt(plain_text.encode('utf-8'))
        return encrypted_bytes.decode('utf-8')
    except Exception as e:
        raise InternalError(
            component_name="encryption_helper",
            message=f"Encryption failed: {str(e)}"
        )
    
def decrypt_data(encrypted_text: str) -> str:
    if not encrypted_text:
        return ""
    
    try:
        decrypted_bytes = _get_cipher().decrypt(encrypted_text.encode('utf-8'))
        return decrypted_bytes.decode('utf-8')
    except Exception as e:
        raise InternalError(
            component_name="encryption_helper",
            message=f"Decryption failed: {str(e)}"
        )
    
def hash_password(password: str, rounds: int = 12) -> str:
    if not password:
        raise InvalidInputError(field_name="password")
    
    try:
        salt = bcrypt.gensalt(rounds=rounds)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    except Exception:
        raise InternalError(component_name="encryption_helper")
    
def verify_password(password: str, hashed_password: str) -> bool:
    if not password or not hashed_password:
        return False
    
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def hash_data(data: str) -> str:
    if not data:
        return ""
    
    try:
        return hashlib.sha256(data.encode('utf-8')).hexdigest()
    except Exception:
        raise InternalError(component_name="encryption_helper")