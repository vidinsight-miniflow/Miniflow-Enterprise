import pytest
import redis
import json
from unittest.mock import patch, MagicMock
from qbitra.utils.handlers.redis_handler import RedisClient
from qbitra.utils.handlers import ConfigurationHandler
from qbitra.core.exceptions import (
    RedisClientError,
    RedisOperationError,
    ExternalServiceConnectionError,
    ExternalServiceTimeoutError,
)

@pytest.fixture(autouse=True)
def reset_redis_client():
    """Reset RedisClient class variables before each test."""
    RedisClient._pool = None
    RedisClient._client = None
    RedisClient._initialized = False
    RedisClient._host = None
    RedisClient._port = None
    RedisClient._db = None
    yield
    if RedisClient._pool:
        RedisClient._pool.disconnect()
    RedisClient._pool = None
    RedisClient._client = None
    RedisClient._initialized = False

def test_load_success():
    """Test successful client loading and pool creation."""
    with patch.object(ConfigurationHandler, "ensure_loaded"), \
         patch.object(ConfigurationHandler, "get_value_as_str", return_value="localhost"), \
         patch.object(ConfigurationHandler, "get_value_as_int", return_value=6379), \
         patch.object(ConfigurationHandler, "get_value_as_bool", return_value=True), \
         patch("qbitra.utils.handlers.redis_handler.ConnectionPool") as mock_pool, \
         patch("redis.Redis") as mock_redis:
        
        RedisClient.load()
        
        assert RedisClient._initialized is True
        assert RedisClient._host == "localhost"
        assert RedisClient._port == 6379
        mock_pool.assert_called_once()
        mock_redis.assert_called_once()

def test_load_failure():
    """Test client loading failure."""
    with patch.object(ConfigurationHandler, "ensure_loaded", side_effect=Exception("Config Error")):
        with pytest.raises(RedisClientError) as exc:
            RedisClient.load()
        assert "başlatılamadı" in str(exc.value)

def test_init_success():
    """Test successful initialization with validation."""
    def mock_load():
        RedisClient._initialized = True

    with patch.object(RedisClient, "load", side_effect=mock_load), \
         patch.object(RedisClient, "test", return_value=(True, "localhost:6379/0")):
        
        success = RedisClient.init()
        assert success is True
        assert RedisClient.is_initialized() is True

def test_init_failure():
    """Test initialization failure when test fails."""
    with patch.object(RedisClient, "load"), \
         patch.object(RedisClient, "test", return_value=(False, None)):
        
        with pytest.raises(ExternalServiceConnectionError) as exc:
            RedisClient.init()
        assert "bağlanılamadı" in str(exc.value)

def test_ensure_initialized_error():
    """Test error when calling operation before initialization."""
    RedisClient._initialized = False
    with pytest.raises(RedisClientError) as exc:
        RedisClient.set("key", "value")
    assert "başlatılmadan işlem yapılamaz" in str(exc.value)

def test_set_get_string():
    """Test basic SET and GET operations with strings."""
    RedisClient._initialized = True
    RedisClient._client = MagicMock()
    
    # Test SET
    RedisClient._client.set.return_value = True
    assert RedisClient.set("key", "value") is True
    RedisClient._client.set.assert_called_once_with("key", "value", ex=None)
    
    # Test GET
    RedisClient._client.get.return_value = "value"
    assert RedisClient.get("key") == "value"

def test_set_get_json():
    """Test SET and GET operations with JSON objects."""
    RedisClient._initialized = True
    RedisClient._client = MagicMock()
    
    data = {"name": "QBitra", "version": 1}
    json_data = json.dumps(data)
    
    # Test SET JSON
    RedisClient.set("data", data)
    RedisClient._client.set.assert_called_once_with("data", json_data, ex=None)
    
    # Test GET JSON
    RedisClient._client.get.return_value = json_data
    assert RedisClient.get("data") == data

def test_delete_exists():
    """Test DELETE and EXISTS operations."""
    RedisClient._initialized = True
    RedisClient._client = MagicMock()
    
    RedisClient._client.exists.return_value = 1
    assert RedisClient.exists("key") is True
    
    RedisClient._client.delete.return_value = 1
    assert RedisClient.delete("key") == 1

def test_incr_decr():
    """Test atomic increment and decrement."""
    RedisClient._initialized = True
    RedisClient._client = MagicMock()
    
    RedisClient._client.incr.return_value = 101
    assert RedisClient.incr("counter", 1) == 101
    
    RedisClient._client.decr.return_value = 100
    assert RedisClient.decr("counter", 1) == 100

def test_hash_operations():
    """Test Redis hash (HSET, HGET, HGETALL) operations."""
    RedisClient._initialized = True
    RedisClient._client = MagicMock()
    
    # HSET Individual
    RedisClient.hset("myhash", "field", "value")
    RedisClient._client.hset.assert_called_with("myhash", "field", "value")
    
    # HSET Mapping with JSON
    mapping = {"f1": "v1", "f2": {"inner": "data"}}
    RedisClient.hset("myhash", mapping=mapping)
    # The actual call stringifies JSON values
    
    # HGET
    RedisClient._client.hget.return_value = json.dumps({"f": 1})
    assert RedisClient.hget("myhash", "field") == {"f": 1}
    
    # HGETALL
    RedisClient._client.hgetall.return_value = {"k1": "v1", "k2": json.dumps([1,2])}
    assert RedisClient.hgetall("myhash") == {"k1": "v1", "k2": [1,2]}

@pytest.mark.parametrize("exception_type, error_str, expected_qbitra_exc", [
    (redis.ConnectionError, "connection", ExternalServiceConnectionError),
    (TimeoutError, "timeout", ExternalServiceTimeoutError),
    (Exception, "random", RedisOperationError),
])
def test_handle_operation_exception_mapping(exception_type, error_str, expected_qbitra_exc):
    """Test that low-level Redis exceptions are correctly mapped."""
    with pytest.raises(expected_qbitra_exc):
        RedisClient._handle_operation_exception(
            exception_type(error_str), 
            "test_op", 
            key="test_key"
        )

def test_close_and_reload():
    """Test closing and reloading the client."""
    RedisClient._pool = MagicMock()
    RedisClient._initialized = True
    
    RedisClient.close()
    assert RedisClient._initialized is False
    RedisClient._pool.disconnect.assert_called_once()
    
    with patch.object(RedisClient, "load") as mock_load:
        RedisClient.reload()
        mock_load.assert_called_once()
