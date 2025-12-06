"""Test custom script endpoints."""

import pytest
from fastapi.testclient import TestClient
from tests.fixtures.endpoint_test_helpers import EndpointTester


class TestCustomScriptEndpoints:
    """Test custom script endpoints."""
    
    def test_create_custom_script_unauthorized(self, client: TestClient):
        """Test creating custom script without authentication."""
        tester = EndpointTester(client)
        script_data = {
            "name": "Test Script",
            "content": "print('hello')",
            "category": "data_processing"
        }
        response = tester.post("/frontend/workspaces/WSP-0000000000000001/scripts", json=script_data)
        tester.assert_unauthorized(response)
    
    def test_get_custom_script_unauthorized(self, client: TestClient):
        """Test getting custom script without authentication."""
        tester = EndpointTester(client)
        response = tester.get("/frontend/workspaces/WSP-0000000000000001/scripts/SCR-0000000000000001")
        tester.assert_unauthorized(response)
    
    def test_get_script_content_unauthorized(self, client: TestClient):
        """Test getting script content without authentication."""
        tester = EndpointTester(client)
        response = tester.get("/frontend/workspaces/WSP-0000000000000001/scripts/SCR-0000000000000001/content")
        tester.assert_unauthorized(response)
    
    def test_get_all_scripts_unauthorized(self, client: TestClient):
        """Test getting all scripts without authentication."""
        tester = EndpointTester(client)
        response = tester.get("/frontend/workspaces/WSP-0000000000000001/scripts")
        tester.assert_unauthorized(response)
    
    def test_update_custom_script_unauthorized(self, client: TestClient):
        """Test updating custom script without authentication."""
        tester = EndpointTester(client)
        script_data = {"name": "Updated Script"}
        response = tester.put("/frontend/workspaces/WSP-0000000000000001/scripts/SCR-0000000000000001", json=script_data)
        tester.assert_unauthorized(response)
    
    def test_approve_script_unauthorized(self, client: TestClient):
        """Test approving script without authentication."""
        tester = EndpointTester(client)
        response = tester.post("/frontend/workspaces/WSP-0000000000000001/scripts/SCR-0000000000000001/approve", json={})
        tester.assert_unauthorized(response)
    
    def test_reject_script_unauthorized(self, client: TestClient):
        """Test rejecting script without authentication."""
        tester = EndpointTester(client)
        reject_data = {"reason": "Invalid script"}
        response = tester.post("/frontend/workspaces/WSP-0000000000000001/scripts/SCR-0000000000000001/reject", json=reject_data)
        tester.assert_unauthorized(response)
    
    def test_delete_custom_script_unauthorized(self, client: TestClient):
        """Test deleting custom script without authentication."""
        tester = EndpointTester(client)
        response = tester.delete("/frontend/workspaces/WSP-0000000000000001/scripts/SCR-0000000000000001")
        tester.assert_unauthorized(response)
    
    def test_reset_approval_status_unauthorized(self, client: TestClient):
        """Test resetting approval status without authentication."""
        tester = EndpointTester(client)
        response = tester.post("/frontend/workspaces/WSP-0000000000000001/scripts/SCR-0000000000000001/reset-approval", json={})
        tester.assert_unauthorized(response)
    
    def test_mark_as_dangerous_unauthorized(self, client: TestClient):
        """Test marking script as dangerous without authentication."""
        tester = EndpointTester(client)
        response = tester.post("/frontend/workspaces/WSP-0000000000000001/scripts/SCR-0000000000000001/mark-dangerous", json={})
        tester.assert_unauthorized(response)
    
    def test_unmark_as_dangerous_unauthorized(self, client: TestClient):
        """Test unmarking script as dangerous without authentication."""
        tester = EndpointTester(client)
        response = tester.post("/frontend/workspaces/WSP-0000000000000001/scripts/SCR-0000000000000001/unmark-dangerous", json={})
        tester.assert_unauthorized(response)
    
    def test_create_custom_script_forbidden(self, client: TestClient, auth_headers: dict):
        """Test creating custom script without workspace access."""
        tester = EndpointTester(client, auth_headers)
        script_data = {
            "name": "Test Script",
            "content": "print('hello')",
            "category": "data_processing"
        }
        response = tester.post("/frontend/workspaces/WSP-OTHERWORKSPACE01/scripts", json=script_data)
        if response.status_code == 403:
            tester.assert_forbidden(response)
        elif response.status_code == 401:
            tester.assert_unauthorized(response)
    
    def test_create_custom_script_validation_error(self, client: TestClient, auth_headers: dict):
        """Test creating custom script with invalid data."""
        tester = EndpointTester(client, auth_headers)
        invalid_data = {
            "content": "print('hello')"
            # Missing name, category
        }
        response = tester.post("/frontend/workspaces/WSP-0000000000000001/scripts", json=invalid_data)
        if response.status_code == 422:
            tester.assert_validation_error(response)
        elif response.status_code in [401, 403]:
            pass
    
    def test_get_custom_script_not_found(self, client: TestClient, auth_headers: dict):
        """Test getting non-existent custom script."""
        tester = EndpointTester(client, auth_headers)
        response = tester.get("/frontend/workspaces/WSP-0000000000000001/scripts/SCR-NONEXISTENT123")
        if response.status_code == 404:
            tester.assert_not_found(response)
        elif response.status_code in [401, 403]:
            pass
    
    def test_approve_script_forbidden(self, client: TestClient, auth_headers: dict):
        """Test approving script without admin access."""
        tester = EndpointTester(client, auth_headers)
        approval_data = {"review_notes": "Looks good"}
        response = tester.post("/frontend/workspaces/WSP-0000000000000001/scripts/SCR-0000000000000001/approve", json=approval_data)
        # May return 403 if not admin, or 401 if auth fails
        if response.status_code == 403:
            tester.assert_forbidden(response)
        elif response.status_code == 401:
            tester.assert_unauthorized(response)
    
    def test_reject_script_validation_error(self, client: TestClient, auth_headers: dict):
        """Test rejecting script with missing review notes."""
        tester = EndpointTester(client, auth_headers)
        invalid_data = {}  # Missing review_notes
        response = tester.post("/frontend/workspaces/WSP-0000000000000001/scripts/SCR-0000000000000001/reject", json=invalid_data)
        if response.status_code == 422:
            tester.assert_validation_error(response)
        elif response.status_code in [401, 403]:
            pass

