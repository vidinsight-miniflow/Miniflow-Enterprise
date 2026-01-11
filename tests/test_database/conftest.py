import os
import pytest
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base

from qbitra.database.config import DatabaseConfig, DatabaseType
from qbitra.database.engine import DatabaseEngine, DatabaseManager, get_database_manager

Base = declarative_base()

class TestUser(Base):
    """Test model for database operations."""
    __tablename__ = "test_users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), nullable=False)

@pytest.fixture(scope="session")
def sqlite_path(tmp_path_factory):
    """Temporary SQLite database path."""
    db_path = tmp_path_factory.mktemp("db") / "test.db"
    return str(db_path)

@pytest.fixture
def db_config():
    """SQLite in-memory configuration."""
    return DatabaseConfig(
        db_type=DatabaseType.SQLITE,
        db_name="test_db",
        sqlite_path=":memory:"
    )

@pytest.fixture
def file_db_config(sqlite_path):
    """SQLite file-based configuration."""
    return DatabaseConfig(
        db_type=DatabaseType.SQLITE,
        db_name="test_file_db",
        sqlite_path=sqlite_path
    )

@pytest.fixture
def engine(db_config):
    """Initialized DatabaseEngine instance."""
    engine = DatabaseEngine(db_config)
    engine.start()
    engine.create_tables(Base.metadata)
    yield engine
    engine.stop()

@pytest.fixture(autouse=True)
def clean_manager():
    """Ensure DatabaseManager is reset before and after each test."""
    manager = DatabaseManager()
    manager.reset(full_reset=True)
    yield manager
    manager.reset(full_reset=True)

@pytest.fixture
def manager(db_config):
    """Initialized DatabaseManager instance."""
    manager = get_database_manager(db_config)
    manager.engine.create_tables(Base.metadata)
    return manager
