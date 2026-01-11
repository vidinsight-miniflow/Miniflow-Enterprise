import jwt
from typing import Dict, Any, Tuple, Optional
from datetime import datetime, timezone, timedelta

from qbitra.core.qbitra_logger import get_logger
from qbitra.core.exceptions import (
    JWTConfigurationError,
    JWTExpiredError,
    JWTInvalidTokenError,
    JWTMissingClaimError,
    JWTTokenTypeError,
    JWTRevokedError,
)
from qbitra.utils.handlers.environment_handler import EnvironmentHandler
from qbitra.utils.handlers.configuration_handler import ConfigurationHandler


# Cache variables for lazy loading
_jwt_secret_key: Optional[str] = None
_jwt_algorithm: Optional[str] = None

_access_token_expire_minutes: Optional[timedelta] = None
_refresh_token_expire_days: Optional[timedelta] = None

_logger = get_logger("jwt_helper")


def _get_jwt_secret_key() -> str:
    global _jwt_secret_key
    
    if _jwt_secret_key is None:
        _logger.debug("JWT secret key cache'de yok, environment'dan okunuyor")
        try:
            key = EnvironmentHandler.get_value_as_str("JWT_SECRET_KEY", default=None)
        except Exception as e:
            _logger.error(
                "JWT_SECRET_KEY environment variable okunamadı",
                extra={"error": str(e), "error_type": type(e).__name__},
                exc_info=True
            )
            raise JWTConfigurationError(
                config_key="JWT_SECRET_KEY",
                message="JWT_SECRET_KEY environment variable is required but not set",
                cause=e
            ) from e
        
        if key:
            _jwt_secret_key = key
            _logger.debug("JWT secret key başarıyla yüklendi")
        else:
            _logger.error("JWT_SECRET_KEY environment variable tanımlı değil")
            raise JWTConfigurationError(
                config_key="JWT_SECRET_KEY",
                message="JWT_SECRET_KEY environment variable is required but not set"
            )
    
    return _jwt_secret_key


def _get_jwt_algorithm() -> str:
    global _jwt_algorithm
    
    if _jwt_algorithm is None:
        _logger.debug("JWT algorithm cache'de yok, configuration'dan okunuyor")
        try:
            algorithm = ConfigurationHandler.get_value_as_str("JWT Settings", "algorithm", fallback="HS256")
        except Exception as e:
            _logger.warning(
                "JWT algorithm configuration'dan okunamadı, varsayılan kullanılıyor",
                extra={"error": str(e), "default_algorithm": "HS256"},
                exc_info=True
            )
            algorithm = "HS256"
        
        if algorithm:
            _jwt_algorithm = algorithm
            _logger.debug(f"JWT algorithm yüklendi: {algorithm}")
        else:
            _logger.warning("JWT algorithm configuration'da bulunamadı, varsayılan kullanılıyor: HS256")
            _jwt_algorithm = "HS256"
    
    return _jwt_algorithm


def _get_access_token_expire_minutes() -> timedelta:
    global _access_token_expire_minutes
    
    if _access_token_expire_minutes is None:
        _logger.debug("Access token expire minutes cache'de yok, configuration'dan okunuyor")
        try:
            minutes = ConfigurationHandler.get_value_as_int("JWT Settings", "jwt_access_token_expire_minutes", fallback=60)
        except Exception as e:
            _logger.warning(
                "Access token expire minutes configuration'dan okunamadı, varsayılan kullanılıyor",
                extra={"error": str(e), "default_minutes": 60},
                exc_info=True
            )
            minutes = 60
        
        if minutes and minutes > 0:
            _access_token_expire_minutes = timedelta(minutes=minutes)
            _logger.debug(f"Access token expire minutes yüklendi: {minutes} dakika")
        else:
            _logger.warning("Access token expire minutes geçersiz, varsayılan kullanılıyor: 60 dakika")
            _access_token_expire_minutes = timedelta(minutes=60)
    
    return _access_token_expire_minutes


