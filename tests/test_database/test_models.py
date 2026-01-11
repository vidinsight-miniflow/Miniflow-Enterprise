import pytest
from datetime import datetime, date
from decimal import Decimal
import uuid
import json
from sqlalchemy.orm import Session
from qbitra.database.models.serializations import model_to_dict, models_to_list, model_to_json
from tests.test_database.conftest import TestUser, TestParent, TestChild, TestTypes, MyEnum, Base

def test_base_model_id_generation():
    """Test prefix-based ID generation in BaseModel."""
    user = TestUser(username="prefix_test", email="test@test.com")
    assert user.id is None # Not generated until flushed or accessed if default is set
    
    # Force ID generation by calling the class method directly or accessing property if configured
    generated_id = TestUser._generate_id()
    assert generated_id.startswith("USR-")
    assert len(generated_id) == 20 # 3(prefix) + 1(dash) + 16(uuid)

def test_base_model_prefix_validation():
    """Test that prefixes must be exactly 3 characters."""
    class BadPrefix(Base):
        __tablename__ = "bad_prefix"
        __prefix__ = "LONGPREFIX"
    
    with pytest.raises(ValueError) as exc:
        BadPrefix._generate_id()
    assert "must be exactly 3 characters" in str(exc.value)

def test_mixins_logic(manager):
    """Test Timestamp, SoftDelete, and Audit mixins."""
    engine = manager.engine
    engine.create_tables(Base.metadata)
    
    with engine.session_context(auto_commit=True) as session:
        parent = TestParent(name="Parent 1", created_by="admin")
        session.add(parent)
        session.flush()
        
        # Verify TimestampMixin
        assert isinstance(parent.created_at, datetime)
        assert isinstance(parent.updated_at, datetime)
        
        # Verify AuditMixin
        assert parent.created_by == "admin"
        
        # Verify SoftDeleteMixin Initial
        assert parent.is_deleted is False
        assert parent.deleted_at is None
        
        # Test soft delete
        parent.soft_delete()
        assert parent.is_deleted is True
        assert parent.deleted_at is not None
        
        # Test restore
        parent.restore()
        assert parent.is_deleted is False
        assert parent.deleted_at is None

def test_serialization_all_types():
    """Test model_to_dict with every supported type including UUID, bytes, and containers."""
    dt = datetime(2023, 1, 1, 12, 0, 0)
    d = date(2023, 1, 1)
    u = uuid.uuid4()
    b = b"hello world"
    
    item = TestTypes(
        string_col="text",
        int_col=123,
        float_col=45.67,
        bool_col=True,
        dt_col=dt,
        d_col=d,
        num_col=Decimal("100.50"),
        enum_col=MyEnum.VALUE1,
        uuid_col=u,
        bytes_col=b
    )
    
    # Manually attach extra fields that might not be in __table__.columns 
    # but could be present on the instance (e.g. dynamic attributes)
    item.dict_col = {"key": "value"}
    item.set_col = {1, 2, 3}
    item.none_col = None
    
    # Test fallback object
    class DummyObj:
        def __init__(self): self.foo = "bar"
        def __str__(self): return "Dummy" 
    item.obj_col = DummyObj()
    
    # We need to mock __table__.columns behavior if we want model_to_dict 
    # to pick up these dynamic ones, OR just rely on fact that serializations.py 
    # iterates over table columns. Let's verify the table-column based logic first.
    
    item.id = "TYP-1"
    result = model_to_dict(item)
    
    assert result["string_col"] == "text"
    assert result["int_col"] == 123
    assert result["float_col"] == 45.67
    assert result["bool_col"] is True
    assert result["dt_col"] == dt.isoformat()
    assert result["d_col"] == d.isoformat()
    assert result["num_col"] == 100.5
    assert result["enum_col"] == "v1"
    assert result["uuid_col"] == str(u)
    assert result["bytes_col"] == "hello world"
    
    # Test the standalone _serialize_value function for containers and fallback
    from qbitra.database.models.serializations import _serialize_value
    assert _serialize_value({"a": 1}) == {"a": 1}
    assert _serialize_value({1, 2}) == [1, 2] or _serialize_value({1, 2}) == [2, 1]
    assert _serialize_value(None) is None
    assert _serialize_value(DummyObj()) == "Dummy"

def test_serialization_exclusions():
    """Test the exclude parameter in model_to_dict."""
    user = TestUser(username="excl_test", email="excl@test.com")
    user.id = "USR-123"
    
    result = model_to_dict(user, exclude=["email", "id"])
    assert "username" in result
    assert "email" not in result
    assert "id" not in result
    assert "_sa_instance_state" not in result

def test_serialization_relationships(manager):
    """Test relationship serialization and max_depth."""
    engine = manager.engine
    engine.create_tables(Base.metadata)
    
    with engine.session_context(auto_commit=True) as session:
        parent = TestParent(name="Parent", id="PAR-1")
        child1 = TestChild(name="Child 1", id="CHI-1", parent=parent)
        child2 = TestChild(name="Child 2", id="CHI-2", parent=parent)
        session.add_all([parent, child1, child2])
        session.flush()
        
        # Test serialization WITH relationships
        # We use a fresh dict to avoid detached session issues if needed, 
        # but here we are in the context.
        res_depth_1 = model_to_dict(parent, include_relationships=True, max_depth=1)
        assert res_depth_1["name"] == "Parent"
        assert len(res_depth_1["children"]) == 2
        assert res_depth_1["children"][0]["name"] in ["Child 1", "Child 2"]
        # In depth 1, children should NOT have their parent serialized again (circular) 
        # or it should be None if visited.
        assert "parent" not in res_depth_1["children"][0] or res_depth_1["children"][0]["parent"] is None

def test_serialization_circular_references():
    """Test that circular references return None instead of recursing."""
    c1 = TestChild(name="C1", id="CHI-1")
    c2 = TestChild(name="C2", id="CHI-2")
    c1.related_to = c2
    c2.related_to = c1 # Circular!
    
    # Should not crash
    result = model_to_dict(c1, include_relationships=True, max_depth=5)
    
    assert result["name"] == "C1"
    assert result["related_to"]["name"] == "C2"
    # The back-link CHI-2 -> CHI-1 should be None because CHI-1 is already visited
    assert result["related_to"]["related_to"] is None

def test_serialization_bulk_and_json():
    """Test models_to_list and model_to_json."""
    users = [
        TestUser(username=f"u{i}", email=f"u{i}@t.com", id=f"USR-{i}")
        for i in range(3)
    ]
    
    # Bulk
    bulk_res = models_to_list(users)
    assert len(bulk_res) == 3
    assert bulk_res[0]["username"] == "u0"
    
    # JSON
    json_str = model_to_json(users[0], indent=2)
    data = json.loads(json_str)
    assert data["username"] == "u0"
    assert "  \"username\": \"u0\"" in json_str # check indent
