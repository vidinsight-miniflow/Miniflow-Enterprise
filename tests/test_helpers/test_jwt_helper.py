import pytest
import jwt
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

from qbitra.utils.helpers import jwt_helper
from qbitra.utils.handlers import EnvironmentHandler, ConfigurationHandler
from qbitra.core.exceptions import (
    JWTConfigurationError,
    JWTExpiredError,
    JWTInvalidTokenError,
    JWTMissingClaimError,
    JWTTokenTypeError,
)

@pytest.fixture(autouse=True)
def reset_jwt_cache():
    """Reset the module-level cache variables in jwt_helper."""
    jwt_helper._jwt_secret_key = None
    jwt_helper._jwt_algorithm = None
    jwt_helper._access_token_expire_minutes = None
    jwt_helper._refresh_token_expire_days = None
    yield

@pytest.fixture
def jwt_settings():
    """Default JWT settings for tests."""
    return {
        "secret": "test_secret_key_1234567890",
        "algorithm": "HS256",
        "access_expire": 60,
        "refresh_expire": 7
    }

def test_config_loading_success(jwt_settings):
    """Test successful loading of JWT configuration."""
    with patch.object(EnvironmentHandler, "get_value_as_str", return_value=jwt_settings["secret"]), \
         patch.object(ConfigurationHandler, "get_value_as_str", return_value=jwt_settings["algorithm"]), \
         patch.object(ConfigurationHandler, "get_value_as_int", side_effect=[jwt_settings["access_expire"], jwt_settings["refresh_expire"]]):
        
        assert jwt_helper._get_jwt_secret_key() == jwt_settings["secret"]
        assert jwt_helper._get_jwt_algorithm() == jwt_settings["algorithm"]
        assert jwt_helper._get_access_token_expire_minutes() == timedelta(minutes=jwt_settings["access_expire"])
        assert jwt_helper._get_refresh_token_expire_days() == timedelta(days=jwt_settings["refresh_expire"])

def test_config_loading_missing_secret():
    """Test error when JWT_SECRET_KEY is missing."""
    with patch.object(EnvironmentHandler, "get_value_as_str", return_value=None):
        with pytest.raises(JWTConfigurationError) as exc:
            jwt_helper._get_jwt_secret_key()
        assert "JWT_SECRET_KEY" in str(exc.value)

def test_create_access_token(jwt_settings):
    """Test creating an access token and verifying its payload."""
    user_id = "user_123"
    jti = "jti_abc"
    claims = {"role": "admin"}
    fixed_now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    
    with patch.object(EnvironmentHandler, "get_value_as_str", return_value=jwt_settings["secret"]), \
         patch.object(jwt_helper, "_now", return_value=fixed_now):
        
        token, expires_at = jwt_helper.create_access_token(user_id, jti, claims)
        
        assert isinstance(token, str)
        assert expires_at == fixed_now + timedelta(minutes=60)
        
        # Decode and verify (disable expiration check because jwt.decode uses real time)
        payload = jwt.decode(
            token, 
            jwt_settings["secret"], 
            algorithms=[jwt_settings["algorithm"]],
            options={"verify_exp": False}
        )
        assert payload["user_id"] == user_id
        assert payload["jti"] == jti
        assert payload["token_type"] == "access"
        assert payload["role"] == "admin"
        assert payload["exp"] == int(expires_at.timestamp())
        assert payload["iat"] == int(fixed_now.timestamp())

def test_create_refresh_token(jwt_settings):
    """Test creating a refresh token."""
    user_id = "user_123"
    jti = "jti_refresh"
    fixed_now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    
    with patch.object(EnvironmentHandler, "get_value_as_str", return_value=jwt_settings["secret"]), \
         patch.object(jwt_helper, "_now", return_value=fixed_now):
        
        token, expires_at = jwt_helper.create_refresh_token(user_id, jti)
        
        assert expires_at == fixed_now + timedelta(days=7)
        payload = jwt.decode(
            token, 
            jwt_settings["secret"], 
            algorithms=[jwt_settings["algorithm"]],
            options={"verify_exp": False}
        )
        assert payload["token_type"] == "refresh"
        assert payload["user_id"] == user_id

def test_validate_token_success(jwt_settings):
    """Test successful token validation."""
    user_id = "user_123"
    jti = "jti_access"
    
    # Use real now to avoid expiration issues in validation tests
    with patch.object(EnvironmentHandler, "get_value_as_str", return_value=jwt_settings["secret"]):
        token, _ = jwt_helper.create_access_token(user_id, jti)
        success, payload = jwt_helper.validate_access_token(token)
        
        assert success is True
        assert payload["user_id"] == user_id
        assert payload["jti"] == jti

