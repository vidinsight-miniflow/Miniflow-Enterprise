import jwt
from typing import Dict, Any, Tuple, Optional
from datetime import datetime, timezone, timedelta


from ..handlers import EnvironmentHandler
from ..handlers import ConfigurationHandler
from miniflow.core.exceptions import TokenExpiredError, TokenInvalidError


# Cache variables for lazy loading
_jwt_secret_key: Optional[str] = None
_jwt_algorithm: Optional[str] = None

_access_token_type: Optional[str] = None
_refresh_token_type: Optional[str] = None


def _get_jwt_secret_key() -> str:
    global _jwt_secret_key
    
    if _jwt_secret_key is None:
        key = EnvironmentHandler.get("JWT_SECRET_KEY")

        if key:
            _jwt_secret_key = key if isinstance(key, str) else str(key)
        else:
            print("\n[ERROR] JWT_SECRET_KEY ayarlanmamış.")
            print("[ERROR] JWT token işlemleri için JWT_SECRET_KEY ortam değişkenini ayarlayın.")
            raise ValueError("JWT_SECRET_KEY environment variable is not set")
    
    return _jwt_secret_key


def _get_jwt_algorithm() -> str:
    global _jwt_algorithm
    
    if _jwt_algorithm is None:
        algorithm = EnvironmentHandler.get("JWT_ALGORITHM")

        if algorithm:
            _jwt_algorithm = algorithm if isinstance(algorithm, str) else str(algorithm)
        else:
            print("\n[WARNING] JWT_ALGORITHM ayarlanmamış. Varsayılan algoritma kullanılıyor: HS256")
            print("[WARNING] Production için JWT_ALGORITHM ortam değişkenini ayarlayın.")
            _jwt_algorithm = "HS256"
    
    return _jwt_algorithm


def _get_access_token_type() -> str:
    global _access_token_type
    
    if _access_token_type is None:
        token_type = ConfigurationHandler.get("JWT Settings", "access_token_type")

        if token_type:
            _access_token_type = token_type if isinstance(token_type, str) else str(token_type)
        else:
            print("\n[WARNING] access_token_type ayarlanmamış. Varsayılan değer kullanılıyor: access")
            print("[WARNING] Production için JWT Settings bölümünde access_token_type değerini ayarlayın.")
            _access_token_type = "access"
    
    return _access_token_type


def _get_refresh_token_type() -> str:
    global _refresh_token_type
    
    if _refresh_token_type is None:
        token_type = ConfigurationHandler.get("JWT Settings", "refresh_token_type")

        if token_type:
            _refresh_token_type = token_type if isinstance(token_type, str) else str(token_type)
        else:
            print("\n[WARNING] refresh_token_type ayarlanmamış. Varsayılan değer kullanılıyor: refresh")
            print("[WARNING] Production için JWT Settings bölümünde refresh_token_type değerini ayarlayın.")
            _refresh_token_type = "refresh"
    
    return _refresh_token_type


def create_access_token(user_id: str, access_token_jti: str, additional_claims: Optional[Dict[str, Any]] = None) -> Tuple[str, datetime]:
    now = datetime.now(timezone.utc)
    access_token_expire_minutes = ConfigurationHandler.get_int("JWT Settings", "jwt_access_token_expire_minutes")
    expire_delta = timedelta(minutes=access_token_expire_minutes)
    expires_at = now + expire_delta

    payload = {
        "user_id": user_id, 
        "jti": access_token_jti,
        "token_type": _get_access_token_type(),
        "exp": int(expires_at.timestamp()),
        "iat": int(now.timestamp()),           
        "nbf": int(now.timestamp())             
    }

    if additional_claims:
        payload.update(additional_claims)


    token = jwt.encode(payload, _get_jwt_secret_key(), _get_jwt_algorithm())
    return token, expires_at

def create_refresh_token(user_id: str, refresh_token_jti: str, additional_claims: Optional[Dict[str, Any]] = None) -> Tuple[str, datetime]:
    now = datetime.now(timezone.utc)
    refresh_token_expire_days = ConfigurationHandler.get_int("JWT Settings", "jwt_refresh_token_expire_days")
    expire_delta = timedelta(days=refresh_token_expire_days)
    expires_at = now + expire_delta

    payload = {
        "user_id": user_id, 
        "jti": refresh_token_jti,
        "token_type": _get_refresh_token_type(),
        "exp": int(expires_at.timestamp()),
        "iat": int(now.timestamp()),           
        "nbf": int(now.timestamp())             
    }

    if additional_claims:
        payload.update(additional_claims)

    token = jwt.encode(payload, _get_jwt_secret_key(), _get_jwt_algorithm())
    return token, expires_at

def validate_access_token(token: str) -> Tuple[bool, Any]:
    try:
        payload = jwt.decode(token, _get_jwt_secret_key(), algorithms=[_get_jwt_algorithm()])

        if payload.get("token_type") != _get_access_token_type():
             raise TokenInvalidError(token_type="access")
        
        return True, payload
    
    except jwt.ExpiredSignatureError:
        raise TokenExpiredError(token_type="access")
    except jwt.InvalidTokenError:
        raise TokenInvalidError(token_type="access")
    except Exception:
        raise TokenInvalidError(token_type="access")
    
def validate_refresh_token(token: str) -> Tuple[bool, Any]:
    try:
        payload = jwt.decode(token, _get_jwt_secret_key(), algorithms=[_get_jwt_algorithm()])

        if payload.get("token_type") != _get_refresh_token_type():
             raise TokenInvalidError(token_type="refresh")
        
        return True, payload
    
    except jwt.ExpiredSignatureError:
        raise TokenExpiredError(token_type="refresh")
    except jwt.InvalidTokenError:
        raise TokenInvalidError(token_type="refresh")
    except Exception:
        raise TokenInvalidError(token_type="refresh")
    
def get_token_remaining_time(token: str) -> Optional[int]:
    try:
        payload = jwt.decode(token, options={"verify_signature": False})

        if not payload or "exp" not in payload:
            return None
        
        exp = payload["exp"]
        now = datetime.now(timezone.utc)
        remaining = exp - int(now.timestamp())

        return remaining if remaining > 0 else 0
    
    except Exception:
        return None

def is_token_valid(token: str) -> bool:
    try:
        payload = jwt.decode(token, options={"verify_signature": False})

        if not payload or "exp" not in payload:
            return False
        
        exp = payload["exp"]
        now = datetime.now(timezone.utc)

        return (exp - int(now.timestamp())) > 0

    except Exception:
        return False
    
def decode_token_without_validation(token: str) -> Optional[Dict[str, Any]]:
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        return payload
    except Exception:
        return None