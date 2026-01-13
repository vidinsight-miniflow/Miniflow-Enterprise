import threading
import pytest
import time
from sqlalchemy.orm import Session
from qbitra.infrastructure.database.engine.manager import DatabaseManager
from tests.test_database.conftest import TestUser, Base

def test_race_conditions_multithreading(file_db_config):
    """Test concurrent database access from multiple threads."""
    manager = DatabaseManager()
    manager.initialize(file_db_config, force_reinitialize=True)
    manager.engine.create_tables(Base.metadata)
    
    def worker(thread_id: int):
        with manager.engine.session_context(auto_commit=True) as session:
            username = f"user_{thread_id}_{time.time()}"
            user = TestUser(username=username, email=f"{username}@test.com")
            session.add(user)
            # Give some time to other threads
            time.sleep(0.01)
            
    threads = []
    for i in range(10):
        t = threading.Thread(target=worker, args=(i,))
        threads.append(t)
        t.start()
        
    for t in threads:
        t.join()
        
    # Verify all records were created
    with manager.engine.session_context() as session:
        count = session.query(TestUser).count()
        assert count == 10

def test_session_leak_detection(manager):
    """Test that sessions are not leaked even if not explicitly closed (GC)."""
    engine = manager.engine
    
    def create_and_lose_session():
        session = engine.get_session()
        # Session is now 'active' and tracked
        assert engine.get_active_session_count() >= 1
        # session is lost here (goes out of scope)
    
    create_and_lose_session()
    
    # Force garbage collection to trigger weakref cleanup
    import gc
    gc.collect()
    
    # Wait a bit for the cleanup callback if necessary
    # (Though in CPython it should be immediate)
    
    # active_session_count has lazy cleanup, so call it a few times 
    # or just check if it eventually drops
    for _ in range(15): # Trigger lazy cleanup (counter % 10 == 0)
        count = engine.get_active_session_count()
        
    assert engine.get_active_session_count() == 0

def test_manager_reset_during_active_sessions(db_config):
    """Test that resetting the manager handles active sessions correctly."""
    manager = DatabaseManager()
    manager.initialize(db_config)
    
    session = manager.engine.get_session()
    assert manager.engine.get_active_session_count() == 1
    
    manager.reset(full_reset=True)
    
    # Should be closed and engine cleared
    try:
        session.execute(text("SELECT 1"))
        assert False, "Should have raised an error"
    except Exception:
        pass
    
    with pytest.raises(Exception): 
        _ = manager.engine
