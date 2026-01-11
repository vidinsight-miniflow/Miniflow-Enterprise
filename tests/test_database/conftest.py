import os
import pytest
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Date, Numeric, Enum, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, Session

from qbitra.database.config import DatabaseConfig, DatabaseType
from qbitra.database.engine import DatabaseEngine, DatabaseManager, get_database_manager

from qbitra.database.models.base import BaseModel
from qbitra.database.models.mixins import TimestampMixin, SoftDeleteMixin, AuditMixin
import enum

# Use BaseModel as the base for new tests
Base = BaseModel

# Guard against multiple definitions which cause registry conflicts in SQLA 2.0
if "TestUser" not in Base.registry._class_registry:
    class TestUser(Base):
        """Test model for database operations."""
        __tablename__ = "test_users"
        __table_args__ = {"extend_existing": True}
        __prefix__ = "USR"
        username = Column(String(50), unique=True)
        email = Column(String(100))

    class TestParent(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
        __tablename__ = "test_parents"
        __table_args__ = {"extend_existing": True}
        __prefix__ = "PAR"
        name = Column(String(50))
        children = relationship("TestChild", back_populates="parent", cascade="all, delete-orphan")

    class TestChild(Base):
        __tablename__ = "test_children"
        __table_args__ = {"extend_existing": True}
        __prefix__ = "CHI"
        name = Column(String(50))
        parent_id = Column(String(20), ForeignKey("test_parents.id"))
        parent = relationship("TestParent", back_populates="children")
        
        # Self-referential for circular reference testing
        related_to_id = Column(String(20), ForeignKey("test_children.id"))
        related_to = relationship("TestChild", remote_side="TestChild.id")

    class MyEnum(enum.Enum):
        VALUE1 = "v1"
        VALUE2 = "v2"

    class TestTypes(Base):
        __tablename__ = "test_types"
        __table_args__ = {"extend_existing": True}
        __prefix__ = "TYP"
        string_col = Column(String(50))
        int_col = Column(Integer)
        float_col = Column(Float)
        bool_col = Column(Boolean)
        dt_col = Column(DateTime)
        d_col = Column(Date)
        num_col = Column(Numeric(10, 2))
        enum_col = Column(Enum(MyEnum))
        # Add fields for extra types testing (values can be set even if not fully mapped in all DBs)
        bytes_col = Column(String(255)) # Store as string but will set as bytes in test
        uuid_col = Column(String(36))   # Store as string but will set as UUID object
else:
    # Use existing classes if already registered
    TestUser = Base.registry._class_registry["TestUser"]
    TestParent = Base.registry._class_registry["TestParent"]
    TestChild = Base.registry._class_registry["TestChild"]
    TestTypes = Base.registry._class_registry["TestTypes"]
    # Enum is not in registry, but we can assume it's defined if others are
    import enum
    class MyEnum(enum.Enum):
        VALUE1 = "v1"
        VALUE2 = "v2"

@pytest.fixture
def sqlite_path(tmp_path):
    """Temporary SQLite database path (function scope for isolation)."""
    db_path = tmp_path / "test.db"
    return str(db_path)

@pytest.fixture
def db_config(sqlite_path):
    """SQLite file-based configuration for better isolation than :memory:."""
    return DatabaseConfig(
        db_type=DatabaseType.SQLITE,
        db_name="test_db",
        sqlite_path=sqlite_path
    )

@pytest.fixture
def file_db_config(sqlite_path):
    """Same as db_config but explicitly named."""
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
    """Initialized DatabaseManager instance with fresh tables."""
    manager = get_database_manager(db_config)
    # Ensure tables are created for the fresh DB
    manager.engine.create_tables(Base.metadata)
    return manager
