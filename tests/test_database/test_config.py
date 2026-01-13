import pytest
from qbitra.infrastructure.database.config import DatabaseConfig, EngineConfig, DatabaseType
from qbitra.infrastructure.database.config.factories import get_sqlite_config, get_postgresql_config, get_mysql_config
from qbitra.core.exceptions import DatabaseValidationError

def test_database_config_init():
    """Test basic DatabaseConfig initialization."""
    config = DatabaseConfig(
        db_type=DatabaseType.SQLITE,
        db_name="test_db",
        sqlite_path="test.db"
    )
    assert config.db_name == "test_db"
    assert config.db_type == DatabaseType.SQLITE
    assert config.sqlite_path == "test.db"

def test_database_config_validation():
    """Test DatabaseConfig field validation."""
    # Invalid port
    with pytest.raises(DatabaseValidationError) as exc:
        DatabaseConfig(db_type=DatabaseType.POSTGRESQL, db_name="db", port="invalid")
    assert "port" in str(exc.value)

    # Missing username for MySQL (checked before host/port in requires_credentials)
    with pytest.raises(DatabaseValidationError) as exc:
        DatabaseConfig(db_type=DatabaseType.MYSQL, db_name="db", host="localhost", username="")
    assert "username" in str(exc.value)

    # Missing host for PostgreSQL (checked after username)
    with pytest.raises(DatabaseValidationError) as exc:
        DatabaseConfig(db_type=DatabaseType.POSTGRESQL, db_name="db", username="u", password="p", host="")
    assert "host" in str(exc.value)

def test_engine_config_validation():
    """Test EngineConfig field validation."""
    with pytest.raises(DatabaseValidationError) as exc:
        EngineConfig(pool_size=-1)
    assert "pool_size" in str(exc.value)

    config = EngineConfig(pool_size=20)
    assert config.pool_size == 20

def test_connection_string_generation():
    """Test SQLAlchemy connection string generation."""
    # SQLite
    sqlite_config = DatabaseConfig(db_type=DatabaseType.SQLITE, sqlite_path="data.db")
    assert sqlite_config.get_connection_string() == "sqlite:///data.db"
    
    # SQLite In-memory
    memory_config = DatabaseConfig(db_type=DatabaseType.SQLITE, sqlite_path=":memory:")
    assert "sqlite:///file::memory:" in memory_config.get_connection_string()

    # PostgreSQL
    pg_config = DatabaseConfig(
        db_type=DatabaseType.POSTGRESQL,
        db_name="mydb",
        host="localhost",
        port=5432,
        username="user",
        password="pass"
    )
    conn_str = pg_config.get_connection_string()
    # Password might be masked as ***
    assert "postgresql://" in conn_str
    assert "@localhost:5432/mydb" in conn_str

def test_config_factories():
    """Test convenience factory functions."""
    sqlite = get_sqlite_config("my.db")
    assert sqlite.db_type == DatabaseType.SQLITE
    assert sqlite.sqlite_path == "my.db"

    pg = get_postgresql_config(database_name="pgdb", host="remotedb")
    assert pg.db_type == DatabaseType.POSTGRESQL
    assert pg.db_name == "pgdb"
    assert pg.host == "remotedb"
    assert pg.port == 5432
