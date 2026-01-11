import json
from typing import Optional, Any

import redis
from redis.connection import ConnectionPool

from miniflow.core.exceptions import InternalError
from .configuration_handler import ConfigurationHandler


class RedisClient:
    """Redis client handler for managing Redis connections and operations."""
    _pool: Optional[ConnectionPool] = None
    _client: Optional[redis.Redis] = None
    _initialized: bool = False

    @classmethod
    def initialize(cls):
        """Initialize Redis connection pool and client."""
        if cls._initialized:
            return
        
        try:
            cls.load_redis_configurations()
            cls._client = redis.Redis(connection_pool=cls._pool)
            cls._client.ping()

            cls._initialized = True
        except redis.ConnectionError as e:
            # Get Redis connection details for error reporting
            host = ConfigurationHandler.get('Redis', 'host', fallback='localhost')
            port = ConfigurationHandler.get_int('Redis', 'port', fallback=6379)
            raise InternalError(
                component_name="redis_client",
                message=f"Failed to connect to Redis server: {str(e)}",
                error_details={
                    "host": host,
                    "port": port,
                    "error_type": type(e).__name__,
                    "original_error": str(e)
                }
            )
        except Exception as e:
            raise InternalError(
                component_name="redis_client",
                message=f"Unexpected error during Redis initialization: {str(e)}",
                error_details={
                    "error_type": type(e).__name__,
                    "original_error": str(e)
                }
            )
        
    @classmethod
    def load_redis_configurations(cls):
        """Load Redis configuration from configuration handler."""
        ConfigurationHandler.ensure_loaded()

        host = ConfigurationHandler.get('Redis', 'host', fallback='localhost')
        port = ConfigurationHandler.get_int('Redis', 'port', fallback=6379)
        db = ConfigurationHandler.get_int('Redis', 'db', fallback=0)
        password = ConfigurationHandler.get('Redis', 'password', fallback=None)
        max_connections = ConfigurationHandler.get_int('Redis', 'max_connections', fallback=50)
        socket_timeout = ConfigurationHandler.get_int('Redis', 'socket_timeout', fallback=5)
        socket_connect_timeout = ConfigurationHandler.get_int('Redis', 'socket_connect_timeout', fallback=5)
        decode_responses = ConfigurationHandler.get_bool('Redis', 'decode_responses', fallback=True)

        cls._pool = ConnectionPool(
            host=host,
            port=port,
            db=db,
            password=password,
            max_connections=max_connections,
            socket_timeout=socket_timeout,
            socket_connect_timeout=socket_connect_timeout,
            decode_responses=decode_responses
        )

    @classmethod
    def close(cls):
        """Close Redis connection pool."""
        if cls._pool:
            cls._pool.disconnect()
            cls._initialized = False

    @classmethod
    def set(cls, key: str, value: Any, ex: Optional[int] = None) -> bool:
        """Set a key-value pair in Redis with optional expiration."""
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        return cls._client.set(key, value, ex=ex)

    @classmethod
    def get(cls, key: str) -> Optional[Any]:
        """Get a value from Redis by key, automatically parsing JSON if applicable."""
        value = cls._client.get(key)
        if value is None:
            return None
        
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value

    @classmethod
    def delete(cls, *keys: str) -> int:
        """Delete one or more keys from Redis."""
        return cls._client.delete(*keys)

    @classmethod
    def exists(cls, key: str) -> bool:
        """Check if a key exists in Redis."""
        return bool(cls._client.exists(key))

    @classmethod
    def expire(cls, key: str, seconds: int) -> bool:
        """Set expiration time for a key in seconds."""
        return cls._client.expire(key, seconds)

    @classmethod
    def ttl(cls, key: str) -> int:
        """Get the remaining time to live of a key in seconds."""
        return cls._client.ttl(key)

    @classmethod
    def incr(cls, key: str, amount: int = 1) -> int:
        """Increment the value of a key by the specified amount."""
        return cls._client.incr(key, amount)

    @classmethod
    def decr(cls, key: str, amount: int = 1) -> int:
        """Decrement the value of a key by the specified amount."""
        return cls._client.decr(key, amount)

    @classmethod
    def keys(cls, pattern: str = "*") -> list:
        """Get all keys matching the specified pattern."""
        return cls._client.keys(pattern)

    @classmethod
    def flushdb(cls):
        """Flush all keys from the current database."""
        return cls._client.flushdb()