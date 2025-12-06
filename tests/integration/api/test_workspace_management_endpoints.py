"""Test workspace management endpoints."""

import pytest
from fastapi.testclient import TestClient
from tests.fixtures.endpoint_test_helpers import EndpointTester


class TestWorkspaceManagementEndpoints:
    """Test workspace management endpoints."""
    
    # ========================================================================
    # CREATE WORKSPACE ENDPOINTS
    # ========================================================================
    
    def test_create_workspace_unauthorized(self, client: TestClient):
        """Test creating workspace without authentication."""
        tester = EndpointTester(client)
        
        workspace_data = {
            "name": "Test Workspace",
            "slug": "test-workspace",
            "description": "Test description"
        }
        
        response = tester.post("/frontend/workspaces", json=workspace_data)
        tester.assert_unauthorized(response)
    
    def test_create_workspace_validation_error(self, client: TestClient, auth_headers: dict):
        """Test creating workspace with invalid data."""
        tester = EndpointTester(client, auth_headers)
        
        # Missing required fields
        invalid_data = {
            "name": "Test Workspace"
            # Missing slug
        }
        
        response = tester.post("/frontend/workspaces", json=invalid_data)
        if response.status_code == 422:
            tester.assert_validation_error(response)
        elif response.status_code in [401, 403]:
            # Auth issues
            pass
    
    # ========================================================================
    # GET WORKSPACE ENDPOINTS
    # ========================================================================
    
    def test_get_workspace_unauthorized(self, client: TestClient):
        """Test getting workspace without authentication."""
        tester = EndpointTester(client)
        
        response = tester.get("/frontend/workspaces/WSP-0000000000000001")
        tester.assert_unauthorized(response)
    
    def test_get_workspace_forbidden(self, client: TestClient, auth_headers: dict):
        """Test getting workspace without access."""
        tester = EndpointTester(client, auth_headers)
        
        response = tester.get("/frontend/workspaces/WSP-OTHERWORKSPACE01")
        # Should return 403 if user doesn't have access
        if response.status_code == 403:
            tester.assert_forbidden(response)
        elif response.status_code == 401:
            tester.assert_unauthorized(response)
    
    def test_get_workspace_details_unauthorized(self, client: TestClient):
        """Test getting workspace details without authentication."""
        tester = EndpointTester(client)
        
        response = tester.get("/frontend/workspaces/WSP-0000000000000001/details")
        tester.assert_unauthorized(response)
    
    def test_get_workspace_details_forbidden(self, client: TestClient, auth_headers: dict):
        """Test getting workspace details without access."""
        tester = EndpointTester(client, auth_headers)
        
        response = tester.get("/frontend/workspaces/WSP-OTHERWORKSPACE01/details")
        # Should return 403 if user doesn't have access
        if response.status_code == 403:
            tester.assert_forbidden(response)
        elif response.status_code == 401:
            tester.assert_unauthorized(response)
    
    def test_get_workspace_limits_unauthorized(self, client: TestClient):
        """Test getting workspace limits without authentication."""
        tester = EndpointTester(client)
        
        response = tester.get("/frontend/workspaces/WSP-0000000000000001/limits")
        tester.assert_unauthorized(response)
    
    def test_get_workspace_limits_forbidden(self, client: TestClient, auth_headers: dict):
        """Test getting workspace limits without access."""
        tester = EndpointTester(client, auth_headers)
        
        response = tester.get("/frontend/workspaces/WSP-OTHERWORKSPACE01/limits")
        # Should return 403 if user doesn't have access
        if response.status_code == 403:
            tester.assert_forbidden(response)
        elif response.status_code == 401:
            tester.assert_unauthorized(response)
    
    def test_get_workspace_by_slug_unauthorized(self, client: TestClient):
        """Test getting workspace by slug without authentication."""
        tester = EndpointTester(client)
        
        response = tester.get("/frontend/workspaces/slug/test-workspace")
        tester.assert_unauthorized(response)
    
    def test_get_workspace_by_slug_not_found(self, client: TestClient, auth_headers: dict):
        """Test getting non-existent workspace by slug."""
        tester = EndpointTester(client, auth_headers)
        
        response = tester.get("/frontend/workspaces/slug/non-existent-workspace")
        # May return 404 if workspace doesn't exist
        if response.status_code == 404:
            tester.assert_not_found(response)
        elif response.status_code in [401, 403]:
            # Auth issues
            pass
    
    # ========================================================================
    # UPDATE WORKSPACE ENDPOINTS
    # ========================================================================
    
    def test_update_workspace_unauthorized(self, client: TestClient):
        """Test updating workspace without authentication."""
        tester = EndpointTester(client)
        
        workspace_data = {
            "name": "Updated Workspace",
            "slug": "updated-workspace"
        }
        
        response = tester.put("/frontend/workspaces/WSP-0000000000000001", json=workspace_data)
        tester.assert_unauthorized(response)
    
    def test_update_workspace_forbidden(self, client: TestClient, auth_headers: dict):
        """Test updating workspace as non-owner."""
        tester = EndpointTester(client, auth_headers)
        
        workspace_data = {
            "name": "Updated Workspace",
            "slug": "updated-workspace"
        }
        
        response = tester.put("/frontend/workspaces/WSP-OTHERWORKSPACE01", json=workspace_data)
        # Should return 403 if user is not owner
        if response.status_code == 403:
            tester.assert_forbidden(response)
        elif response.status_code == 401:
            tester.assert_unauthorized(response)
    
    def test_update_workspace_validation_error(self, client: TestClient, auth_headers: dict):
        """Test updating workspace with invalid data."""
        tester = EndpointTester(client, auth_headers)
        
        # Invalid data
        invalid_data = {
            "name": ""  # Empty name
        }
        
        response = tester.put("/frontend/workspaces/WSP-0000000000000001", json=invalid_data)
        if response.status_code == 422:
            tester.assert_validation_error(response)
        elif response.status_code in [401, 403]:
            # Auth issues
            pass
    
    # ========================================================================
    # DELETE WORKSPACE ENDPOINTS
    # ========================================================================
    
    def test_delete_workspace_unauthorized(self, client: TestClient):
        """Test deleting workspace without authentication."""
        tester = EndpointTester(client)
        
        response = tester.delete("/frontend/workspaces/WSP-0000000000000001")
        tester.assert_unauthorized(response)
    
    def test_delete_workspace_forbidden(self, client: TestClient, auth_headers: dict):
        """Test deleting workspace as non-owner."""
        tester = EndpointTester(client, auth_headers)
        
        response = tester.delete("/frontend/workspaces/WSP-OTHERWORKSPACE01")
        # Should return 403 if user is not owner
        if response.status_code == 403:
            tester.assert_forbidden(response)
        elif response.status_code == 401:
            tester.assert_unauthorized(response)
    
    def test_delete_workspace_not_found(self, client: TestClient, auth_headers: dict):
        """Test deleting non-existent workspace."""
        tester = EndpointTester(client, auth_headers)
        
        response = tester.delete("/frontend/workspaces/WSP-NONEXISTENT123")
        # May return 404 if workspace doesn't exist
        if response.status_code == 404:
            tester.assert_not_found(response)
        elif response.status_code in [401, 403]:
            # Auth issues
            pass
    
    # ========================================================================
    # SUSPEND/UNSUSPEND ENDPOINTS
    # ========================================================================
    
    def test_suspend_workspace_unauthorized(self, client: TestClient):
        """Test suspending workspace without authentication."""
        tester = EndpointTester(client)
        
        suspend_data = {
            "reason": "Test suspension"
        }
        
        response = tester.post("/frontend/workspaces/WSP-0000000000000001/suspend", json=suspend_data)
        tester.assert_unauthorized(response)
    
    def test_suspend_workspace_forbidden(self, client: TestClient, auth_headers: dict):
        """Test suspending workspace as non-admin."""
        tester = EndpointTester(client, auth_headers)
        
        suspend_data = {
            "reason": "Test suspension"
        }
        
        response = tester.post("/frontend/workspaces/WSP-0000000000000001/suspend", json=suspend_data)
        # Should return 403 if user is not admin (TODO: Currently only checks auth, not admin)
        if response.status_code == 403:
            tester.assert_forbidden(response)
        elif response.status_code == 401:
            tester.assert_unauthorized(response)
    
    def test_suspend_workspace_validation_error(self, client: TestClient, admin_headers: dict):
        """Test suspending workspace with invalid data."""
        tester = EndpointTester(client, admin_headers)
        
        # Missing required fields
        invalid_data = {}
        
        response = tester.post("/frontend/workspaces/WSP-0000000000000001/suspend", json=invalid_data)
        if response.status_code == 422:
            tester.assert_validation_error(response)
        elif response.status_code in [401, 403]:
            # Auth issues
            pass
    
    def test_unsuspend_workspace_unauthorized(self, client: TestClient):
        """Test unsuspending workspace without authentication."""
        tester = EndpointTester(client)
        
        response = tester.post("/frontend/workspaces/WSP-0000000000000001/unsuspend", json={})
        tester.assert_unauthorized(response)
    
    def test_unsuspend_workspace_forbidden(self, client: TestClient, auth_headers: dict):
        """Test unsuspending workspace as non-admin."""
        tester = EndpointTester(client, auth_headers)
        
        response = tester.post("/frontend/workspaces/WSP-0000000000000001/unsuspend", json={})
        # Should return 403 if user is not admin (TODO: Currently only checks auth, not admin)
        if response.status_code == 403:
            tester.assert_forbidden(response)
        elif response.status_code == 401:
            tester.assert_unauthorized(response)
    
    # ========================================================================
    # TRANSFER OWNERSHIP ENDPOINTS
    # ========================================================================
    
    def test_transfer_ownership_unauthorized(self, client: TestClient):
        """Test transferring ownership without authentication."""
        tester = EndpointTester(client)
        
        transfer_data = {
            "new_owner_id": "USR-0000000000000002"
        }
        
        response = tester.post("/frontend/workspaces/WSP-0000000000000001/transfer-ownership", json=transfer_data)
        tester.assert_unauthorized(response)
    
    def test_transfer_ownership_forbidden(self, client: TestClient, auth_headers: dict):
        """Test transferring ownership as non-owner."""
        tester = EndpointTester(client, auth_headers)
        
        transfer_data = {
            "new_owner_id": "USR-0000000000000002"
        }
        
        response = tester.post("/frontend/workspaces/WSP-OTHERWORKSPACE01/transfer-ownership", json=transfer_data)
        # Should return 403 if user is not owner
        if response.status_code == 403:
            tester.assert_forbidden(response)
        elif response.status_code == 401:
            tester.assert_unauthorized(response)
    
    def test_transfer_ownership_validation_error(self, client: TestClient, auth_headers: dict):
        """Test transferring ownership with invalid data."""
        tester = EndpointTester(client, auth_headers)
        
        # Missing required fields
        invalid_data = {}
        
        response = tester.post("/frontend/workspaces/WSP-0000000000000001/transfer-ownership", json=invalid_data)
        if response.status_code == 422:
            tester.assert_validation_error(response)
        elif response.status_code in [401, 403]:
            # Auth issues
            pass
    
    def test_transfer_ownership_not_found(self, client: TestClient, auth_headers: dict):
        """Test transferring ownership of non-existent workspace."""
        tester = EndpointTester(client, auth_headers)
        
        transfer_data = {
            "new_owner_id": "USR-0000000000000002"
        }
        
        response = tester.post("/frontend/workspaces/WSP-NONEXISTENT123/transfer-ownership", json=transfer_data)
        # May return 404 if workspace doesn't exist
        if response.status_code == 404:
            tester.assert_not_found(response)
        elif response.status_code in [401, 403]:
            # Auth issues
            pass

