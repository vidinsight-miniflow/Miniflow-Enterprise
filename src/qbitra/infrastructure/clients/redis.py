import json
from typing import Optional, Any, List

import redis
from redis.connection import ConnectionPool

from qbitra.core.qbitra_logger import get_logger
from qbitra.core.exceptions import (
    RedisError,
    RedisClientError,
    RedisOperationError,
    ExternalServiceConnectionError,
    ExternalServiceTimeoutError,
)
from qbitra.utils.handlers.configuration_handler import ConfigurationHandler


class RedisClient:
    """Redis client handler for managing Redis connections and operations."""

    _pool: Optional[ConnectionPool] = None
    _client: Optional[redis.Redis] = None
    _initialized: bool = False
    # Infrastructure katmanı logger'ı (logs/infrastructure/redis/service.log)
    _logger = get_logger("redis", parent_folder="infrastructure")

    _host: str = None
    _port: int = None
    _db: int = None

    @classmethod
    def _load_configuration(cls):
        """Load Redis configuration from configuration handler."""
        ConfigurationHandler.ensure_loaded()

        cls._host = ConfigurationHandler.get_value_as_str("Redis", "host", fallback="localhost")
        cls._port = ConfigurationHandler.get_value_as_int("Redis", "port", fallback=6379)
        cls._db = ConfigurationHandler.get_value_as_int("Redis", "db", fallback=0)
        password = ConfigurationHandler.get_value_as_str("Redis", "password", fallback=None)
        max_connections = ConfigurationHandler.get_value_as_int("Redis", "max_connections", fallback=50)
        socket_timeout = ConfigurationHandler.get_value_as_int("Redis", "socket_timeout", fallback=5)
        socket_connect_timeout = ConfigurationHandler.get_value_as_int("Redis", "socket_connect_timeout", fallback=5)
        decode_responses = ConfigurationHandler.get_value_as_bool("Redis", "decode_responses", fallback=True)

        cls._pool = ConnectionPool(
            host=cls._host,
            port=cls._port,
            db=cls._db,
            password=password,
            max_connections=max_connections,
            socket_timeout=socket_timeout,
            socket_connect_timeout=socket_connect_timeout,
            decode_responses=decode_responses
        )
        cls._logger.debug(
            f"Redis connection pool oluşturuldu: {cls._host}:{cls._port}/{cls._db}",
            extra={"host": cls._host, "port": cls._port, "db": cls._db}
        )

    @classmethod
    def _handle_operation_exception(cls, e: Exception, operation: str, key: Optional[str] = None, **extra_context):
        """
        Standart hata yönetimi helper metodu.
        Original exception'ı cause olarak tutar, tipine göre uygun exception fırlatır.
        """
        error_str = str(e).lower()
        
        # Context bilgilerini hazırla
        context = {
            "operation": operation,
            "error": str(e),
            "error_type": type(e).__name__,
            **extra_context
        }
        if key:
            context["key"] = key
        
        cls._logger.error(
            f"Redis {operation} hatası",
            extra=context,
        )
        
        # Exception tipine göre uygun exception fırlat
        if isinstance(e, (redis.ConnectionError, ConnectionError)) or "connection" in error_str or "connect" in error_str:
            raise ExternalServiceConnectionError(
                service_name="Redis",
                operation_name=operation,
                message=f"Redis {operation} bağlantı hatası: {e}",
                cause=e
            ) from e
        elif isinstance(e, (TimeoutError,)) or "timeout" in error_str or "timed out" in error_str:
            raise ExternalServiceTimeoutError(
                service_name="Redis",
                operation_name=operation,
                message=f"Redis {operation} timeout oluştu: {e}",
                cause=e
            ) from e
        else:
            # Genel operation error - original exception cause olarak tutulur
            raise RedisOperationError(
                operation=operation,
                key=key,
                message=f"Redis {operation} işlemi başarısız: {e}",
                cause=e
            ) from e

    @classmethod
    def load(cls):
        """Load Redis connection pool and create client instance."""
        if cls._initialized:
            cls._logger.info("Redis client daha önce başlatılmış, tekrar başlatılamaz")
            return

        try:
            cls._load_configuration()
            cls._client = redis.Redis(connection_pool=cls._pool)
            cls._logger.debug("Redis client başarıyla yüklendi")
            cls._initialized = True
        except redis.ConnectionError as e:
            cls._logger.error(
                f"Redis sunucusuna bağlanılamadı: {e}",
                extra={"host": cls._host, "port": cls._port, "error": str(e)},
            )
            raise ExternalServiceConnectionError(
                service_name="Redis",
                operation_name="initialization",
                message=f"Redis sunucusuna bağlanılamadı ({cls._host}:{cls._port}): {e}",
                cause=e
            ) from e
        except Exception as e:
            cls._logger.error(
                f"Redis client başlatılırken hata oluştu: {e}",
                extra={"error": str(e), "error_type": type(e).__name__},
            )
            raise RedisClientError(
                operation="initialization",
                message=f"Redis client başlatılamadı: {e}",
                cause=e
            ) from e

    @classmethod
    def test(cls) -> tuple[bool, Optional[str]]:
        """Test Redis connection by sending a ping command."""
        if not cls._initialized:
            cls._logger.error("Test işlemi yapılmadan önce Redis client başlatılmalıdır")
            cls._logger.debug("Redis client başlatılıyor...")
            cls.load()

        try:
            ping_result = cls._client.ping()
            cls._logger.debug(f"Redis ping test: {ping_result}")
            return ping_result, f"{cls._host}:{cls._port}/{cls._db}"
        except redis.ConnectionError as e:
            cls._logger.error(
                f"Redis ping test başarısız: {e}",
                extra={"error": str(e)},
            )
            return False, None

    @classmethod
    def init(cls) -> bool:
        """Initialize Redis client with connection test."""
        if cls._initialized:
            cls._logger.info("Redis client daha önce başlatılmış, tekrar başlatılamaz")
            return True

        cls.load()

        success, connection_info = cls.test()
        if not success:
            cls._logger.error(
                "Redis bağlantı testi başarısız",
                extra={"host": cls._host, "port": cls._port, "db": cls._db}
            )
            raise ExternalServiceConnectionError(
                service_name="Redis",
                operation_name="test",
                message="Redis sunucusuna bağlanılamadı. Host ve port bilgilerini kontrol ediniz."
            )

        cls._logger.info(f"Redis client başarıyla başlatıldı: {connection_info}")
        return cls._initialized

    @classmethod
    def is_initialized(cls) -> bool:
        """Check if Redis client is initialized."""
        return cls._initialized

    @classmethod
    def _ensure_initialized(cls):
        """Ensure client is initialized before operations."""
        if not cls._initialized:
            cls._logger.error("Redis client başlatılmadan işlem yapılamaz")
            raise RedisClientError(
                operation="operation",
                message="Redis client başlatılmadan işlem yapılamaz"
            )

    @classmethod
    def close(cls):
        """Close Redis connection pool."""
        if cls._pool:
            cls._pool.disconnect()
            cls._client = None
            cls._initialized = False
            cls._logger.info("Redis bağlantısı kapatıldı")

    @classmethod
    def set(cls, key: str, value: Any, ex: Optional[int] = None) -> bool:
        """Set a key-value pair in Redis with optional expiration."""
        cls._ensure_initialized()
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            result = cls._client.set(key, value, ex=ex)
            cls._logger.debug(
                f"Redis SET: {key} (ex={ex})",
                extra={"key": key, "ex": ex, "success": result}
            )
            return result
        except RedisError:
            raise
        except Exception as e:
            cls._handle_operation_exception(e, "SET", key=key)

    @classmethod
    def get(cls, key: str) -> Optional[Any]:
        """Get a value from Redis by key, automatically parsing JSON if applicable."""
        cls._ensure_initialized()
        try:
            value = cls._client.get(key)
            if value is None:
                cls._logger.debug(f"Redis GET: {key} (not found)")
                return None
            try:
                parsed_value = json.loads(value)
                cls._logger.debug(f"Redis GET: {key} (JSON parsed)")
                return parsed_value
            except (json.JSONDecodeError, TypeError):
                cls._logger.debug(f"Redis GET: {key} (raw value)")
                return value
        except RedisError:
            raise
        except Exception as e:
            cls._handle_operation_exception(e, "GET", key=key)

    @classmethod
    def delete(cls, *keys: str) -> int:
        """Delete one or more keys from Redis."""
        cls._ensure_initialized()
        try:
            result = cls._client.delete(*keys)
            cls._logger.debug(
                f"Redis DELETE: {keys} ({result} silindi)",
                extra={"keys": keys, "deleted_count": result}
            )
            return result
        except RedisError:
            raise
        except Exception as e:
            cls._handle_operation_exception(e, "DELETE", key=", ".join(keys) if keys else None)

    @classmethod
    def exists(cls, key: str) -> bool:
        """Check if a key exists in Redis."""
        cls._ensure_initialized()
        try:
            result = bool(cls._client.exists(key))
            cls._logger.debug(f"Redis EXISTS: {key} = {result}")
            return result
        except RedisError:
            raise
        except Exception as e:
            cls._handle_operation_exception(e, "EXISTS", key=key)

    @classmethod
    def expire(cls, key: str, seconds: int) -> bool:
        """Set expiration time for a key in seconds."""
        cls._ensure_initialized()
        try:
            result = cls._client.expire(key, seconds)
            cls._logger.debug(
                f"Redis EXPIRE: {key} ({seconds}s)",
                extra={"key": key, "seconds": seconds, "success": result}
            )
            return result
        except RedisError:
            raise
        except Exception as e:
            cls._handle_operation_exception(e, "EXPIRE", key=key, seconds=seconds)

    @classmethod
    def ttl(cls, key: str) -> int:
        """Get the remaining time to live of a key in seconds."""
        cls._ensure_initialized()
        try:
            result = cls._client.ttl(key)
            cls._logger.debug(f"Redis TTL: {key} = {result}s")
            return result
        except RedisError:
            raise
        except Exception as e:
            cls._handle_operation_exception(e, "TTL", key=key)

    @classmethod
    def incr(cls, key: str, amount: int = 1) -> int:
        """Increment the value of a key by the specified amount."""
        cls._ensure_initialized()
        try:
            result = cls._client.incr(key, amount)
            cls._logger.debug(
                f"Redis INCR: {key} (+{amount}) = {result}",
                extra={"key": key, "amount": amount, "result": result}
            )
            return result
        except RedisError:
            raise
        except Exception as e:
            cls._handle_operation_exception(e, "INCR", key=key, amount=amount)

    @classmethod
    def decr(cls, key: str, amount: int = 1) -> int:
        """Decrement the value of a key by the specified amount."""
        cls._ensure_initialized()
        try:
            result = cls._client.decr(key, amount)
            cls._logger.debug(
                f"Redis DECR: {key} (-{amount}) = {result}",
                extra={"key": key, "amount": amount, "result": result}
            )
            return result
        except RedisError:
            raise
        except Exception as e:
            cls._handle_operation_exception(e, "DECR", key=key, amount=amount)

    @classmethod
    def keys(cls, pattern: str = "*") -> List[str]:
        """Get all keys matching the specified pattern."""
        cls._ensure_initialized()
        try:
            result = cls._client.keys(pattern)
            cls._logger.debug(f"Redis KEYS: pattern={pattern} (found {len(result)} keys)")
            return result
        except RedisError:
            raise
        except Exception as e:
            cls._handle_operation_exception(e, "KEYS", key=pattern)

    @classmethod
    def flushdb(cls) -> bool:
        """Flush all keys from the current database."""
        cls._ensure_initialized()
        try:
            result = cls._client.flushdb()
            cls._logger.warning(
                f"Redis FLUSHDB: Tüm keyler silindi (db={cls._db})",
                extra={"db": cls._db}
            )
            return result
        except RedisError:
            raise
        except Exception as e:
            cls._handle_operation_exception(e, "FLUSHDB", key=f"db={cls._db}")

    @classmethod
    def hset(cls, name: str, key: str = None, value: Any = None, mapping: dict = None) -> int:
        """Set hash field(s) in Redis."""
        cls._ensure_initialized()
        try:
            if mapping:
                mapping = {k: json.dumps(v) if isinstance(v, (dict, list)) else v for k, v in mapping.items()}
                result = cls._client.hset(name, mapping=mapping)
                cls._logger.debug(
                    f"Redis HSET: {name} (mapping, {len(mapping)} fields)",
                    extra={"hash_name": name, "fields_count": len(mapping), "result": result}
                )
            else:
                if isinstance(value, (dict, list)):
                    value = json.dumps(value)
                result = cls._client.hset(name, key, value)
                cls._logger.debug(
                    f"Redis HSET: {name}.{key}",
                    extra={"hash_name": name, "field": key, "result": result}
                )
            return result
        except RedisError:
            raise
        except Exception as e:
            cls._handle_operation_exception(e, "HSET", key=name)

    @classmethod
    def hget(cls, name: str, key: str) -> Optional[Any]:
        """Get a hash field value from Redis."""
        cls._ensure_initialized()
        try:
            value = cls._client.hget(name, key)
            if value is None:
                cls._logger.debug(f"Redis HGET: {name}.{key} (not found)")
                return None
            try:
                parsed_value = json.loads(value)
                cls._logger.debug(f"Redis HGET: {name}.{key} (JSON parsed)")
                return parsed_value
            except (json.JSONDecodeError, TypeError):
                cls._logger.debug(f"Redis HGET: {name}.{key} (raw value)")
                return value
        except RedisError:
            raise
        except Exception as e:
            cls._handle_operation_exception(e, "HGET", key=f"{name}.{key}")

    @classmethod
    def hgetall(cls, name: str) -> dict:
        """Get all hash fields and values from Redis."""
        cls._ensure_initialized()
        try:
            data = cls._client.hgetall(name)
            result = {}
            for k, v in data.items():
                try:
                    result[k] = json.loads(v)
                except (json.JSONDecodeError, TypeError):
                    result[k] = v
            cls._logger.debug(f"Redis HGETALL: {name} (found {len(result)} fields)")
            return result
        except RedisError:
            raise
        except Exception as e:
            cls._handle_operation_exception(e, "HGETALL", key=name)

    @classmethod
    def hdel(cls, name: str, *keys: str) -> int:
        """Delete hash field(s) from Redis."""
        cls._ensure_initialized()
        try:
            result = cls._client.hdel(name, *keys)
            cls._logger.debug(
                f"Redis HDEL: {name} ({keys}) ({result} silindi)",
                extra={"hash_name": name, "fields": keys, "deleted_count": result}
            )
            return result
        except RedisError:
            raise
        except Exception as e:
            cls._handle_operation_exception(e, "HDEL", key=name)

    @classmethod
    def get_connection_info(cls) -> dict:
        """Get current connection information."""
        cls._ensure_initialized()
        return {
            "host": cls._host,
            "port": cls._port,
            "db": cls._db,
            "initialized": cls._initialized
        }

    @classmethod
    def reload(cls):
        """Reload Redis client configuration and reconnect."""
        cls._logger.info("Redis client yeniden yükleniyor...")
        cls.close()
        cls.load()
        cls._logger.info("Redis client başarıyla yeniden yüklendi")
