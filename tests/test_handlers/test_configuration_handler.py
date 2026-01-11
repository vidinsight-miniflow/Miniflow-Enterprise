import pytest
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from configparser import ConfigParser
from qbitra.utils.handlers.configuration_handler import ConfigurationHandler
from qbitra.utils.handlers.environment_handler import EnvironmentHandler
from qbitra.core.exceptions import (
    ConfigurationDirectoryNotFoundError,
    ConfigurationFileNotFoundError,
    ConfigurationInvalidAppEnvError,
    ConfigurationTestFailedError,
    ConfigurationNotInitializedError,
    ConfigurationTypeConversionError,
)

@pytest.fixture(autouse=True)
def reset_config_handler():
    """Reset ConfigurationHandler class variables before each test."""
    ConfigurationHandler._initialized = False
    ConfigurationHandler._parser = ConfigParser()
    ConfigurationHandler._config_dir = None
    ConfigurationHandler._current_env = None
    yield
    ConfigurationHandler._initialized = False
    ConfigurationHandler._parser = ConfigParser()
    ConfigurationHandler._config_dir = None
    ConfigurationHandler._current_env = None

def test_load_directory_not_found():
    """Test load() raises error if configurations directory is missing."""
    with patch("qbitra.utils.handlers.environment_handler.EnvironmentHandler.is_initialized", return_value=True), \
         patch("pathlib.Path.exists", return_value=False):
        with pytest.raises(ConfigurationDirectoryNotFoundError):
            ConfigurationHandler.load()

def test_load_app_env_missing():
    """Test load() raises error if APP_ENV is not set."""
    with patch("qbitra.utils.handlers.environment_handler.EnvironmentHandler.is_initialized", return_value=True), \
         patch("pathlib.Path.exists", return_value=True), \
         patch("qbitra.utils.handlers.environment_handler.EnvironmentHandler.get_value_as_str", return_value=None):
        with pytest.raises(ConfigurationInvalidAppEnvError) as exc:
            ConfigurationHandler.load()
        assert "APP_ENV environment variable tanımlı değil" in str(exc.value)

def test_load_invalid_app_env():
    """Test load() raises error if APP_ENV is invalid."""
    with patch("qbitra.utils.handlers.environment_handler.EnvironmentHandler.is_initialized", return_value=True), \
         patch("pathlib.Path.exists", return_value=True), \
         patch("qbitra.utils.handlers.environment_handler.EnvironmentHandler.get_value_as_str", return_value="invalid"):
        with pytest.raises(ConfigurationInvalidAppEnvError) as exc:
            ConfigurationHandler.load()
        assert "Geçersiz APP_ENV değeri" in str(exc.value)

def test_load_file_not_found():
    """Test load() raises error if the .ini file is missing."""
    with patch("qbitra.utils.handlers.environment_handler.EnvironmentHandler.is_initialized", return_value=True), \
         patch("qbitra.utils.handlers.environment_handler.EnvironmentHandler.get_value_as_str", return_value="dev"), \
         patch("pathlib.Path.exists", side_effect=[True, False, True, True]): # Dir exists, File doesn't
        with pytest.raises(ConfigurationFileNotFoundError):
            ConfigurationHandler.load()

def test_load_success():
    """Test successful configuration loading."""
    with patch("qbitra.utils.handlers.environment_handler.EnvironmentHandler.is_initialized", return_value=True), \
         patch("qbitra.utils.handlers.environment_handler.EnvironmentHandler.get_value_as_str", return_value="dev"), \
         patch("pathlib.Path.exists", return_value=True), \
         patch("configparser.ConfigParser.read") as mock_read:
        
        ConfigurationHandler.load()
        assert ConfigurationHandler.is_initialized() is True
        assert ConfigurationHandler.get_current_env() == "dev"
        mock_read.assert_called_once()

def test_init_and_validation_success():
    """Test init() with validation success."""
    def mock_load():
        ConfigurationHandler._initialized = True

    with patch.object(ConfigurationHandler, "load", side_effect=mock_load), \
         patch.object(ConfigurationHandler, "_parser") as mock_parser:
        
        mock_parser.get.return_value = "ThisKeyIsForConfigTest"
        success = ConfigurationHandler.init()
        assert success is True
        assert ConfigurationHandler.is_initialized() is True

def test_init_validation_failure():
    """Test init() raises error on validation failure."""
    ConfigurationHandler._initialized = False
    with patch.object(ConfigurationHandler, "load"), \
         patch.object(ConfigurationHandler, "_parser") as mock_parser:
        
        mock_parser.get.return_value = "WrongValue"
        with pytest.raises(ConfigurationTestFailedError):
            ConfigurationHandler.init()

def test_get_value_as_str():
    """Test string type conversion."""
    ConfigurationHandler._initialized = True
    ConfigurationHandler._parser.add_section("App")
    ConfigurationHandler._parser.set("App", "name", " QBitra ")
    
    assert ConfigurationHandler.get_value_as_str("App", "name") == "QBitra"
    assert ConfigurationHandler.get_value_as_str("App", "missing", fallback="def") == "def"

