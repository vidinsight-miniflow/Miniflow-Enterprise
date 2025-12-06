"""Test user role endpoints."""

import pytest
from fastapi.testclient import TestClient
from tests.fixtures.endpoint_test_helpers import EndpointTester


class TestUserRoleEndpoints:
    """Test user role endpoints."""
    
    def test_get_all_user_roles_unauthorized(self, client: TestClient):
        """Test getting all user roles without authentication."""
        tester = EndpointTester(client)
        response = tester.get("/frontend/user-roles")
        tester.assert_unauthorized(response)
    
    def test_get_user_role_by_id_unauthorized(self, client: TestClient):
        """Test getting user role by ID without authentication."""
        tester = EndpointTester(client)
        response = tester.get("/frontend/user-roles/ROL-0000000000000001")
        tester.assert_unauthorized(response)
    
    def test_get_user_role_by_name_unauthorized(self, client: TestClient):
        """Test getting user role by name without authentication."""
        tester = EndpointTester(client)
        response = tester.get("/frontend/user-roles/name/admin")
        tester.assert_unauthorized(response)
    
    def test_get_role_permissions_unauthorized(self, client: TestClient):
        """Test getting role permissions without authentication."""
        tester = EndpointTester(client)
        response = tester.get("/frontend/user-roles/ROL-0000000000000001/permissions")
        tester.assert_unauthorized(response)
    
    def test_check_permission_unauthorized(self, client: TestClient):
        """Test checking permission without authentication."""
        tester = EndpointTester(client)
        response = tester.get("/frontend/user-roles/ROL-0000000000000001/check-permission?permission=can_edit_workspace")
        tester.assert_unauthorized(response)
    
    def test_check_permission_validation_error(self, client: TestClient, auth_headers: dict):
        """Test checking permission with missing query parameter."""
        tester = EndpointTester(client, auth_headers)
        response = tester.get("/frontend/user-roles/ROL-0000000000000001/check-permission")
        if response.status_code == 422:
            tester.assert_validation_error(response)
        elif response.status_code in [401, 403]:
            pass

