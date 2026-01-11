import pytest
import time
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError
from qbitra.database.engine.decorators import (
    with_session, with_transaction_session, with_readonly_session, with_retry_session
)
from qbitra.database.engine.manager import DatabaseManager
from qbitra.core.exceptions import DatabaseDecoratorSignatureError
from tests.test_database.conftest import TestUser

# Example functions to test decorators
@with_session()
def create_user_session(username: str, email: str, session: Session = None):
    user = TestUser(username=username, email=email)
    session.add(user)
    session.flush() # Ensure ID is assigned
    user_id = user.id # Access while session is active to avoid detached error
    return user_id, user

@with_transaction_session()
def atomic_operation(username: str, email: str, fail: bool = False, session: Session = None):
    user = TestUser(username=username, email=email)
    session.add(user)
    if fail:
        raise ValueError("Simulated failure")
    return user

@with_readonly_session()
def get_user_readonly(username: str, session: Session = None):
    user = session.query(TestUser).filter_by(username=username).first()
    if user:
        return user.id, user.username
    return None, None

def test_with_session_decorator(manager):
    """Test @with_session decorator."""
    user_id, user = create_user_session("dec_user", "dec@test.com")
    assert user_id is not None
    
    # Verify persistence
    with manager.engine.session_context() as session:
        db_user = session.query(TestUser).filter_by(username="dec_user").first()
        assert db_user is not None

def test_with_transaction_rollback(manager):
    """Test @with_transaction_session rollback on error."""
    try:
        atomic_operation("fail_txn", "fail@test.com", fail=True)
    except ValueError:
        pass
        
    with manager.engine.session_context() as session:
        db_user = session.query(TestUser).filter_by(username="fail_txn").first()
        assert db_user is None

def test_with_readonly_session(manager):
    """Test @with_readonly_session decorator."""
    # Pre-create user
    create_user_session("ready_user", "ready@test.com")
    
    user_id, username = get_user_readonly("ready_user")
    assert user_id is not None
    assert username == "ready_user"

def test_decorator_signature_validation():
    """Test that decorators validate function signatures."""
    with pytest.raises(DatabaseDecoratorSignatureError):
        @with_session()
        def invalid_func(username: str): # Missing 'session' param
            pass

def test_with_retry_session_success(manager):
    """Test @with_retry_session with a successful call."""
    attempts = 0
    
    @with_retry_session(max_attempts=3)
    def retryable_op(session: Session = None):
        nonlocal attempts
        attempts += 1
        return "success"
        
    result = retryable_op()
    assert result == "success"
    assert attempts == 1

def test_with_retry_session_fail_then_success(manager, monkeypatch):
    """Test @with_retry_session with initial failures."""
    attempts = 0
    
    @with_retry_session(max_attempts=3, delay=0.01)
    def retryable_op(session: Session = None):
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            # Simulate a deadlock/retryable error
            from sqlalchemy.exc import OperationalError
            # Note: _is_deadlock_error checks for specific strings/codes
            raise OperationalError("deadlock detected", None, None)
        return "finally success"
        
    result = retryable_op()
    assert result == "finally success"
    assert attempts == 3

class TestClassDecorators:
    """Test decorators used on class methods."""
    
    @with_session()
    def instance_method(self, name: str, session: Session = None):
        user = TestUser(username=name, email=f"{name}@test.com")
        session.add(user)
        session.flush()
        return user.id, user
        
    @classmethod
    @with_session()
    def class_method(cls, name: str, session: Session = None):
        user = TestUser(username=name, email=f"{name}@test.com")
        session.add(user)
        session.flush()
        return user.id, user

def test_class_decorators(manager):
    """Test using decorators on instance and class methods."""
    obj = TestClassDecorators()
    
    u1_id, u1 = obj.instance_method("instance_user")
    assert u1_id is not None
    
    u2_id, u2 = TestClassDecorators.class_method("class_user")
    assert u2_id is not None
