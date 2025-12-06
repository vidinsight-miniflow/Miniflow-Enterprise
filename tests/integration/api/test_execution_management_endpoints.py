"""Test execution management endpoints."""

import pytest
from fastapi.testclient import TestClient
from tests.fixtures.endpoint_test_helpers import EndpointTester


class TestExecutionManagementEndpoints:
    """Test execution management endpoints."""
    
    def test_start_execution_unauthorized(self, client: TestClient):
        """Test starting execution without authentication."""
        tester = EndpointTester(client)
        execution_data = {"input_data": {}}
        response = tester.post("/frontend/workspaces/WSP-0000000000000001/workflows/WFL-0000000000000001/executions/test", json=execution_data)
        tester.assert_unauthorized(response)
    
    def test_get_execution_unauthorized(self, client: TestClient):
        """Test getting execution without authentication."""
        tester = EndpointTester(client)
        response = tester.get("/frontend/workspaces/WSP-0000000000000001/executions/EXE-0000000000000001")
        tester.assert_unauthorized(response)
    
    def test_get_workspace_executions_unauthorized(self, client: TestClient):
        """Test getting workspace executions without authentication."""
        tester = EndpointTester(client)
        response = tester.get("/frontend/workspaces/WSP-0000000000000001/executions")
        tester.assert_unauthorized(response)
    
    def test_get_workflow_executions_unauthorized(self, client: TestClient):
        """Test getting workflow executions without authentication."""
        tester = EndpointTester(client)
        response = tester.get("/frontend/workspaces/WSP-0000000000000001/workflows/WFL-0000000000000001/executions")
        tester.assert_unauthorized(response)
    
    def test_get_execution_stats_unauthorized(self, client: TestClient):
        """Test getting execution stats without authentication."""
        tester = EndpointTester(client)
        response = tester.get("/frontend/workspaces/WSP-0000000000000001/executions/stats")
        tester.assert_unauthorized(response)

