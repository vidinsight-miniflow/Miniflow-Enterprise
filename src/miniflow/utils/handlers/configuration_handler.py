from pathlib import Path
from configparser import ConfigParser
from .environment_handler import EnvironmentHandler
from src.miniflow.core.exceptions import ResourceNotFoundError, InternalError

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

        print(f"[CONFIG] Config file is loading.")
        EnvironmentHandler.load_env()

        project_root = Path(__file__).resolve().parents[4]
        cls._config_dir = project_root / "configurations"

        if not cls._config_dir.exists():
            raise ResourceNotFoundError(
                resource_name="Config file can't found",
                resource_id=str(cls._config_dir)
            )

        cls._load_configuration_file()

        success, _ = cls.test()
        if not success:
            raise InternalError(
                message="Configuration validation test failed. Configuration file may be corrupted or invalid.",
                component_name="configuration_handler"
            )

        cls._initialized = True
        print(f"[CONFIG] Configuration files loaded successfully from: {cls._config_dir}")

    @classmethod
    def _load_configuration_file(cls):
        """Load the appropriate configuration file based on APP_ENV."""
        app_type = EnvironmentHandler.get("APP_ENV")

        if not app_type:
            raise InternalError(
                message="APP_ENV environment variable is not set or is empty.",
                component_name="configuration_handler"
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
                message=f"Invalid APP_ENV value: '{app_type}'. Expected one of: dev, prod, local, test",
                component_name="configuration_handler"
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
        return cls._parser.getint(section, key, fallback=fallback)

    @classmethod
    def get_bool(cls, section: str, key: str, fallback=None):
        """Get a boolean value from configuration."""
        return cls._parser.getboolean(section, key, fallback=fallback)

    @classmethod
    def get_list(cls, section: str, key: str, separator: str = ",", fallback=None):
        """Get a list value from configuration by splitting on separator."""
        value = cls._parser.get(section, key, fallback=fallback)
        if value is None:
            return fallback if fallback is not None else []
        return [item.strip() for item in value.split(separator) if item.strip()]

    @classmethod
    def reload(cls):
        """Reload configuration file from disk."""
        cls._load_configuration_file()
