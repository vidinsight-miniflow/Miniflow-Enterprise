"""Test node endpoints."""

import pytest
from fastapi.testclient import TestClient
from tests.fixtures.endpoint_test_helpers import EndpointTester


class TestNodeEndpoints:
    """Test node endpoints."""
    
    def test_create_node_unauthorized(self, client: TestClient):
        """Test creating node without authentication."""
        tester = EndpointTester(client)
        node_data = {
            "name": "Test Node",
            "node_type": "SCRIPT",
            "script_id": "SCR-0000000000000001"
        }
        response = tester.post("/frontend/workspaces/WSP-0000000000000001/workflows/WFL-0000000000000001/nodes", json=node_data)
        tester.assert_unauthorized(response)
    
    def test_get_node_unauthorized(self, client: TestClient):
        """Test getting node without authentication."""
        tester = EndpointTester(client)
        response = tester.get("/frontend/workspaces/WSP-0000000000000001/workflows/WFL-0000000000000001/nodes/NOD-0000000000000001")
        tester.assert_unauthorized(response)
    
    def test_get_node_form_schema_unauthorized(self, client: TestClient):
        """Test getting node form schema without authentication."""
        tester = EndpointTester(client)
        response = tester.get("/frontend/workspaces/WSP-0000000000000001/workflows/WFL-0000000000000001/nodes/NOD-0000000000000001/form-schema")
        tester.assert_unauthorized(response)
    
    def test_get_all_nodes_unauthorized(self, client: TestClient):
        """Test getting all nodes without authentication."""
        tester = EndpointTester(client)
        response = tester.get("/frontend/workspaces/WSP-0000000000000001/workflows/WFL-0000000000000001/nodes")
        tester.assert_unauthorized(response)
    
    def test_update_node_unauthorized(self, client: TestClient):
        """Test updating node without authentication."""
        tester = EndpointTester(client)
        node_data = {"name": "Updated Node"}
        response = tester.put("/frontend/workspaces/WSP-0000000000000001/workflows/WFL-0000000000000001/nodes/NOD-0000000000000001", json=node_data)
        tester.assert_unauthorized(response)
    
    def test_update_input_params_unauthorized(self, client: TestClient):
        """Test updating input params without authentication."""
        tester = EndpointTester(client)
        params_data = {"input_params": {"key": "value"}}
        response = tester.put("/frontend/workspaces/WSP-0000000000000001/workflows/WFL-0000000000000001/nodes/NOD-0000000000000001/input-params", json=params_data)
        tester.assert_unauthorized(response)
    
    def test_sync_input_values_unauthorized(self, client: TestClient):
        """Test syncing input values without authentication."""
        tester = EndpointTester(client)
        sync_data = {"input_schema": {"type": "object"}}
        response = tester.put("/frontend/workspaces/WSP-0000000000000001/workflows/WFL-0000000000000001/nodes/NOD-0000000000000001/sync-input-values", json=sync_data)
        tester.assert_unauthorized(response)
    
    def test_reset_input_params_unauthorized(self, client: TestClient):
        """Test resetting input params without authentication."""
        tester = EndpointTester(client)
        response = tester.post("/frontend/workspaces/WSP-0000000000000001/workflows/WFL-0000000000000001/nodes/NOD-0000000000000001/reset-input-params", json={})
        tester.assert_unauthorized(response)
    
    def test_delete_node_unauthorized(self, client: TestClient):
        """Test deleting node without authentication."""
        tester = EndpointTester(client)
        response = tester.delete("/frontend/workspaces/WSP-0000000000000001/workflows/WFL-0000000000000001/nodes/NOD-0000000000000001")
        tester.assert_unauthorized(response)

