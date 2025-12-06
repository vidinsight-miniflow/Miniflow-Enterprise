"""Test workspace member endpoints."""

import pytest
from fastapi.testclient import TestClient
from tests.fixtures.endpoint_test_helpers import EndpointTester


class TestWorkspaceMemberEndpoints:
    """Test workspace member endpoints."""
    
    def test_get_workspace_members_unauthorized(self, client: TestClient):
        """Test getting workspace members without authentication."""
        tester = EndpointTester(client)
        response = tester.get("/frontend/workspaces/WSP-0000000000000001/members")
        tester.assert_unauthorized(response)
    
    def test_get_member_details_unauthorized(self, client: TestClient):
        """Test getting member details without authentication."""
        tester = EndpointTester(client)
        response = tester.get("/frontend/workspaces/WSP-0000000000000001/members/MEM-0000000000000001")
        tester.assert_unauthorized(response)
    
    def test_get_user_workspaces_unauthorized(self, client: TestClient):
        """Test getting user workspaces without authentication."""
        tester = EndpointTester(client)
        response = tester.get("/frontend/workspaces/user/USR-0000000000000001/workspaces")
        tester.assert_unauthorized(response)
    
    def test_change_member_role_unauthorized(self, client: TestClient):
        """Test changing member role without authentication."""
        tester = EndpointTester(client)
        role_data = {"new_role_id": "ROL-0000000000000002"}
        response = tester.put("/frontend/workspaces/WSP-0000000000000001/members/MEM-0000000000000001/role", json=role_data)
        tester.assert_unauthorized(response)
    
    def test_remove_member_unauthorized(self, client: TestClient):
        """Test removing member without authentication."""
        tester = EndpointTester(client)
        response = tester.delete("/frontend/workspaces/WSP-0000000000000001/members/USR-0000000000000001")
        tester.assert_unauthorized(response)
    
    def test_leave_workspace_unauthorized(self, client: TestClient):
        """Test leaving workspace without authentication."""
        tester = EndpointTester(client)
        response = tester.post("/frontend/workspaces/WSP-0000000000000001/leave", json={})
        tester.assert_unauthorized(response)
    
    def test_set_custom_permissions_unauthorized(self, client: TestClient):
        """Test setting custom permissions without authentication."""
        tester = EndpointTester(client)
        permissions_data = {"custom_permissions": ["can_edit"]}
        response = tester.put("/frontend/workspaces/WSP-0000000000000001/members/MEM-0000000000000001/permissions", json=permissions_data)
        tester.assert_unauthorized(response)
    
    def test_clear_custom_permissions_unauthorized(self, client: TestClient):
        """Test clearing custom permissions without authentication."""
        tester = EndpointTester(client)
        response = tester.delete("/frontend/workspaces/WSP-0000000000000001/members/MEM-0000000000000001/permissions")
        tester.assert_unauthorized(response)

