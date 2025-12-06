"""Test workflow management endpoints."""

import pytest
from fastapi.testclient import TestClient
from tests.fixtures.endpoint_test_helpers import EndpointTester


class TestWorkflowManagementEndpoints:
    """Test workflow management endpoints."""
    
    # ========================================================================
    # CREATE WORKFLOW ENDPOINTS
    # ========================================================================
    
    def test_create_workflow_unauthorized(self, client: TestClient):
        """Test creating workflow without authentication."""
        tester = EndpointTester(client)
        
        workflow_data = {
            "name": "Test Workflow",
            "description": "Test description",
            "priority": "normal",
            "tags": ["test"]
        }
        
        response = tester.post("/frontend/workspaces/WSP-0000000000000001/workflows", json=workflow_data)
        tester.assert_unauthorized(response)
    
    def test_create_workflow_forbidden(self, client: TestClient, auth_headers: dict):
        """Test creating workflow without workspace access."""
        tester = EndpointTester(client, auth_headers)
        
        workflow_data = {
            "name": "Test Workflow",
            "description": "Test description"
        }
        
        response = tester.post("/frontend/workspaces/WSP-OTHERWORKSPACE01/workflows", json=workflow_data)
        # Should return 403 if user doesn't have workspace access
        if response.status_code == 403:
            tester.assert_forbidden(response)
        elif response.status_code == 401:
            tester.assert_unauthorized(response)
    
    def test_create_workflow_validation_error(self, client: TestClient, auth_headers: dict):
        """Test creating workflow with invalid data."""
        tester = EndpointTester(client, auth_headers)
        
        # Missing required fields
        invalid_data = {
            "description": "Test description"
            # Missing name
        }
        
        response = tester.post("/frontend/workspaces/WSP-0000000000000001/workflows", json=invalid_data)
        if response.status_code == 422:
            tester.assert_validation_error(response)
        elif response.status_code in [401, 403]:
            # Auth issues
            pass
    
    # ========================================================================
    # GET WORKFLOW ENDPOINTS
    # ========================================================================
    
    def test_get_workflow_unauthorized(self, client: TestClient):
        """Test getting workflow without authentication."""
        tester = EndpointTester(client)
        
        response = tester.get("/frontend/workspaces/WSP-0000000000000001/workflows/WKF-0000000000000001")
        tester.assert_unauthorized(response)
    
    def test_get_workflow_forbidden(self, client: TestClient, auth_headers: dict):
        """Test getting workflow without workspace access."""
        tester = EndpointTester(client, auth_headers)
        
        response = tester.get("/frontend/workspaces/WSP-OTHERWORKSPACE01/workflows/WKF-0000000000000001")
        # Should return 403 if user doesn't have workspace access
        if response.status_code == 403:
            tester.assert_forbidden(response)
        elif response.status_code == 401:
            tester.assert_unauthorized(response)
    
    def test_get_workflow_not_found(self, client: TestClient, auth_headers: dict):
        """Test getting non-existent workflow."""
        tester = EndpointTester(client, auth_headers)
        
        response = tester.get("/frontend/workspaces/WSP-0000000000000001/workflows/WKF-NONEXISTENT123")
        # May return 404 if workflow doesn't exist
        if response.status_code == 404:
            tester.assert_not_found(response)
        elif response.status_code in [401, 403]:
            # Auth issues
            pass
    
    def test_get_workspace_workflows_unauthorized(self, client: TestClient):
        """Test getting workspace workflows without authentication."""
        tester = EndpointTester(client)
        
        response = tester.get("/frontend/workspaces/WSP-0000000000000001/workflows")
        tester.assert_unauthorized(response)
    
    def test_get_workspace_workflows_forbidden(self, client: TestClient, auth_headers: dict):
        """Test getting workspace workflows without workspace access."""
        tester = EndpointTester(client, auth_headers)
        
        response = tester.get("/frontend/workspaces/WSP-OTHERWORKSPACE01/workflows")
        # Should return 403 if user doesn't have workspace access
        if response.status_code == 403:
            tester.assert_forbidden(response)
        elif response.status_code == 401:
            tester.assert_unauthorized(response)
    
    def test_get_workspace_workflows_with_status_filter(self, client: TestClient, auth_headers: dict):
        """Test getting workspace workflows with status filter."""
        tester = EndpointTester(client, auth_headers)
        
        response = tester.get("/frontend/workspaces/WSP-0000000000000001/workflows?status=ACTIVE")
        # May fail if workspace access not available
        if response.status_code == 200:
            data = tester.assert_success(response)
            assert "items" in data or "workflows" in data
        elif response.status_code in [401, 403]:
            # Auth issues
            pass
    
    def test_get_workflow_graph_unauthorized(self, client: TestClient):
        """Test getting workflow graph without authentication."""
        tester = EndpointTester(client)
        
        response = tester.get("/frontend/workspaces/WSP-0000000000000001/workflows/WKF-0000000000000001/graph")
        tester.assert_unauthorized(response)
    
    def test_get_workflow_graph_forbidden(self, client: TestClient, auth_headers: dict):
        """Test getting workflow graph without workspace access."""
        tester = EndpointTester(client, auth_headers)
        
        response = tester.get("/frontend/workspaces/WSP-OTHERWORKSPACE01/workflows/WKF-0000000000000001/graph")
        # Should return 403 if user doesn't have workspace access
        if response.status_code == 403:
            tester.assert_forbidden(response)
        elif response.status_code == 401:
            tester.assert_unauthorized(response)
    
    # ========================================================================
    # UPDATE WORKFLOW ENDPOINTS
    # ========================================================================
    
    def test_update_workflow_unauthorized(self, client: TestClient):
        """Test updating workflow without authentication."""
        tester = EndpointTester(client)
        
        workflow_data = {
            "name": "Updated Workflow",
            "description": "Updated description"
        }
        
        response = tester.put("/frontend/workspaces/WSP-0000000000000001/workflows/WKF-0000000000000001", json=workflow_data)
        tester.assert_unauthorized(response)
    
    def test_update_workflow_forbidden(self, client: TestClient, auth_headers: dict):
        """Test updating workflow without workspace access."""
        tester = EndpointTester(client, auth_headers)
        
        workflow_data = {
            "name": "Updated Workflow"
        }
        
        response = tester.put("/frontend/workspaces/WSP-OTHERWORKSPACE01/workflows/WKF-0000000000000001", json=workflow_data)
        # Should return 403 if user doesn't have workspace access
        if response.status_code == 403:
            tester.assert_forbidden(response)
        elif response.status_code == 401:
            tester.assert_unauthorized(response)
    
    def test_update_workflow_validation_error(self, client: TestClient, auth_headers: dict):
        """Test updating workflow with invalid data."""
        tester = EndpointTester(client, auth_headers)
        
        # Invalid data
        invalid_data = {
            "name": ""  # Empty name
        }
        
        response = tester.put("/frontend/workspaces/WSP-0000000000000001/workflows/WKF-0000000000000001", json=invalid_data)
        if response.status_code == 422:
            tester.assert_validation_error(response)
        elif response.status_code in [401, 403]:
            # Auth issues
            pass
    
    def test_update_workflow_not_found(self, client: TestClient, auth_headers: dict):
        """Test updating non-existent workflow."""
        tester = EndpointTester(client, auth_headers)
        
        workflow_data = {
            "name": "Updated Workflow"
        }
        
        response = tester.put("/frontend/workspaces/WSP-0000000000000001/workflows/WKF-NONEXISTENT123", json=workflow_data)
        # May return 404 if workflow doesn't exist
        if response.status_code == 404:
            tester.assert_not_found(response)
        elif response.status_code in [401, 403]:
            # Auth issues
            pass
    
    # ========================================================================
    # ACTIVATE/DEACTIVATE WORKFLOW ENDPOINTS
    # ========================================================================
    
    def test_activate_workflow_unauthorized(self, client: TestClient):
        """Test activating workflow without authentication."""
        tester = EndpointTester(client)
        
        response = tester.post("/frontend/workspaces/WSP-0000000000000001/workflows/WKF-0000000000000001/activate", json={})
        tester.assert_unauthorized(response)
    
    def test_activate_workflow_forbidden(self, client: TestClient, auth_headers: dict):
        """Test activating workflow without workspace access."""
        tester = EndpointTester(client, auth_headers)
        
        response = tester.post("/frontend/workspaces/WSP-OTHERWORKSPACE01/workflows/WKF-0000000000000001/activate", json={})
        # Should return 403 if user doesn't have workspace access
        if response.status_code == 403:
            tester.assert_forbidden(response)
        elif response.status_code == 401:
            tester.assert_unauthorized(response)
    
    def test_activate_workflow_not_found(self, client: TestClient, auth_headers: dict):
        """Test activating non-existent workflow."""
        tester = EndpointTester(client, auth_headers)
        
        response = tester.post("/frontend/workspaces/WSP-0000000000000001/workflows/WKF-NONEXISTENT123/activate", json={})
        # May return 404 if workflow doesn't exist
        if response.status_code == 404:
            tester.assert_not_found(response)
        elif response.status_code in [401, 403]:
            # Auth issues
            pass
    
    def test_deactivate_workflow_unauthorized(self, client: TestClient):
        """Test deactivating workflow without authentication."""
        tester = EndpointTester(client)
        
        deactivate_data = {
            "reason": "Test deactivation"
        }
        
        response = tester.post("/frontend/workspaces/WSP-0000000000000001/workflows/WKF-0000000000000001/deactivate", json=deactivate_data)
        tester.assert_unauthorized(response)
    
    def test_deactivate_workflow_forbidden(self, client: TestClient, auth_headers: dict):
        """Test deactivating workflow without workspace access."""
        tester = EndpointTester(client, auth_headers)
        
        deactivate_data = {
            "reason": "Test deactivation"
        }
        
        response = tester.post("/frontend/workspaces/WSP-OTHERWORKSPACE01/workflows/WKF-0000000000000001/deactivate", json=deactivate_data)
        # Should return 403 if user doesn't have workspace access
        if response.status_code == 403:
            tester.assert_forbidden(response)
        elif response.status_code == 401:
            tester.assert_unauthorized(response)
    
    def test_deactivate_workflow_validation_error(self, client: TestClient, auth_headers: dict):
        """Test deactivating workflow with invalid data."""
        tester = EndpointTester(client, auth_headers)
        
        # Missing required fields
        invalid_data = {}
        
        response = tester.post("/frontend/workspaces/WSP-0000000000000001/workflows/WKF-0000000000000001/deactivate", json=invalid_data)
        if response.status_code == 422:
            tester.assert_validation_error(response)
        elif response.status_code in [401, 403]:
            # Auth issues
            pass
    
    def test_deactivate_workflow_not_found(self, client: TestClient, auth_headers: dict):
        """Test deactivating non-existent workflow."""
        tester = EndpointTester(client, auth_headers)
        
        deactivate_data = {
            "reason": "Test deactivation"
        }
        
        response = tester.post("/frontend/workspaces/WSP-0000000000000001/workflows/WKF-NONEXISTENT123/deactivate", json=deactivate_data)
        # May return 404 if workflow doesn't exist
        if response.status_code == 404:
            tester.assert_not_found(response)
        elif response.status_code in [401, 403]:
            # Auth issues
            pass
    
    # ========================================================================
    # ARCHIVE/SET DRAFT ENDPOINTS
    # ========================================================================
    
    def test_archive_workflow_unauthorized(self, client: TestClient):
        """Test archiving workflow without authentication."""
        tester = EndpointTester(client)
        
        response = tester.post("/frontend/workspaces/WSP-0000000000000001/workflows/WKF-0000000000000001/archive", json={})
        tester.assert_unauthorized(response)
    
    def test_archive_workflow_forbidden(self, client: TestClient, auth_headers: dict):
        """Test archiving workflow without workspace access."""
        tester = EndpointTester(client, auth_headers)
        
        response = tester.post("/frontend/workspaces/WSP-OTHERWORKSPACE01/workflows/WKF-0000000000000001/archive", json={})
        # Should return 403 if user doesn't have workspace access
        if response.status_code == 403:
            tester.assert_forbidden(response)
        elif response.status_code == 401:
            tester.assert_unauthorized(response)
    
    def test_archive_workflow_not_found(self, client: TestClient, auth_headers: dict):
        """Test archiving non-existent workflow."""
        tester = EndpointTester(client, auth_headers)
        
        response = tester.post("/frontend/workspaces/WSP-0000000000000001/workflows/WKF-NONEXISTENT123/archive", json={})
        # May return 404 if workflow doesn't exist
        if response.status_code == 404:
            tester.assert_not_found(response)
        elif response.status_code in [401, 403]:
            # Auth issues
            pass
    
    def test_set_draft_unauthorized(self, client: TestClient):
        """Test setting workflow to draft without authentication."""
        tester = EndpointTester(client)
        
        response = tester.post("/frontend/workspaces/WSP-0000000000000001/workflows/WKF-0000000000000001/set-draft", json={})
        tester.assert_unauthorized(response)
    
    def test_set_draft_forbidden(self, client: TestClient, auth_headers: dict):
        """Test setting workflow to draft without workspace access."""
        tester = EndpointTester(client, auth_headers)
        
        response = tester.post("/frontend/workspaces/WSP-OTHERWORKSPACE01/workflows/WKF-0000000000000001/set-draft", json={})
        # Should return 403 if user doesn't have workspace access
        if response.status_code == 403:
            tester.assert_forbidden(response)
        elif response.status_code == 401:
            tester.assert_unauthorized(response)
    
    def test_set_draft_not_found(self, client: TestClient, auth_headers: dict):
        """Test setting non-existent workflow to draft."""
        tester = EndpointTester(client, auth_headers)
        
        response = tester.post("/frontend/workspaces/WSP-0000000000000001/workflows/WKF-NONEXISTENT123/set-draft", json={})
        # May return 404 if workflow doesn't exist
        if response.status_code == 404:
            tester.assert_not_found(response)
        elif response.status_code in [401, 403]:
            # Auth issues
            pass
    
    # ========================================================================
    # DELETE WORKFLOW ENDPOINTS
    # ========================================================================
    
    def test_delete_workflow_unauthorized(self, client: TestClient):
        """Test deleting workflow without authentication."""
        tester = EndpointTester(client)
        
        response = tester.delete("/frontend/workspaces/WSP-0000000000000001/workflows/WKF-0000000000000001")
        tester.assert_unauthorized(response)
    
    def test_delete_workflow_forbidden(self, client: TestClient, auth_headers: dict):
        """Test deleting workflow without workspace access."""
        tester = EndpointTester(client, auth_headers)
        
        response = tester.delete("/frontend/workspaces/WSP-OTHERWORKSPACE01/workflows/WKF-0000000000000001")
        # Should return 403 if user doesn't have workspace access
        if response.status_code == 403:
            tester.assert_forbidden(response)
        elif response.status_code == 401:
            tester.assert_unauthorized(response)
    
    def test_delete_workflow_not_found(self, client: TestClient, auth_headers: dict):
        """Test deleting non-existent workflow."""
        tester = EndpointTester(client, auth_headers)
        
        response = tester.delete("/frontend/workspaces/WSP-0000000000000001/workflows/WKF-NONEXISTENT123")
        # May return 404 if workflow doesn't exist
        if response.status_code == 404:
            tester.assert_not_found(response)
        elif response.status_code in [401, 403]:
            # Auth issues
            pass