def test_get_value_as_int():
    """Test integer type conversion."""
    ConfigurationHandler._initialized = True
    ConfigurationHandler._parser.add_section("App")
    ConfigurationHandler._parser.set("App", "port", "8080")
    
    assert ConfigurationHandler.get_value_as_int("App", "port") == 8080
    
    ConfigurationHandler._parser.set("App", "bad_int", "not_int")
    with pytest.raises(ConfigurationTypeConversionError) as exc:
        ConfigurationHandler.get_value_as_int("App", "bad_int")
    assert exc.value.error_details["target_type"] == "integer"

def test_get_value_as_float():
    """Test float type conversion."""
    ConfigurationHandler._initialized = True
    ConfigurationHandler._parser.add_section("App")
    ConfigurationHandler._parser.set("App", "version", "1.5")
    
    assert ConfigurationHandler.get_value_as_float("App", "version") == 1.5
    
    ConfigurationHandler._parser.set("App", "bad_float", "abc")
    with pytest.raises(ConfigurationTypeConversionError) as exc:
        ConfigurationHandler.get_value_as_float("App", "bad_float")
    assert exc.value.error_details["target_type"] == "float"

def test_get_value_as_bool():
    """Test boolean type conversion."""
    ConfigurationHandler._initialized = True
    ConfigurationHandler._parser.add_section("App")
    ConfigurationHandler._parser.set("App", "debug", "true")
    
    assert ConfigurationHandler.get_value_as_bool("App", "debug") is True
    
    ConfigurationHandler._parser.set("App", "off_key", "no")
    assert ConfigurationHandler.get_value_as_bool("App", "off_key") is False

def test_get_value_as_list():
    """Test list type conversion."""
    ConfigurationHandler._initialized = True
    ConfigurationHandler._parser.add_section("App")
    ConfigurationHandler._parser.set("App", "allowed_hosts", "localhost, 127.0.0.1,  internal.net ")
    
    assert ConfigurationHandler.get_value_as_list("App", "allowed_hosts") == ["localhost", "127.0.0.1", "internal.net"]
    assert ConfigurationHandler.get_value_as_list("App", "missing") == []

def test_section_management():
    """Test section and option existence checks."""
    ConfigurationHandler._initialized = True
    ConfigurationHandler._parser.add_section("DB")
    ConfigurationHandler._parser.set("DB", "host", "localhost")
    
    assert ConfigurationHandler.has_section("DB") is True
    assert ConfigurationHandler.has_section("Missing") is False
    assert ConfigurationHandler.has_option("DB", "host") is True
    assert ConfigurationHandler.get_sections() == ["DB"]
    assert ConfigurationHandler.get_options("DB") == ["host"]

def test_not_initialized_error_across_types():
    """Test that all getters raise error before initialization."""
    ConfigurationHandler._initialized = False
    
    getters = [
        lambda: ConfigurationHandler.get_value_as_str("ANY", "KEY"),
        lambda: ConfigurationHandler.get_value_as_int("ANY", "KEY"),
        lambda: ConfigurationHandler.get_value_as_float("ANY", "KEY"),
        lambda: ConfigurationHandler.get_value_as_bool("ANY", "KEY"),
        lambda: ConfigurationHandler.get_value_as_list("ANY", "KEY"),
        lambda: ConfigurationHandler.has_section("ANY"),
        lambda: ConfigurationHandler.has_option("ANY", "KEY"),
        lambda: ConfigurationHandler.get_sections(),
        lambda: ConfigurationHandler.get_options("ANY"),
    ]
    
    for getter in getters:
        with pytest.raises(ConfigurationNotInitializedError):
            getter()

def test_type_conversion_error_metadata():
    """Test that ConfigurationTypeConversionError contains correct metadata."""
    ConfigurationHandler._initialized = True
    ConfigurationHandler._parser.add_section("App")
    ConfigurationHandler._parser.set("App", "bad_int", "not_int")
    
    with pytest.raises(ConfigurationTypeConversionError) as exc:
        ConfigurationHandler.get_value_as_int("App", "bad_int")
    
    assert exc.value.error_details["section"] == "App"
    assert exc.value.error_details["key"] == "bad_int"
    assert exc.value.error_details["target_type"] == "integer"

def test_type_conversion_error_catch_all():
    """Test the catch-all exception block in getters."""
    ConfigurationHandler._initialized = True
    
    # Mocking _parser.get to raise a weird error
    with patch.object(ConfigurationHandler._parser, "get", side_effect=RuntimeError("Unexpected")):
        with pytest.raises(ConfigurationTypeConversionError) as exc:
            ConfigurationHandler.get_value_as_str("App", "any")
        assert exc.value.error_details["target_type"] == "string"
        assert "Unexpected" in str(exc.value.__cause__)

def test_reload():
    """Test reload functionality."""
    with patch.object(ConfigurationHandler, "load") as mock_load:
        ConfigurationHandler.reload()
        assert ConfigurationHandler._initialized is False # It gets set to False then load() is called
        mock_load.assert_called_once()