def _get_refresh_token_expire_days() -> timedelta:
    global _refresh_token_expire_days
    
    if _refresh_token_expire_days is None:
        _logger.debug("Refresh token expire days cache'de yok, configuration'dan okunuyor")
        try:
            days = ConfigurationHandler.get_value_as_int("JWT Settings", "jwt_refresh_token_expire_days", fallback=7)
        except Exception as e:
            _logger.warning(
                "Refresh token expire days configuration'dan okunamadı, varsayılan kullanılıyor",
                extra={"error": str(e), "default_days": 7},
                exc_info=True
            )
            days = 7
        
        if days and days > 0:
            _refresh_token_expire_days = timedelta(days=days)
            _logger.debug(f"Refresh token expire days yüklendi: {days} gün")
        else:
            _logger.warning("Refresh token expire days geçersiz, varsayılan kullanılıyor: 7 gün")
            _refresh_token_expire_days = timedelta(days=7)
    
    return _refresh_token_expire_days


def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_access_token(user_id: str, access_token_jti: str, additional_claims: Optional[Dict[str, Any]] = None) -> Tuple[str, datetime]:
    _logger.debug(
        "Access token oluşturuluyor",
        extra={"user_id": user_id, "access_token_jti": access_token_jti}
    )
    
    expires_at = _now() + _get_access_token_expire_minutes()
    _logger.debug(
        "Access token expire at hesaplandı",
        extra={"expires_at": expires_at.isoformat(), "user_id": user_id}
    )

    payload = {
        "user_id": user_id, 
        "jti": access_token_jti,
        "token_type": "access",
        "exp": int(expires_at.timestamp()),
        "iat": int(_now().timestamp()),           
        "nbf": int(_now().timestamp())             
    }

    if additional_claims:
        payload.update(additional_claims)
        _logger.debug(
            "Additional claims eklendi",
            extra={"additional_claims_count": len(additional_claims)}
        )

    try:
        token = jwt.encode(payload, _get_jwt_secret_key(), _get_jwt_algorithm())
        _logger.info(
            "Access token başarıyla oluşturuldu",
            extra={"user_id": user_id, "jti": access_token_jti, "expires_at": expires_at.isoformat()}
        )
        return token, expires_at
    except Exception as e:
        _logger.error(
            "Access token oluşturma hatası",
            extra={
                "user_id": user_id,
                "jti": access_token_jti,
                "error": str(e),
                "error_type": type(e).__name__
            },
            exc_info=True
        )
        raise JWTInvalidTokenError(
            token_type="access",
            reason="token_creation_failed",
            message=f"Access token oluşturma başarısız: {str(e)}",
            error_details={"user_id": user_id, "jti": access_token_jti},
            cause=e
        ) from e


def create_refresh_token(user_id: str, refresh_token_jti: str, additional_claims: Optional[Dict[str, Any]] = None) -> Tuple[str, datetime]:
    _logger.debug(
        "Refresh token oluşturuluyor",
        extra={"user_id": user_id, "refresh_token_jti": refresh_token_jti}
    )
    
    expires_at = _now() + _get_refresh_token_expire_days()
    _logger.debug(
        "Refresh token expire at hesaplandı",
        extra={"expires_at": expires_at.isoformat(), "user_id": user_id}
    )

    payload = {
        "user_id": user_id, 
        "jti": refresh_token_jti,
        "token_type": "refresh",
        "exp": int(expires_at.timestamp()),
        "iat": int(_now().timestamp()),           
        "nbf": int(_now().timestamp()) 
    }

    if additional_claims:
        payload.update(additional_claims)
        _logger.debug(
            "Additional claims eklendi",
            extra={"additional_claims_count": len(additional_claims)}
        )

    try:
        token = jwt.encode(payload, _get_jwt_secret_key(), _get_jwt_algorithm())
        _logger.info(
            "Refresh token başarıyla oluşturuldu",
            extra={"user_id": user_id, "jti": refresh_token_jti, "expires_at": expires_at.isoformat()}
        )
        return token, expires_at
    except Exception as e:
        _logger.error(
            "Refresh token oluşturma hatası",
            extra={
                "user_id": user_id,
                "jti": refresh_token_jti,
                "error": str(e),
                "error_type": type(e).__name__
            },
            exc_info=True
        )
        raise JWTInvalidTokenError(
            token_type="refresh",
            reason="token_creation_failed",
            message=f"Refresh token oluşturma başarısız: {str(e)}",
            error_details={"user_id": user_id, "jti": refresh_token_jti},
            cause=e
        ) from e


