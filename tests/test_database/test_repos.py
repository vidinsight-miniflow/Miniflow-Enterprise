import pytest
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from qbitra.database.repos.base import BaseRepository, handle_exceptions
from qbitra.database.repos.bulk import BulkRepository
from qbitra.database.repos.extra import ExtraRepository
from qbitra.core.exceptions import (
    DatabaseQueryError,
    DatabaseValidationError,
    DatabaseResourceNotFoundError,
)
from tests.test_database.conftest import TestUser, TestParent, TestChild, TestTypes, Base

# ==================== BaseRepository Tests ====================

def test_base_repository_crud(manager):
    """Test basic CRUD operations in BaseRepository."""
    repo = BaseRepository(TestUser)
    engine = manager.engine
    
    with engine.session_context(auto_commit=True) as session:
        # Create
        user = repo.create(session, username="repo_user", email="repo@base.com")
        user_id = user.id
        assert user.username == "repo_user"
        
        # Get
        found = repo.get(session, user_id)
        assert found.username == "repo_user"
        
        # Update
        updated = repo.update(session, user_id, email="new@base.com")
        assert updated.email == "new@base.com"
        
        # Exists
        assert repo.exists(session, user_id) is True
        
        # Delete
        repo.delete(session, user_id)
        assert repo.get(session, user_id) is None
        assert repo.exists(session, user_id) is False

def test_base_repository_not_found(manager):
    """Test behavior when record is not found."""
    repo = BaseRepository(TestUser)
    engine = manager.engine
    
    with engine.session_context() as session:
        assert repo.get(session, "NON-EXISTENT") is None
        with pytest.raises(DatabaseResourceNotFoundError):
            repo.get_or_raise(session, "NON-EXISTENT")

def test_base_repository_soft_delete(manager):
    """Test soft delete and restore in BaseRepository."""
    repo = BaseRepository(TestParent)
    engine = manager.engine
    
    with engine.session_context(auto_commit=True) as session:
        p = repo.create(session, name="Parent Soft")
        pid = p.id
        
        # Soft Delete
        repo.soft_delete(session, pid)
        assert repo.get(session, pid) is None # Default filters out deleted
        assert repo.get(session, pid, include_deleted=True) is not None
        
        # Restore
        repo.restore(session, pid)
        assert repo.get(session, pid) is not None

def test_base_repository_exception_mapping(manager):
    """Test that SQLAlchemy exceptions are mapped to custom exceptions."""
    repo = BaseRepository(TestUser)
    engine = manager.engine
    
    with engine.session_context(auto_commit=True) as session:
        repo.create(session, username="duplicate", email="1@t.com")
        
        # IntegrityError (Duplicate) -> DatabaseValidationError
        with pytest.raises(DatabaseValidationError):
            repo.create(session, username="duplicate", email="2@t.com")

# ==================== BulkRepository Tests ====================

def test_bulk_repository_operations(manager):
    """Test batch operations in BulkRepository."""
    repo = BulkRepository(TestUser)
    engine = manager.engine
    
    with engine.session_context(auto_commit=True) as session:
        # Bulk Create
        records = [
            {"username": f"bulk_{i}", "email": f"b{i}@t.com"}
            for i in range(10)
        ]
        created = repo.bulk_create(session, records)
        assert len(created) == 10
        
        # Bulk Update
        updates = [
            {"id": c.id, "email": "updated@bulk.com"}
            for c in created[:5]
        ]
        count = repo.bulk_update(session, updates)
        assert count == 5
        
        # Verify
        users = repo.get_all(session, limit=5)
        for u in users:
            assert u.email == "updated@bulk.com"

def test_bulk_soft_delete_and_restore(manager):
    """Test bulk soft delete operations."""
    repo = BulkRepository(TestParent)
    engine = manager.engine
    
    with engine.session_context(auto_commit=True) as session:
        records = [{"name": f"P{i}"} for i in range(5)]
        created = repo.bulk_create(session, records)
        ids = [c.id for c in created]
        
        # Bulk Soft Delete
        affected = repo.bulk_soft_delete(session, ids)
        assert affected == 5
        assert repo.count(session) == 0
        assert repo.count(session, include_deleted=True) == 5
        
        # Bulk Restore
        repo.bulk_restore(session, ids)
        assert repo.count(session) == 5
        assert repo.count(session) == 5 # Should be 5 after restoring

# ==================== ExtraRepository Tests ====================

def test_extra_repository_pagination(manager):
    """Test pagination logic."""
    repo = ExtraRepository(TestUser)
    bulk_repo = BulkRepository(TestUser)
    engine = manager.engine
    
    with engine.session_context(auto_commit=True) as session:
        # Create 25 users
        bulk_repo.bulk_create(session, [{"username": f"u{i}", "email": "e"} for i in range(25)])
        
        # Page 1
        res1 = repo.paginate(session, page=1, per_page=10)
        assert len(res1["items"]) == 10
        assert res1["total"] == 25
        assert res1["pages"] == 3
        assert res1["has_next"] is True
        
        # Page 3
        res3 = repo.paginate(session, page=3, per_page=10)
        assert len(res3["items"]) == 5
        assert res3["has_prev"] is True
        assert res3["has_next"] is False

def test_extra_repository_atomic_adjust(manager):
    """Test atomic increment/decrement."""
    # We'll use TestTypes and its int_col
    repo = ExtraRepository(TestTypes)
    engine = manager.engine
    
    with engine.session_context(auto_commit=True) as session:
        item = repo.create(session, int_col=10)
        iid = item.id
        
        # Increment
        repo.increment(session, iid, "int_col", 5)
        updated = repo.get(session, iid)
        assert updated.int_col == 15
        
        # Decrement
        repo.decrement(session, iid, "int_col", 3)
        updated = repo.get(session, iid)
        assert updated.int_col == 12
        
        # Decrement with negative protection
        with pytest.raises(DatabaseValidationError) as exc:
            repo.decrement(session, iid, "int_col", 20, allow_negative=False)
        assert "Insufficient" in str(exc.value)

def test_extra_repository_aggregates(manager):
    """Test aggregate functions sum, avg, min_max."""
    repo = ExtraRepository(TestTypes)
    bulk_repo = BulkRepository(TestTypes)
    engine = manager.engine
    
    with engine.session_context(auto_commit=True) as session:
        bulk_repo.bulk_create(session, [
            {"int_col": 10},
            {"int_col": 20},
            {"int_col": 30}
        ])
        
        # Expire session to ensure we fetch from DB
        session.expire_all()
        
        assert repo.sum(session, "int_col") == 60
        assert repo.avg(session, "int_col") == 20
        assert repo.min_max(session, "int_col") == (10, 30)

def test_extra_repository_find(manager):
    """Test find and find_one with filters."""
    repo = ExtraRepository(TestUser)
    engine = manager.engine
    
    with engine.session_context(auto_commit=True) as session:
        repo.create(session, username="search_me", email="found@t.com")
        
        found = repo.find_one(session, username="search_me")
        assert found is not None
        assert found.email == "found@t.com"
        
        many = repo.find(session, email="found@t.com")
        assert len(many) == 1
