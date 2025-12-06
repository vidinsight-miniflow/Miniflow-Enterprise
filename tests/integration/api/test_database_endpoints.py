"""Test database endpoints."""

import pytest
from fastapi.testclient import TestClient
from tests.fixtures.endpoint_test_helpers import EndpointTester


class TestDatabaseEndpoints:
    """Test database endpoints."""
    
    def test_create_database_unauthorized(self, client: TestClient):
        """Test creating database without authentication."""
        tester = EndpointTester(client)
        database_data = {
            "name": "Test DB",
            "database_type": "POSTGRESQL",
            "host": "localhost",
            "port": 5432,
            "database_name": "testdb",
            "username": "user",
            "password": "pass"
        }
        response = tester.post("/frontend/workspaces/WSP-0000000000000001/databases", json=database_data)
        tester.assert_unauthorized(response)
    
    def test_get_database_unauthorized(self, client: TestClient):
        """Test getting database without authentication."""
        tester = EndpointTester(client)
        response = tester.get("/frontend/workspaces/WSP-0000000000000001/databases/DB-0000000000000001")
        tester.assert_unauthorized(response)
    
    def test_get_all_databases_unauthorized(self, client: TestClient):
        """Test getting all databases without authentication."""
        tester = EndpointTester(client)
        response = tester.get("/frontend/workspaces/WSP-0000000000000001/databases")
        tester.assert_unauthorized(response)
    
    def test_update_database_unauthorized(self, client: TestClient):
        """Test updating database without authentication."""
        tester = EndpointTester(client)
        database_data = {"name": "Updated DB"}
        response = tester.put("/frontend/workspaces/WSP-0000000000000001/databases/DB-0000000000000001", json=database_data)
        tester.assert_unauthorized(response)
    
    def test_update_test_status_unauthorized(self, client: TestClient):
        """Test updating test status without authentication."""
        tester = EndpointTester(client)
        status_data = {"test_status": "PASSED"}
        response = tester.post("/frontend/workspaces/WSP-0000000000000001/databases/DB-0000000000000001/test-status", json=status_data)
        tester.assert_unauthorized(response)
    
    def test_activate_database_unauthorized(self, client: TestClient):
        """Test activating database without authentication."""
        tester = EndpointTester(client)
        response = tester.post("/frontend/workspaces/WSP-0000000000000001/databases/DB-0000000000000001/activate", json={})
        tester.assert_unauthorized(response)
    
    def test_deactivate_database_unauthorized(self, client: TestClient):
        """Test deactivating database without authentication."""
        tester = EndpointTester(client)
        response = tester.post("/frontend/workspaces/WSP-0000000000000001/databases/DB-0000000000000001/deactivate", json={})
        tester.assert_unauthorized(response)
    
    def test_delete_database_unauthorized(self, client: TestClient):
        """Test deleting database without authentication."""
        tester = EndpointTester(client)
        response = tester.delete("/frontend/workspaces/WSP-0000000000000001/databases/DB-0000000000000001")
        tester.assert_unauthorized(response)