def _validate_token(token: str, expected_token_type: str) -> Tuple[bool, Any]:
    try:
        _logger.debug(
            f"{expected_token_type.capitalize()} token doğrulanıyor",
            extra={"expected_token_type": expected_token_type}
        )
        
        decoded_payload = jwt.decode(
            token,
            _get_jwt_secret_key(),
            algorithms=[_get_jwt_algorithm()],
            options={
                "require": ["user_id", "jti", "token_type", "exp", "iat", "nbf"]
            }
        )
        
        actual_token_type = decoded_payload.get("token_type")
        if actual_token_type != expected_token_type:
            _logger.warning(
                "Token type uyuşmazlığı",
                extra={
                    "expected_type": expected_token_type,
                    "actual_type": actual_token_type,
                    "user_id": decoded_payload.get("user_id"),
                    "jti": decoded_payload.get("jti")
                }
            )
            raise JWTTokenTypeError(
                expected_type=expected_token_type,
                actual_type=actual_token_type,
                message=(
                    f"Token type mismatch. Expected '{expected_token_type}', got '{actual_token_type}'. "
                    "Please use the correct token type."
                ),
                error_details={
                    "expected_type": expected_token_type,
                    "actual_type": actual_token_type,
                    "user_id": decoded_payload.get("user_id"),
                    "jti": decoded_payload.get("jti")
                }
            )
        
        jti = decoded_payload.get("jti")
        user_id = decoded_payload.get("user_id")
        
        _logger.debug(
            f"{expected_token_type.capitalize()} token başarıyla doğrulandı",
            extra={"user_id": user_id, "jti": jti, "token_type": actual_token_type}
        )
        return True, decoded_payload

    except JWTTokenTypeError:
        raise
    except JWTConfigurationError:
        raise
    except jwt.ExpiredSignatureError as e:
        _logger.debug(
            "Token expired",
            extra={"expected_token_type": expected_token_type}
        )
        raise JWTExpiredError(
            token_type=expected_token_type,
            message=f"{expected_token_type.capitalize()} token has expired",
            cause=e
        ) from e
        
    except jwt.InvalidIssuerError as e:
        _logger.warning(
            "Invalid token issuer",
            extra={"expected_token_type": expected_token_type, "error": str(e)}
        )
        raise JWTInvalidTokenError(
            token_type=expected_token_type,
            reason="invalid_issuer",
            message="JWT token has invalid issuer",
            cause=e
        ) from e
        
    except jwt.InvalidAudienceError as e:
        _logger.warning(
            "Invalid token audience",
            extra={"expected_token_type": expected_token_type, "error": str(e)}
        )
        raise JWTInvalidTokenError(
            token_type=expected_token_type,
            reason="invalid_audience",
            message="JWT token has invalid audience",
            cause=e
        ) from e
        
    except jwt.MissingRequiredClaimError as e:
        _logger.warning(
            "Missing required claim",
            extra={"expected_token_type": expected_token_type, "missing_claim": e.claim}
        )
        raise JWTMissingClaimError(
            claim=e.claim,
            message=f"JWT token is missing required claim: {e.claim}",
            cause=e
        ) from e
        
    except jwt.InvalidTokenError as e:
        _logger.warning(
            "Invalid token",
            extra={"expected_token_type": expected_token_type, "error": str(e)}
        )
        raise JWTInvalidTokenError(
            token_type=expected_token_type,
            reason="invalid_token",
            message=f"JWT token is invalid: {str(e)}",
            cause=e
        ) from e
        
    except Exception as e:
        _logger.error(
            "Token validation sırasında beklenmeyen hata",
            extra={
                "expected_token_type": expected_token_type,
                "error": str(e),
                "error_type": type(e).__name__
            },
            exc_info=True
        )
        raise JWTInvalidTokenError(
            token_type=expected_token_type,
            reason="unexpected_error",
            message=f"Unexpected error during token validation: {str(e)}",
            cause=e
        ) from e


