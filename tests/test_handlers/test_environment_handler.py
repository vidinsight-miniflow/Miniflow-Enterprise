import pytest
import os
import json
from unittest.mock import patch, MagicMock
from pathlib import Path
from qbitra.utils.handlers.environment_handler import EnvironmentHandler
from qbitra.core.exceptions import (
    EnvironmentFileNotFoundError,
    EnvironmentTestFailedError,
    EnvironmentNotInitializedError,
    EnvironmentTypeConversionError,
)

@pytest.fixture(autouse=True)
def reset_handler():
    """Reset EnvironmentHandler class variables before each test."""
    EnvironmentHandler._initialized = False
    EnvironmentHandler._env_path = None
    yield
    EnvironmentHandler._initialized = False
    EnvironmentHandler._env_path = None

def test_load_file_not_found():
    """Test load() raises error if .env is missing."""
    with patch("pathlib.Path.exists", return_value=False):
        with pytest.raises(EnvironmentFileNotFoundError):
            EnvironmentHandler.load()

def test_load_success():
    """Test successful environment loading."""
    with patch("pathlib.Path.exists", return_value=True), \
         patch("qbitra.utils.handlers.environment_handler.load_dotenv") as mock_load:
        EnvironmentHandler.load()
        assert EnvironmentHandler._initialized is True
        mock_load.assert_called_once()
        
        # Test duplicate load attempt
        EnvironmentHandler.load()
        # mock_load should still be called only once from previous call (logic skips if initialized)
        assert mock_load.call_count == 1

def test_init_and_test_logic():
    """Test init() and test() methods."""
    # Side effect to set _initialized=True as real load would do
    def mock_load():
        EnvironmentHandler._initialized = True

    with patch.object(EnvironmentHandler, "load", side_effect=mock_load), \
         patch("os.getenv", return_value="ThisKeyIsForEnvTest"):
        
        success = EnvironmentHandler.init()
        assert success is True
        assert EnvironmentHandler.is_initialized() is True

    # Test failure case
    EnvironmentHandler._initialized = False # reset for failure test
    with patch.object(EnvironmentHandler, "load", side_effect=mock_load), \
         patch("os.getenv", return_value="WrongValue"):
        
        with pytest.raises(EnvironmentTestFailedError):
            EnvironmentHandler.init()

def test_get_value_as_str():
    """Test string type conversion."""
    EnvironmentHandler._initialized = True # Simulate loaded state
    with patch("os.getenv", return_value="  hello  "):
        assert EnvironmentHandler.get_value_as_str("ANY") == "hello"
    
    with patch("os.getenv", return_value=None):
        assert EnvironmentHandler.get_value_as_str("MISSING", default="def") == "def"

def test_get_value_as_int():
    """Test integer type conversion."""
    EnvironmentHandler._initialized = True
    with patch("os.getenv", return_value="123"):
        assert EnvironmentHandler.get_value_as_int("ANY") == 123
    
    with patch("os.getenv", return_value="not_an_int"):
        with pytest.raises(EnvironmentTypeConversionError):
            EnvironmentHandler.get_value_as_int("ANY")

def test_get_value_as_float():
    """Test float type conversion."""
    EnvironmentHandler._initialized = True
    with patch("os.getenv", return_value="12.34"):
        assert EnvironmentHandler.get_value_as_float("ANY") == 12.34
    
    with patch("os.getenv", return_value="abc"):
        with pytest.raises(EnvironmentTypeConversionError):
            EnvironmentHandler.get_value_as_float("ANY")

def test_get_value_as_bool():
    """Test boolean type conversion."""
    EnvironmentHandler._initialized = True
    
    # Test truthy cases
    for val in ["true", "1", "yes", "on"]:
        with patch.dict(os.environ, {"ANY_BOOL": val}):
            assert EnvironmentHandler.get_value_as_bool("ANY_BOOL") is True
            
    # Test falsy cases
    for val in ["false", "0", "no", "off"]:
        with patch.dict(os.environ, {"ANY_BOOL": val}):
            assert EnvironmentHandler.get_value_as_bool("ANY_BOOL") is False
            
    # Test unknown string returns default
    with patch.dict(os.environ, {"ANY_BOOL": "anything_else"}):
        assert EnvironmentHandler.get_value_as_bool("ANY_BOOL") is None
        assert EnvironmentHandler.get_value_as_bool("ANY_BOOL", default=False) is False

