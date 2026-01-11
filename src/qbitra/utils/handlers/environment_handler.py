import os
import json
from pathlib import Path
from dotenv import load_dotenv

from qbitra.core.qbitra_logger import get_logger
from qbitra.core.exceptions import (
    QBitraException,
    EnvironmentFileNotFoundError,
    EnvironmentTestFailedError,
    EnvironmentNotInitializedError,
    EnvironmentTypeConversionError,
)


class EnvironmentHandler:
    _env_path = None
    _initialized = False
    _logger = get_logger("core")

    @classmethod
    def load(cls):
        if cls._initialized:
            cls._logger.info("Environment Handler daha önce başlatılmış, tekrar başlatılamaz")
            return

        src_path = Path(__file__).resolve().parents[3]
        cls._env_path = src_path / ".env"

        if not cls._env_path.exists():
            cls._logger.error(
                f"Environment dosyası bulunamadı: {cls._env_path}",
                extra={"env_file_path": str(cls._env_path)}
            )
            raise EnvironmentFileNotFoundError(
                file_path=str(cls._env_path),
                message=f"Environment dosyası bulunamadı: {cls._env_path}"
            )

        load_dotenv(cls._env_path)
        cls._logger.debug("Environment dosyası başarıyla yüklendi")
        cls._initialized = True

    @classmethod
    def test(cls, test_key: str = "TestKey", expected_value: str = "ThisKeyIsForEnvTest"):
        if not cls._initialized:
            cls._logger.error("Test işlemi yapılmadan önce Environment Handler başlatılmalıdır")
            cls._logger.debug("Environment Handler başlatılıyor...")
            cls.load()

        actual_value = os.getenv(test_key)
        cls._logger.debug(f"Test key: {test_key}, Expected value: {expected_value}, Actual value: {actual_value}")
        return actual_value == expected_value, actual_value, expected_value

    @classmethod
    def init(cls, test_key: str = "TestKey", expected_value: str = "ThisKeyIsForEnvTest"):
        if cls._initialized:
            cls._logger.info("Environment Handler daha önce başlatılmış, tekrar başlatılamaz")
            return True

        cls.load()

        success, actual_value, expected_value = cls.test(test_key, expected_value)
        if not success:
            cls._logger.error(
                "Environment test başarısız, .env dosyasını kontrol ediniz",
                extra={
                    "test_key": test_key,
                    "expected_value": expected_value,
                    "actual_value": actual_value
                }
            )
            raise EnvironmentTestFailedError(
                test_key=test_key,
                expected_value=expected_value,
                actual_value=actual_value,
                message=f"Environment test başarısız. Beklenen: {expected_value}, Bulunan: {actual_value}"
            )

        cls._logger.info("Environment Handler başarıyla başlatıldı")
        return cls._initialized

    @classmethod
    def is_initialized(cls):
        return cls._initialized

    @classmethod
    def _get(cls, key: str, default: str = None):
        if not cls._initialized:
            cls._logger.error(
                "Get işlemi yapılmadan önce Environment Handler başlatılmalıdır",
                extra={"key": key}
            )
            raise EnvironmentNotInitializedError(
                message="Environment Handler başlatılmadan değer alınamaz"
            )

        return os.getenv(key, default)

    @classmethod
    def get_value_as_str(cls, key: str, default: str = None) -> str:
        try:
            value = cls._get(key, default)
            if value is None:
                return default
            return str(value).strip()
        except (QBitraException, EnvironmentError):
            raise
        except Exception as e:
            cls._logger.error(
                f"Environment değeri alınamadı: {key}",
                extra={"key": key, "target_type": "string", "error": str(e)},
                exc_info=True
            )
            raise EnvironmentTypeConversionError(
                key=key,
                target_type="string",
                message=f"'{key}' string'e dönüştürülemedi: {e}",
                cause=e
            ) from e

    @classmethod
    def get_value_as_int(cls, key: str, default: int = None) -> int:
        try:
            value = cls._get(key, default)
            if value is None:
                return default
            return int(value)
        except (QBitraException, EnvironmentError):
            raise
        except (ValueError, TypeError) as e:
            cls._logger.error(
                f"Environment değeri alınamadı: {key}",
                extra={"key": key, "target_type": "integer", "error": str(e)},
                exc_info=True
            )
            raise EnvironmentTypeConversionError(
                key=key,
                target_type="integer",
                message=f"'{key}' integer'a dönüştürülemedi: {e}",
                cause=e
            ) from e

    @classmethod
    def get_value_as_float(cls, key: str, default: float = None) -> float:
        try:
            value = cls._get(key, default)
            if value is None:
                return default
            return float(value)
        except (QBitraException, EnvironmentError):
            raise
        except (ValueError, TypeError) as e:
            cls._logger.error(
                f"Environment değeri alınamadı: {key}",
                extra={"key": key, "target_type": "float", "error": str(e)},
                exc_info=True
            )
            raise EnvironmentTypeConversionError(
                key=key,
                target_type="float",
                message=f"'{key}' float'a dönüştürülemedi: {e}",
                cause=e
            ) from e

    @classmethod
    def get_value_as_bool(cls, key: str, default: bool = None) -> bool:
        try:
            value = cls._get(key, None)

            if value is None:
                return default
            if isinstance(value, bool):
                return value
            if isinstance(value, (int, float)):
                return bool(value)
            if isinstance(value, str):
                normalized = value.strip().lower()
                if normalized in {"true", "1", "yes", "on"}:
                    return True
                if normalized in {"false", "0", "no", "off"}:
                    return False
            return default
        except (QBitraException, EnvironmentError):
            raise
        except Exception as e:
            cls._logger.error(
                f"Environment değeri alınamadı: {key}",
                extra={"key": key, "target_type": "boolean", "error": str(e)},
                exc_info=True
            )
            raise EnvironmentTypeConversionError(
                key=key,
                target_type="boolean",
                message=f"'{key}' boolean'a dönüştürülemedi: {e}",
                cause=e
            ) from e

    @classmethod
    def get_value_as_list(cls, key: str, default: list = None) -> list:
        try:
            value = cls._get(key, default)
            if value is None:
                return default
            if isinstance(value, list):
                return value
            return json.loads(value)
        except (QBitraException, EnvironmentError):
            raise
        except json.JSONDecodeError as e:
            cls._logger.error(
                f"Environment değeri alınamadı: {key}",
                extra={"key": key, "target_type": "list", "error": str(e)},
                exc_info=True
            )
            raise EnvironmentTypeConversionError(
                key=key,
                target_type="list",
                message=f"'{key}' list'e dönüştürülemedi (geçerli JSON değil): {e}",
                cause=e
            ) from e

    @classmethod
    def get_value_as_dict(cls, key: str, default: dict = None) -> dict:
        try:
            value = cls._get(key, default)
            if value is None:
                return default
            if isinstance(value, dict):
                return value
            return json.loads(value)
        except (QBitraException, EnvironmentError):
            raise
        except json.JSONDecodeError as e:
            cls._logger.error(
                f"Environment değeri alınamadı: {key}",
                extra={"key": key, "target_type": "dict", "error": str(e)},
                exc_info=True
            )
            raise EnvironmentTypeConversionError(
                key=key,
                target_type="dict",
                message=f"'{key}' dict'e dönüştürülemedi (geçerli JSON değil): {e}",
                cause=e
            ) from e