def validate_access_token(token: str) -> Tuple[bool, Any]:
    _logger.debug("Access token doğrulanıyor")
    try:
        return _validate_token(token, "access")
    except (JWTExpiredError, JWTInvalidTokenError, JWTMissingClaimError, JWTTokenTypeError) as e:
        _logger.debug(
            "Access token doğrulama başarısız",
            extra={"error": str(e), "error_type": type(e).__name__}
        )
        return False, e
    except Exception as e:
        _logger.error(
            "Access token doğrulama sırasında beklenmeyen hata",
            extra={"error": str(e), "error_type": type(e).__name__},
            exc_info=True
        )
        return False, JWTInvalidTokenError(
            token_type="access",
            reason="unexpected_error",
            message=f"Unexpected error during access token validation: {str(e)}",
            cause=e
        )


def validate_refresh_token(token: str) -> Tuple[bool, Any]:
    _logger.debug("Refresh token doğrulanıyor")
    try:
        return _validate_token(token, "refresh")
    except (JWTExpiredError, JWTInvalidTokenError, JWTMissingClaimError, JWTTokenTypeError) as e:
        _logger.debug(
            "Refresh token doğrulama başarısız",
            extra={"error": str(e), "error_type": type(e).__name__}
        )
        return False, e
    except Exception as e:
        _logger.error(
            "Refresh token doğrulama sırasında beklenmeyen hata",
            extra={"error": str(e), "error_type": type(e).__name__},
            exc_info=True
        )
        return False, JWTInvalidTokenError(
            token_type="refresh",
            reason="unexpected_error",
            message=f"Unexpected error during refresh token validation: {str(e)}",
            cause=e
        )


def get_token_remaining_time(token: str) -> Optional[int]:
    try:
        _logger.debug("Token kalan süre hesaplanıyor")
        
        payload = jwt.decode(
            token,
            options={
                "verify_signature": False,
                "verify_exp": False
            }
        )
        
        exp = payload.get("exp")
        if exp is None:
            _logger.debug("Token'da expiration claim yok")
            return None
            
        remaining = exp - int(_now().timestamp())
        
        if remaining < 0:
            _logger.debug(
                "Token zaten expire olmuş",
                extra={"expired_seconds_ago": abs(remaining)}
            )
            return 0
        
        _logger.debug(
            "Token kalan süre hesaplandı",
            extra={"remaining_seconds": remaining}
        )
        return remaining
        
    except jwt.InvalidTokenError as e:
        _logger.debug(
            "Token kalan süre hesaplanamadı: geçersiz token",
            extra={"error": str(e)}
        )
        return None
    except Exception as e:
        _logger.warning(
            "Token kalan süre hesaplanırken hata oluştu",
            extra={"error": str(e), "error_type": type(e).__name__},
            exc_info=True
        )
        return None


def decode_token_unverified(token: str) -> Optional[Dict[str, Any]]:
    try:
        _logger.debug("Token doğrulama olmadan decode ediliyor")
        
        payload = jwt.decode(
            token,
            options={
                "verify_signature": False,
                "verify_exp": False,
                "verify_aud": False,
                "verify_iss": False
            }
        )
        
        _logger.debug(
            "Token başarıyla decode edildi (doğrulama olmadan)",
            extra={"user_id": payload.get("user_id"), "jti": payload.get("jti")}
        )
        return payload
    except jwt.InvalidTokenError as e:
        _logger.debug(
            "Token decode edilemedi: geçersiz token",
            extra={"error": str(e)}
        )
        return None
    except Exception as e:
        _logger.warning(
            "Token decode edilirken hata oluştu",
            extra={"error": str(e), "error_type": type(e).__name__},
            exc_info=True
        )
        return None


def get_token_jti(token: str) -> Optional[str]:
    _logger.debug("Token JTI alınıyor")
    payload = decode_token_unverified(token)
    if payload:
        jti = payload.get("jti")
        _logger.debug("Token JTI alındı", extra={"jti": jti})
        return jti
    _logger.debug("Token JTI alınamadı: token decode edilemedi")
    return None


def get_token_user_id(token: str) -> Optional[str]:
    _logger.debug("Token user_id alınıyor")
    payload = decode_token_unverified(token)
    if payload:
        user_id = payload.get("user_id")
        _logger.debug("Token user_id alındı", extra={"user_id": user_id})
        return user_id
    _logger.debug("Token user_id alınamadı: token decode edilemedi")
    return None
