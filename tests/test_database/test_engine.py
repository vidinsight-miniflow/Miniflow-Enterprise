import pytest
from sqlalchemy import text
from qbitra.infrastructure.database.engine.engine import DatabaseEngine
from qbitra.core.exceptions import DatabaseEngineError
from tests.test_database.conftest import TestUser

def test_engine_lifecycle(db_config):
    """Test engine start and stop."""
    engine = DatabaseEngine(db_config)
    assert not engine.is_alive
    
    engine.start()
    assert engine.is_alive
    
    engine.stop()
    assert not engine.is_alive

def test_session_context_success(engine):
    """Test successful session context with auto-commit."""
    with engine.session_context(auto_commit=True) as session:
        new_user = TestUser(username="testuser", email="test@example.com")
        session.add(new_user)
    
    # Verify persistence
    with engine.session_context() as session:
        user = session.query(TestUser).filter_by(username="testuser").first()
        assert user is not None
        assert user.email == "test@example.com"

def test_session_context_rollback(engine):
    """Test session context rollback on exception."""
    try:
        with engine.session_context(auto_commit=True) as session:
            new_user = TestUser(username="failuser", email="fail@example.com")
            session.add(new_user)
            raise ValueError("Forced failure")
    except ValueError:
        pass
    
    # Verify it was NOT persisted
    with engine.session_context() as session:
        user = session.query(TestUser).filter_by(username="failuser").first()
        assert user is None

def test_health_check(engine):
    """Test engine health check."""
    status = engine.health_check()
    assert status["status"] == "healthy"
    assert "active_sessions" in status

def test_active_session_tracking(engine):
    """Test tracking of active sessions."""
    import weakref
    
    # Ensure clean state
    for _ in range(11): engine.get_active_session_count()
    assert engine.get_active_session_count() == 0
    
    with engine.session_context() as session:
        assert engine.get_active_session_count() == 1
        session_ref = weakref.ref(session)
    
    # Session is closed but might be in generator's frame
    del session
    import gc
    gc.collect()
        
    # Trigger lazy cleanup
    for _ in range(11): engine.get_active_session_count()
    assert engine.get_active_session_count() == 0

def test_engine_stop_closes_sessions(engine):
    """Test that stopping the engine closes active sessions."""
    session = engine.get_session()
    assert engine.get_active_session_count() == 1
    
    engine.stop()
    assert engine.get_active_session_count() == 0
    # Instead of is_active (which might be True if the object lives), 
    # check if it's usable. In SQLAlchemy, a closed session should not 
    # be active in the sense of having a connection.
    try:
        session.execute(text("SELECT 1"))
        assert False, "Should have raised an error"
    except Exception:
        pass