def test_validate_token_expired(jwt_settings):
    """Test validation of an expired token."""
    # Use a time in the very distant past
    past_now = datetime(2020, 1, 1, tzinfo=timezone.utc)
    user_id = "user_123"
    jti = "jti_expired"
    
    with patch.object(EnvironmentHandler, "get_value_as_str", return_value=jwt_settings["secret"]):
        # Manually create an expired token because create_access_token uses _now() internal to helper
        # but we need to trick jwt.decode (which uses real time)
        payload = {
            "user_id": user_id,
            "jti": jti,
            "token_type": "access",
            "exp": int(past_now.timestamp()),
            "iat": int(past_now.timestamp()),
            "nbf": int(past_now.timestamp())
        }
        token = jwt.encode(payload, jwt_settings["secret"], algorithm=jwt_settings["algorithm"])
        
        success, error = jwt_helper.validate_access_token(token)
        assert success is False
        assert isinstance(error, JWTExpiredError)

def test_validate_token_type_mismatch(jwt_settings):
    """Test error when access token is used where refresh token is expected."""
    with patch.object(EnvironmentHandler, "get_value_as_str", return_value=jwt_settings["secret"]):
        access_token, _ = jwt_helper.create_access_token("u1", "j1")
        
        # Validate as refresh
        success, error = jwt_helper.validate_refresh_token(access_token)
        assert success is False
        assert isinstance(error, JWTTokenTypeError)

def test_validate_token_invalid_signature(jwt_settings):
    """Test validation failure due to wrong secret."""
    with patch.object(EnvironmentHandler, "get_value_as_str", return_value=jwt_settings["secret"]):
        token, _ = jwt_helper.create_access_token("u1", "j1")
        
    # Switch secret for validation
    with patch.object(EnvironmentHandler, "get_value_as_str", return_value="WRONG_SECRET"):
        jwt_helper._jwt_secret_key = None # Clear cache
        success, error = jwt_helper.validate_access_token(token)
        assert success is False
        assert isinstance(error, JWTInvalidTokenError)

def test_get_remaining_time(jwt_settings):
    """Test calculation of remaining time for a token."""
    fixed_now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    
    # We need to provide enough values for _now() calls
    # create_access_token: 3 calls (expires calculation, iat, nbf)
    # get_token_remaining_time: 1 call
    side_effects = [fixed_now] * 3 + [fixed_now + timedelta(minutes=10)]
    
    with patch.object(EnvironmentHandler, "get_value_as_str", return_value=jwt_settings["secret"]), \
         patch.object(jwt_helper, "_now", side_effect=side_effects):
        
        token, _ = jwt_helper.create_access_token("u1", "j1")
        
        # Initially (at creation) it's 60 mins. After 10 mins, it should be 50.
        remaining = jwt_helper.get_token_remaining_time(token)
        assert remaining == 50 * 60

def test_decode_unverified(jwt_settings):
    """Test decoding token without signature verification."""
    user_id = "user_hidden"
    with patch.object(EnvironmentHandler, "get_value_as_str", return_value=jwt_settings["secret"]):
        token, _ = jwt_helper.create_access_token(user_id, "jti")
        
    payload = jwt_helper.decode_token_unverified(token)
    assert payload["user_id"] == user_id

def test_utility_getters(jwt_settings):
    """Test user_id and jti extraction utilities."""
    user_id = "test_user_id"
    jti = "test_jti"
    
    with patch.object(EnvironmentHandler, "get_value_as_str", return_value=jwt_settings["secret"]):
        token, _ = jwt_helper.create_access_token(user_id, jti)
        
        assert jwt_helper.get_token_user_id(token) == user_id
        assert jwt_helper.get_token_jti(token) == jti

def test_missing_required_claim(jwt_settings):
    """Test error when a required claim is missing from the payload."""
    payload = {"user_id": "u1", "jti": "j1"} # Missing exp, iat, nbf, token_type
    token = jwt.encode(payload, jwt_settings["secret"], algorithm=jwt_settings["algorithm"])
    
    with patch.object(EnvironmentHandler, "get_value_as_str", return_value=jwt_settings["secret"]):
        success, error = jwt_helper.validate_access_token(token)
        assert success is False
        assert isinstance(error, JWTMissingClaimError)

def test_config_loading_fallbacks():
    """Test fallbacks for invalid or missing configuration values."""
    with patch.object(EnvironmentHandler, "get_value_as_str", return_value="secret"), \
         patch.object(ConfigurationHandler, "get_value_as_str", return_value=None), \
         patch.object(ConfigurationHandler, "get_value_as_int", return_value=-1): # Invalid value
        
        # Reset cache to force reload
        jwt_helper._jwt_algorithm = None
        jwt_helper._access_token_expire_minutes = None
        jwt_helper._refresh_token_expire_days = None
        
        assert jwt_helper._get_jwt_algorithm() == "HS256"
        assert jwt_helper._get_access_token_expire_minutes() == timedelta(minutes=60)
        assert jwt_helper._get_refresh_token_expire_days() == timedelta(days=7)

