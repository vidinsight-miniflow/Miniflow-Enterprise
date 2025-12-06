from pathlib import Path
from configparser import ConfigParser
from .environment_handler import EnvironmentHandler
from miniflow.core.exceptions import ResourceNotFoundError, InternalError

class ConfigurationHandler:
    """Configuration handler for loading and managing application configuration files."""
    _initialized = False
    _parser = ConfigParser()
    _config_dir = None

    @classmethod
    def load_config(cls):
        """Load configuration files based on APP_ENV environment variable."""
        if cls._initialized:
            return

        EnvironmentHandler.load_env()

        project_root = Path(__file__).resolve().parents[4]
        cls._config_dir = project_root / "configurations"

        if not cls._config_dir.exists():
            raise ResourceNotFoundError(
                resource_name="Configuration directory",
                resource_id=str(cls._config_dir)
            )

        cls._load_configuration_file()

        success, test_value = cls.test()
        if not success:
            raise InternalError(
                component_name="configuration_handler",
                message="Configuration validation test failed. Configuration file may be corrupted or invalid.",
                error_details={
                    "test_section": "Test",
                    "test_key": "value",
                    "expected_value": "ThisKeyIsForConfigTest",
                    "actual_value": test_value,
                    "config_directory": str(cls._config_dir)
                }
            )

        cls._initialized = True

    @classmethod
    def _load_configuration_file(cls):
        """Load the appropriate configuration file based on APP_ENV."""
        app_type = EnvironmentHandler.get("APP_ENV")

        if not app_type:
            raise InternalError(
                component_name="configuration_handler",
                message="APP_ENV environment variable is not set or is empty.",
                error_details={
                    "required_variable": "APP_ENV",
                    "available_environments": ["dev", "prod", "local", "test"]
                }
            )

        app_type = app_type.lower()
        if "dev" in app_type:
            ini_file = cls._config_dir / "dev.ini"
        elif "prod" in app_type:
            ini_file = cls._config_dir / "prod.ini"
        elif "local" in app_type:
            ini_file = cls._config_dir / "local.ini"
        elif "test" in app_type:
            ini_file = cls._config_dir / "test.ini"
        else:
            raise InternalError(
                component_name="configuration_handler",
                message=f"Invalid APP_ENV value: '{app_type}'. Expected one of: dev, prod, local, test",
                error_details={
                    "provided_value": app_type,
                    "expected_values": ["dev", "prod", "local", "test"],
                    "config_directory": str(cls._config_dir)
                }
            )

        if not ini_file.exists():
            raise ResourceNotFoundError(
                resource_name="configuration file",
                resource_id=str(ini_file)
            )

        cls._parser.read(ini_file)

    @classmethod
    def test(cls):
        """Test configuration file validity by checking test key."""
        value = cls._parser.get("Test", "value", fallback=None)
        return (value == "ThisKeyIsForConfigTest", value if value else None)

    @classmethod
    def get(cls, section: str, key: str, fallback=None):
        """Get a string value from configuration."""
        return cls._parser.get(section, key, fallback=fallback)

    @classmethod
    def get_int(cls, section: str, key: str, fallback=None):
        """Get an integer value from configuration."""
        try:
            value = cls._parser.getint(section, key, fallback=fallback)
            # ConfigParser returns fallback as dict in some error cases
            if isinstance(value, dict):
                return fallback if isinstance(fallback, int) else None
            return value if value is not None else fallback
        except (ValueError, TypeError):
            return fallback if isinstance(fallback, int) else None
        except Exception:
            return fallback if isinstance(fallback, int) else None

    @classmethod
    def get_float(cls, section: str, key: str, fallback=None):
        """Get a float value from configuration."""
        try:
            value = cls._parser.getfloat(section, key, fallback=fallback)
            if isinstance(value, dict):
                return fallback if isinstance(fallback, (int, float)) else None
            return value if value is not None else fallback
        except (ValueError, TypeError):
            return fallback if isinstance(fallback, (int, float)) else None
        except Exception:
            return fallback if isinstance(fallback, (int, float)) else None

    @classmethod
    def get_bool(cls, section: str, key: str, fallback=None):
        """Get a boolean value from configuration."""
        try:
            value = cls._parser.getboolean(section, key, fallback=fallback)
            if isinstance(value, dict):
                return fallback if isinstance(fallback, bool) else None
            return value if value is not None else fallback
        except (ValueError, TypeError):
            return fallback if isinstance(fallback, bool) else None
        except Exception:
            return fallback if isinstance(fallback, bool) else None

    @classmethod
    def get_list(cls, section: str, key: str, separator: str = ",", fallback=None):
        """Get a list value from configuration by splitting on separator."""
        try:
            value = cls._parser.get(section, key, fallback=fallback)
        except Exception:
            return fallback if fallback is not None else []
        
        if value is None:
            return fallback if fallback is not None else []
        
        # If value is already a list, return it directly
        if isinstance(value, list):
            return value
        
        # If value is not a string, try to convert or return fallback
        if not isinstance(value, str):
            return fallback if fallback is not None else []
        
        # Split string by separator
        return [item.strip() for item in value.split(separator) if item.strip()]

    @classmethod
    def reload(cls):
        """Reload configuration file from disk."""
        cls._initialized = False
        cls._load_configuration_file()
        cls._initialized = True

    @classmethod
    def ensure_loaded(cls):
        """Ensure configuration is loaded. Safe to call multiple times."""
        if not cls._initialized:
            cls.load_config()
