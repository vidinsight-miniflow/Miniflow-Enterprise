"""Test edge endpoints."""

import pytest
from fastapi.testclient import TestClient
from tests.fixtures.endpoint_test_helpers import EndpointTester


class TestEdgeEndpoints:
    """Test edge endpoints."""
    
    def test_create_edge_unauthorized(self, client: TestClient):
        """Test creating edge without authentication."""
        tester = EndpointTester(client)
        edge_data = {
            "source_node_id": "NOD-0000000000000001",
            "target_node_id": "NOD-0000000000000002"
        }
        response = tester.post("/frontend/workspaces/WSP-0000000000000001/workflows/WFL-0000000000000001/edges", json=edge_data)
        tester.assert_unauthorized(response)
    
    def test_get_edge_unauthorized(self, client: TestClient):
        """Test getting edge without authentication."""
        tester = EndpointTester(client)
        response = tester.get("/frontend/workspaces/WSP-0000000000000001/workflows/WFL-0000000000000001/edges/EDG-0000000000000001")
        tester.assert_unauthorized(response)
    
    def test_get_all_edges_unauthorized(self, client: TestClient):
        """Test getting all edges without authentication."""
        tester = EndpointTester(client)
        response = tester.get("/frontend/workspaces/WSP-0000000000000001/workflows/WFL-0000000000000001/edges")
        tester.assert_unauthorized(response)
    
    def test_get_outgoing_edges_unauthorized(self, client: TestClient):
        """Test getting outgoing edges without authentication."""
        tester = EndpointTester(client)
        response = tester.get("/frontend/workspaces/WSP-0000000000000001/workflows/WFL-0000000000000001/nodes/NOD-0000000000000001/outgoing-edges")
        tester.assert_unauthorized(response)
    
    def test_get_incoming_edges_unauthorized(self, client: TestClient):
        """Test getting incoming edges without authentication."""
        tester = EndpointTester(client)
        response = tester.get("/frontend/workspaces/WSP-0000000000000001/workflows/WFL-0000000000000001/nodes/NOD-0000000000000001/incoming-edges")
        tester.assert_unauthorized(response)
    
    def test_update_edge_unauthorized(self, client: TestClient):
        """Test updating edge without authentication."""
        tester = EndpointTester(client)
        edge_data = {"condition": "value > 10"}
        response = tester.put("/frontend/workspaces/WSP-0000000000000001/workflows/WFL-0000000000000001/edges/EDG-0000000000000001", json=edge_data)
        tester.assert_unauthorized(response)
    
    def test_delete_edge_unauthorized(self, client: TestClient):
        """Test deleting edge without authentication."""
        tester = EndpointTester(client)
        response = tester.delete("/frontend/workspaces/WSP-0000000000000001/workflows/WFL-0000000000000001/edges/EDG-0000000000000001")
        tester.assert_unauthorized(response)