def test_token_creation_failure(jwt_settings):
    """Test error handling when jwt.encode fails."""
    with patch.object(EnvironmentHandler, "get_value_as_str", return_value=jwt_settings["secret"]), \
         patch("jwt.encode", side_effect=Exception("Crypto Library Error")):
        
        with pytest.raises(JWTInvalidTokenError) as exc:
            jwt_helper.create_access_token("u1", "j1")
        assert "Access token oluşturma başarısız" in str(exc.value)

def test_validate_token_not_before(jwt_settings):
    """Test validation failure when current time is before nbf claim."""
    future_now = datetime(2030, 1, 1, tzinfo=timezone.utc)
    user_id = "user_123"
    
    with patch.object(EnvironmentHandler, "get_value_as_str", return_value=jwt_settings["secret"]):
        payload = {
            "user_id": user_id,
            "jti": "j1",
            "token_type": "access",
            "exp": int(future_now.timestamp()) + 3600,
            "iat": int(future_now.timestamp()),
            "nbf": int(future_now.timestamp()) + 60 # Not before 1 minute from now
        }
        token = jwt.encode(payload, jwt_settings["secret"], algorithm=jwt_settings["algorithm"])
        
        # Validation should fail because it's not "before" nbf yet
        success, error = jwt_helper.validate_access_token(token)
        assert success is False
        assert isinstance(error, JWTInvalidTokenError)
        assert "The token is not yet valid" in str(error)

def test_get_remaining_time_edge_cases():
    """Test remaining time with invalid inputs."""
    assert jwt_helper.get_token_remaining_time("garbage.token.string") is None
    
    # Token without exp
    payload = {"user_id": "u1"}
    token = jwt.encode(payload, "key", algorithm="HS256")
    assert jwt_helper.get_token_remaining_time(token) is None

def test_validate_token_unexpected_error(jwt_settings):
    """Test catch-all exception handling in validation."""
    with patch.object(EnvironmentHandler, "get_value_as_str", return_value=jwt_settings["secret"]), \
         patch("jwt.decode", side_effect=RuntimeError("Unexpected!")):
        
        success, error = jwt_helper.validate_access_token("valid.token.here")
        assert success is False
        assert isinstance(error, JWTInvalidTokenError)
        assert "Unexpected error during token validation" in str(error)
def test_validate_token_invalid_issuer(jwt_settings):
    """Test validation failure with mismatching issuer."""
    with patch.object(EnvironmentHandler, "get_value_as_str", return_value=jwt_settings["secret"]):
        # Token with issuer
        payload = {
            "user_id": "u1",
            "jti": "j1",
            "token_type": "access",
            "iss": "wrong-issuer",
            "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
            "iat": int(datetime.now(timezone.utc).timestamp()),
            "nbf": int(datetime.now(timezone.utc).timestamp())
        }
        token = jwt.encode(payload, jwt_settings["secret"], algorithm=jwt_settings["algorithm"])
        
        # We don't provide expected issuer, so PyJWT normally ignores it unless we use options.
        # But if we were to mock jwt.decode to raise InvalidIssuerError:
        with patch("jwt.decode", side_effect=jwt.InvalidIssuerError("Invalid issuer")):
            success, error = jwt_helper.validate_access_token(token)
            assert success is False
            assert isinstance(error, JWTInvalidTokenError)
            assert "invalid_issuer" in error.error_details.get("reason", "")

def test_validate_token_invalid_audience(jwt_settings):
    """Test validation failure with mismatching audience."""
    with patch.object(EnvironmentHandler, "get_value_as_str", return_value=jwt_settings["secret"]):
        with patch("jwt.decode", side_effect=jwt.InvalidAudienceError("Invalid audience")):
            success, error = jwt_helper.validate_access_token("some.token")
            assert success is False
            assert isinstance(error, JWTInvalidTokenError)
            assert "invalid_audience" in error.error_details.get("reason", "")

def test_get_remaining_time_already_expired(jwt_settings):
    """Test that remaining time returns 0 for already expired tokens."""
    past_now = datetime(2020, 1, 1, tzinfo=timezone.utc)
    payload = {"exp": int(past_now.timestamp())}
    token = jwt.encode(payload, "secret", algorithm="HS256")
    
    # Real now > 2020, so it's expired
    remaining = jwt_helper.get_token_remaining_time(token)
    assert remaining == 0