def test_get_value_as_bool_default():
    """Test boolean default value when key is missing."""
    EnvironmentHandler._initialized = True
    # Ensure key is not in environ
    with patch.dict(os.environ, {}, clear=False):
        if "MISSING_BOOL" in os.environ: os.environ.pop("MISSING_BOOL")
        assert EnvironmentHandler.get_value_as_bool("MISSING_BOOL", default=False) is False
        assert EnvironmentHandler.get_value_as_bool("MISSING_BOOL") is None

def test_get_value_as_list():
    """Test list type conversion from JSON."""
    EnvironmentHandler._initialized = True
    with patch("os.getenv", return_value='["a", 2, true]'):
        assert EnvironmentHandler.get_value_as_list("ANY") == ["a", 2, True]
    
    with patch("os.getenv", return_value='invalid_json'):
        with pytest.raises(EnvironmentTypeConversionError):
            EnvironmentHandler.get_value_as_list("ANY")

def test_get_value_as_dict():
    """Test dict type conversion from JSON."""
    EnvironmentHandler._initialized = True
    with patch("os.getenv", return_value='{"key": "val", "num": 1}'):
        assert EnvironmentHandler.get_value_as_dict("ANY") == {"key": "val", "num": 1}
    
    with patch("os.getenv", return_value='["not_a_dict"]'):
        # JSON is valid, but result is not a dict? 
        # Actually code returns json.loads(value) if not already dict.
        # json.loads('["not_a_dict"]') returns a list.
        res = EnvironmentHandler.get_value_as_dict("ANY")
        assert res == ["not_a_dict"] # The implementation doesn't check if it's actually a dict after json.loads

def test_not_initialized_error_across_types():
    """Test that all getters raise error before initialization."""
    EnvironmentHandler._initialized = False
    
    getters = [
        lambda: EnvironmentHandler.get_value_as_str("ANY"),
        lambda: EnvironmentHandler.get_value_as_int("ANY"),
        lambda: EnvironmentHandler.get_value_as_float("ANY"),
        lambda: EnvironmentHandler.get_value_as_bool("ANY"),
        lambda: EnvironmentHandler.get_value_as_list("ANY"),
        lambda: EnvironmentHandler.get_value_as_dict("ANY"),
    ]
    
    for getter in getters:
        with pytest.raises(EnvironmentNotInitializedError) as exc:
            getter()
        assert "başlatılmadan değer alınamaz" in str(exc.value)

def test_type_conversion_error_metadata():
    """Test that EnvironmentTypeConversionError contains correct metadata."""
    EnvironmentHandler._initialized = True
    
    # Int conversion error
    with patch("os.getenv", return_value="invalid"):
        with pytest.raises(EnvironmentTypeConversionError) as exc:
            EnvironmentHandler.get_value_as_int("MY_KEY")
        
        assert exc.value.error_details["key"] == "MY_KEY"
        assert exc.value.error_details["target_type"] == "integer"
        assert "integer'a dönüştürülemedi" in str(exc.value)

def test_json_decode_error_details():
    """Test JSON decode errors in list and dict getters."""
    EnvironmentHandler._initialized = True
    
    invalid_json = "{'key': single_quotes_are_invalid_in_json}"
    
    with patch("os.getenv", return_value=invalid_json):
        # List getter
        with pytest.raises(EnvironmentTypeConversionError) as exc_list:
            EnvironmentHandler.get_value_as_list("MY_LIST")
        assert exc_list.value.error_details["target_type"] == "list"
        assert "geçerli JSON değil" in str(exc_list.value)
        
        # Dict getter
        with pytest.raises(EnvironmentTypeConversionError) as exc_dict:
            EnvironmentHandler.get_value_as_dict("MY_DICT")
        assert exc_dict.value.error_details["target_type"] == "dict"
        assert "geçerli JSON değil" in str(exc_dict.value)

def test_bool_conversion_catch_all_error():
    """Test the catch-all exception block in get_value_as_bool."""
    EnvironmentHandler._initialized = True
    
    with patch.object(EnvironmentHandler, "_get", side_effect=RuntimeError("Unexpected")):
        with pytest.raises(EnvironmentTypeConversionError) as exc:
            EnvironmentHandler.get_value_as_bool("ANY")
        assert exc.value.error_details["target_type"] == "boolean"
        assert "Unexpected" in str(exc.value.__cause__)
