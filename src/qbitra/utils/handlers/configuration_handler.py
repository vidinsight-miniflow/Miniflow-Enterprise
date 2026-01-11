from pathlib import Path
from configparser import ConfigParser

from qbitra.core.qbitra_logger import get_logger
from qbitra.core.exceptions import (
    QBitraException,
    ConfigurationError,
    ConfigurationDirectoryNotFoundError,
    ConfigurationFileNotFoundError,
    ConfigurationInvalidAppEnvError,
    ConfigurationTestFailedError,
    ConfigurationNotInitializedError,
    ConfigurationTypeConversionError,
)
from .environment_handler import EnvironmentHandler


class ConfigurationHandler:
    """Configuration handler for loading and managing application configuration files."""

    _initialized = False
    _parser = ConfigParser()
    _config_dir = None
    _current_env = None
    _logger = get_logger("core")

    VALID_ENVIRONMENTS = ("dev", "prod", "stage", "test")

    @classmethod
    def load(cls):
        """Load configuration files based on APP_ENV environment variable."""
        if cls._initialized:
            cls._logger.info("Configuration Handler daha önce başlatılmış, tekrar başlatılamaz")
            return

        if not EnvironmentHandler.is_initialized():
            cls._logger.debug("Environment Handler başlatılıyor...")
            EnvironmentHandler.load()

        project_root = Path(__file__).resolve().parents[3]
        cls._config_dir = project_root / "configurations"

        if not cls._config_dir.exists():
            cls._logger.error(
                f"Configuration dizini bulunamadı: {cls._config_dir}",
                extra={"config_directory": str(cls._config_dir)}
            )
            raise ConfigurationDirectoryNotFoundError(
                directory_path=str(cls._config_dir),
                message=f"Configuration dizini bulunamadı: {cls._config_dir}"
            )

        cls._load_configuration_file()
        cls._logger.debug("Configuration dosyası başarıyla yüklendi")
        cls._initialized = True

    @classmethod
    def _load_configuration_file(cls):
        """Load the appropriate configuration file based on APP_ENV."""
        app_env = EnvironmentHandler.get_value_as_str("APP_ENV")

        if not app_env:
            cls._logger.error(
                "APP_ENV environment variable tanımlı değil",
                extra={"valid_environments": list(cls.VALID_ENVIRONMENTS)}
            )
            raise ConfigurationInvalidAppEnvError(
                app_env=None,
                valid_environments=list(cls.VALID_ENVIRONMENTS),
                message=f"APP_ENV environment variable tanımlı değil. Geçerli değerler: {cls.VALID_ENVIRONMENTS}"
            )

        app_env = app_env.lower()
        cls._current_env = app_env

        env_file_map = {
            "dev": "dev.ini",
            "prod": "prod.ini",
            "local": "local.ini",
            "test": "test.ini",
        }

        matched_env = None
        for env_key in env_file_map:
            if env_key in app_env:
                matched_env = env_key
                break

        if not matched_env:
            cls._logger.error(
                f"Geçersiz APP_ENV değeri: {app_env}",
                extra={"app_env": app_env, "valid_environments": list(cls.VALID_ENVIRONMENTS)}
            )
            raise ConfigurationInvalidAppEnvError(
                app_env=app_env,
                valid_environments=list(cls.VALID_ENVIRONMENTS),
                message=f"Geçersiz APP_ENV değeri: '{app_env}'. Geçerli değerler: {cls.VALID_ENVIRONMENTS}"
            )

        ini_file = cls._config_dir / env_file_map[matched_env]

        if not ini_file.exists():
            cls._logger.error(
                f"Configuration dosyası bulunamadı: {ini_file}",
                extra={"config_file": str(ini_file), "app_env": app_env}
            )
            raise ConfigurationFileNotFoundError(
                file_path=str(ini_file),
                message=f"Configuration dosyası bulunamadı: {ini_file}"
            )

        cls._parser.read(ini_file)
        cls._logger.debug(f"Configuration dosyası yüklendi: {ini_file}")

    @classmethod
    def test(cls, test_section: str = "Test", test_key: str = "value", expected_value: str = "ThisKeyIsForConfigTest"):
        """Test configuration file validity by checking test key."""
        if not cls._initialized:
            cls._logger.error("Test işlemi yapılmadan önce Configuration Handler başlatılmalıdır")
            cls._logger.debug("Configuration Handler başlatılıyor...")
            cls.load()

        actual_value = cls._parser.get(test_section, test_key, fallback=None)
        cls._logger.debug(
            f"Test section: {test_section}, Test key: {test_key}, "
            f"Expected: {expected_value}, Actual: {actual_value}"
        )
        return actual_value == expected_value, actual_value, expected_value

    @classmethod
    def init(cls, test_section: str = "Test", test_key: str = "value", expected_value: str = "ThisKeyIsForConfigTest"):
        """Initialize Configuration Handler with validation test."""
        if cls._initialized:
            cls._logger.info("Configuration Handler daha önce başlatılmış, tekrar başlatılamaz")
            return True

        cls.load()

        success, actual_value, expected_value = cls.test(test_section, test_key, expected_value)
        if not success:
            cls._logger.error(
                "Configuration test başarısız, config dosyasını kontrol ediniz",
                extra={
                    "test_section": test_section,
                    "test_key": test_key,
                    "expected_value": expected_value,
                    "actual_value": actual_value
                }
            )
            raise ConfigurationTestFailedError(
                test_section=test_section,
                test_key=test_key,
                expected_value=expected_value,
                actual_value=actual_value,
                message=f"Configuration test başarısız. Beklenen: {expected_value}, Bulunan: {actual_value}"
            )

        cls._logger.info("Configuration Handler başarıyla başlatıldı")
        return cls._initialized

    @classmethod
    def is_initialized(cls) -> bool:
        """Check if Configuration Handler is initialized."""
        return cls._initialized

    @classmethod
    def get_current_env(cls) -> str:
        """Get the current environment name."""
        return cls._current_env

    @classmethod
    def _get(cls, section: str, key: str, fallback=None):
        """Internal method to get raw value from configuration."""
        if not cls._initialized:
            cls._logger.error(
                "Get işlemi yapılmadan önce Configuration Handler başlatılmalıdır",
                extra={"section": section, "key": key}
            )
            raise ConfigurationNotInitializedError(
                message="Configuration Handler başlatılmadan değer alınamaz"
            )
        return cls._parser.get(section, key, fallback=fallback)

    @classmethod
    def get_value_as_str(cls, section: str, key: str, fallback: str = None) -> str:
        """Get a string value from configuration."""
        try:
            value = cls._get(section, key, fallback=fallback)
            if value is None:
                return fallback
            return str(value).strip()
        except (QBitraException, ConfigurationError):
            raise
        except Exception as e:
            cls._logger.error(
                f"Configuration değeri alınamadı: [{section}] {key}",
                extra={"section": section, "key": key, "target_type": "string", "error": str(e)},
                exc_info=True
            )
            raise ConfigurationTypeConversionError(
                section=section,
                key=key,
                target_type="string",
                message=f"[{section}] {key} string'e dönüştürülemedi: {e}",
                cause=e
            ) from e

    @classmethod
    def get_value_as_int(cls, section: str, key: str, fallback: int = None) -> int:
        """Get an integer value from configuration."""
        try:
            if not cls._initialized:
                raise ConfigurationNotInitializedError(
                    "Configuration Handler başlatılmadan değer alınamaz"
                )
            value = cls._parser.getint(section, key, fallback=fallback)
            if value is None:
                return fallback
            return value
        except (QBitraException, ConfigurationError):
            raise
        except (ValueError, TypeError) as e:
            cls._logger.error(
                f"Configuration değeri alınamadı: [{section}] {key}",
                extra={"section": section, "key": key, "target_type": "integer", "error": str(e)},
                exc_info=True
            )
            raise ConfigurationTypeConversionError(
                section=section,
                key=key,
                target_type="integer",
                message=f"[{section}] {key} integer'a dönüştürülemedi: {e}",
                cause=e
            ) from e

    @classmethod
    def get_value_as_float(cls, section: str, key: str, fallback: float = None) -> float:
        """Get a float value from configuration."""
        try:
            if not cls._initialized:
                raise ConfigurationNotInitializedError(
                    "Configuration Handler başlatılmadan değer alınamaz"
                )
            value = cls._parser.getfloat(section, key, fallback=fallback)
            if value is None:
                return fallback
            return value
        except (QBitraException, ConfigurationError):
            raise
        except (ValueError, TypeError) as e:
            cls._logger.error(
                f"Configuration değeri alınamadı: [{section}] {key}",
                extra={"section": section, "key": key, "target_type": "float", "error": str(e)},
                exc_info=True
            )
            raise ConfigurationTypeConversionError(
                section=section,
                key=key,
                target_type="float",
                message=f"[{section}] {key} float'a dönüştürülemedi: {e}",
                cause=e
            ) from e

    @classmethod
    def get_value_as_bool(cls, section: str, key: str, fallback: bool = None) -> bool:
        """Get a boolean value from configuration."""
        try:
            if not cls._initialized:
                raise ConfigurationNotInitializedError(
                    "Configuration Handler başlatılmadan değer alınamaz"
                )
            value = cls._parser.getboolean(section, key, fallback=fallback)
            if value is None:
                return fallback
            return value
        except (QBitraException, ConfigurationError):
            raise
        except (ValueError, TypeError) as e:
            cls._logger.error(
                f"Configuration değeri alınamadı: [{section}] {key}",
                extra={"section": section, "key": key, "target_type": "boolean", "error": str(e)},
                exc_info=True
            )
            raise ConfigurationTypeConversionError(
                section=section,
                key=key,
                target_type="boolean",
                message=f"[{section}] {key} boolean'a dönüştürülemedi: {e}",
                cause=e
            ) from e

    @classmethod
    def get_value_as_list(cls, section: str, key: str, separator: str = ",", fallback: list = None) -> list:
        """Get a list value from configuration by splitting on separator."""
        try:
            value = cls._get(section, key, fallback=None)
            if value is None:
                return fallback if fallback is not None else []
            if isinstance(value, list):
                return value
            if not isinstance(value, str):
                return fallback if fallback is not None else []
            return [item.strip() for item in value.split(separator) if item.strip()]
        except (QBitraException, ConfigurationError):
            raise
        except Exception as e:
            cls._logger.error(
                f"Configuration değeri alınamadı: [{section}] {key}",
                extra={"section": section, "key": key, "target_type": "list", "error": str(e)},
                exc_info=True
            )
            raise ConfigurationTypeConversionError(
                section=section,
                key=key,
                target_type="list",
                message=f"[{section}] {key} list'e dönüştürülemedi: {e}",
                cause=e
            ) from e

    @classmethod
    def has_section(cls, section: str) -> bool:
        """Check if a section exists in the configuration."""
        if not cls._initialized:
            cls._logger.error(
                "Configuration Handler başlatılmadan kontrol yapılamaz",
                extra={"section": section}
            )
            raise ConfigurationNotInitializedError(
                message="Configuration Handler başlatılmadan kontrol yapılamaz"
            )
        return cls._parser.has_section(section)

    @classmethod
    def has_option(cls, section: str, key: str) -> bool:
        """Check if an option exists in a section."""
        if not cls._initialized:
            cls._logger.error(
                "Configuration Handler başlatılmadan kontrol yapılamaz",
                extra={"section": section}
            )
            raise ConfigurationNotInitializedError(
                message="Configuration Handler başlatılmadan kontrol yapılamaz"
            )
        return cls._parser.has_option(section, key)

    @classmethod
    def get_sections(cls) -> list:
        """Get all section names."""
        if not cls._initialized:
            raise ConfigurationNotInitializedError(
                "Configuration Handler başlatılmadan section listesi alınamaz"
            )
        return cls._parser.sections()

    @classmethod
    def get_options(cls, section: str) -> list:
        """Get all option names in a section."""
        if not cls._initialized:
            raise ConfigurationNotInitializedError(
                "Configuration Handler başlatılmadan option listesi alınamaz"
            )
        return cls._parser.options(section)

    @classmethod
    def reload(cls):
        """Reload configuration file from disk."""
        cls._logger.info("Configuration yeniden yükleniyor...")
        cls._initialized = False
        cls._parser = ConfigParser()
        cls.load()
        cls._logger.info("Configuration başarıyla yeniden yüklendi")

    @classmethod
    def ensure_loaded(cls):
        """Ensure configuration is loaded. Safe to call multiple times."""
        if not cls._initialized:
            cls.load()