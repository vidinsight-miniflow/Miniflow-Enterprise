import pytest
from qbitra.database.engine.manager import DatabaseManager, get_database_manager
from qbitra.core.exceptions import DatabaseManagerNotInitializedError, DatabaseManagerAlreadyInitializedError

def test_manager_singleton():
    """Test that DatabaseManager is a singleton."""
    m1 = DatabaseManager()
    m2 = DatabaseManager()
    assert m1 is m2

def test_manager_initialization(db_config):
    """Test manager initialization."""
    manager = DatabaseManager()
    assert not manager.is_initialized
    
    manager.initialize(db_config)
    assert manager.is_initialized
    assert manager.engine is not None

def test_manager_not_initialized_error():
    """Test error when accessing engine before initialization."""
    manager = DatabaseManager()
    with pytest.raises(DatabaseManagerNotInitializedError):
        _ = manager.engine

def test_manager_already_initialized_error(db_config):
    """Test error when initializing twice without force."""
    manager = DatabaseManager()
    manager.initialize(db_config)
    
    with pytest.raises(DatabaseManagerAlreadyInitializedError):
        manager.initialize(db_config)

def test_manager_force_reinitialize(db_config):
    """Test force re-initialization."""
    manager = DatabaseManager()
    manager.initialize(db_config)
    
    # Same engine before
    e1 = manager.engine
    
    manager.initialize(db_config, force_reinitialize=True)
    e2 = manager.engine
    
    assert e1 is not e2

def test_get_database_manager_helper(db_config):
    """Test the get_database_manager convenience function."""
    manager = get_database_manager(db_config)
    assert manager.is_initialized
    assert manager.engine.is_alive
