import os
import sys
import pytest
from unittest.mock import patch
from configparser import ConfigParser

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from qbitra.infrastructure.database.config import DatabaseConfig, DatabaseType
from qbitra.infrastructure.database.engine import DatabaseManager, get_database_manager
from qbitra.infrastructure.database.models import BaseModel

# Initialize ConfigurationHandler before any imports that depend on it
from qbitra.utils.handlers.configuration_handler import ConfigurationHandler
from qbitra.utils.handlers.environment_handler import EnvironmentHandler

# Mock EnvironmentHandler for JWT_SECRET_KEY
def mock_get_value_as_str(key: str, default: str = None) -> str:
    if key == "JWT_SECRET_KEY":
        return "test_jwt_secret_key_for_testing_purposes_only_min_32_chars"
    return "dev"

# Initialize EnvironmentHandler
with patch("pathlib.Path.exists", return_value=True), \
     patch("dotenv.load_dotenv"):
    EnvironmentHandler._initialized = False
    EnvironmentHandler._env_path = None
    # Mock environment variables
    import os
    os.environ["JWT_SECRET_KEY"] = "test_jwt_secret_key_for_testing_purposes_only_min_32_chars"
    os.environ["APP_ENV"] = "dev"
    EnvironmentHandler._initialized = True

with patch("qbitra.utils.handlers.environment_handler.EnvironmentHandler.is_initialized", return_value=True), \
     patch("qbitra.utils.handlers.environment_handler.EnvironmentHandler.get_value_as_str", side_effect=mock_get_value_as_str), \
     patch("pathlib.Path.exists", return_value=True), \
     patch("configparser.ConfigParser.read"):
    ConfigurationHandler._initialized = False
    ConfigurationHandler._parser = ConfigParser()
    ConfigurationHandler._parser.add_section("Test")
    ConfigurationHandler._parser.set("Test", "value", "ThisKeyIsForConfigTest")
    ConfigurationHandler._parser.add_section("AUTH")
    ConfigurationHandler._parser.set("AUTH", "max_active_sessions", "5")
    ConfigurationHandler._initialized = True


@pytest.fixture(scope="session", autouse=True)
def init_configuration_handler():
    """Ensure ConfigurationHandler is initialized (already done at module level)."""
    yield
    # Cleanup if needed
    ConfigurationHandler._initialized = False
    ConfigurationHandler._parser = ConfigParser()


@pytest.fixture
def sqlite_path(tmp_path):
    db_path = tmp_path / "test_services.db"
    return str(db_path)


@pytest.fixture
def db_config(sqlite_path):
    return DatabaseConfig(
        db_type=DatabaseType.SQLITE,
        db_name="test_services_db",
        sqlite_path=sqlite_path
    )




@pytest.fixture(autouse=True)
def clean_manager():
    manager = DatabaseManager()
    manager.reset(full_reset=True)
    yield manager
    manager.reset(full_reset=True)


@pytest.fixture
def manager(db_config):
    manager = get_database_manager(db_config)
    manager.engine.create_tables(BaseModel.metadata)
    yield manager
    manager.engine.drop_tables(BaseModel.metadata)
