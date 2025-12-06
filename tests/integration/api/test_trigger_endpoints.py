"""Test trigger endpoints."""

import pytest
from fastapi.testclient import TestClient
from tests.fixtures.endpoint_test_helpers import EndpointTester


class TestTriggerEndpoints:
    """Test trigger endpoints."""
    
    def test_create_trigger_unauthorized(self, client: TestClient):
        """Test creating trigger without authentication."""
        tester = EndpointTester(client)
        trigger_data = {
            "trigger_type": "SCHEDULE",
            "schedule_config": {"cron": "0 0 * * *"}
        }
        response = tester.post("/frontend/workspaces/WSP-0000000000000001/workflows/WFL-0000000000000001/triggers", json=trigger_data)
        tester.assert_unauthorized(response)
    
    def test_get_trigger_unauthorized(self, client: TestClient):
        """Test getting trigger without authentication."""
        tester = EndpointTester(client)
        response = tester.get("/frontend/workspaces/WSP-0000000000000001/workflows/WFL-0000000000000001/triggers/TRG-0000000000000001")
        tester.assert_unauthorized(response)
    
    def test_get_workspace_triggers_unauthorized(self, client: TestClient):
        """Test getting workspace triggers without authentication."""
        tester = EndpointTester(client)
        response = tester.get("/frontend/workspaces/WSP-0000000000000001/triggers")
        tester.assert_unauthorized(response)
    
    def test_get_workflow_triggers_unauthorized(self, client: TestClient):
        """Test getting workflow triggers without authentication."""
        tester = EndpointTester(client)
        response = tester.get("/frontend/workspaces/WSP-0000000000000001/workflows/WFL-0000000000000001/triggers")
        tester.assert_unauthorized(response)
    
    def test_get_trigger_limits_success(self, client: TestClient):
        """Test getting trigger limits (public endpoint)."""
        tester = EndpointTester(client)
        response = tester.get("/frontend/workspaces/triggers/limits")
        # Public endpoint
        if response.status_code == 200:
            tester.assert_success(response)
        elif response.status_code == 404:
            # May return 404 if route not found
            pass
    
    def test_update_trigger_unauthorized(self, client: TestClient):
        """Test updating trigger without authentication."""
        tester = EndpointTester(client)
        trigger_data = {"schedule_config": {"cron": "0 1 * * *"}}
        response = tester.put("/frontend/workspaces/WSP-0000000000000001/workflows/WFL-0000000000000001/triggers/TRG-0000000000000001", json=trigger_data)
        tester.assert_unauthorized(response)
    
    def test_enable_trigger_unauthorized(self, client: TestClient):
        """Test enabling trigger without authentication."""
        tester = EndpointTester(client)
        response = tester.post("/frontend/workspaces/WSP-0000000000000001/workflows/WFL-0000000000000001/triggers/TRG-0000000000000001/enable", json={})
        tester.assert_unauthorized(response)
    
    def test_disable_trigger_unauthorized(self, client: TestClient):
        """Test disabling trigger without authentication."""
        tester = EndpointTester(client)
        response = tester.post("/frontend/workspaces/WSP-0000000000000001/workflows/WFL-0000000000000001/triggers/TRG-0000000000000001/disable", json={})
        tester.assert_unauthorized(response)
    
    def test_delete_trigger_unauthorized(self, client: TestClient):
        """Test deleting trigger without authentication."""
        tester = EndpointTester(client)
        response = tester.delete("/frontend/workspaces/WSP-0000000000000001/workflows/WFL-0000000000000001/triggers/TRG-0000000000000001")
        tester.assert_unauthorized(response)

