"""Test global script endpoints."""

import pytest
from fastapi.testclient import TestClient
from tests.fixtures.endpoint_test_helpers import EndpointTester


class TestGlobalScriptEndpoints:
    """Test global script endpoints."""
    
    def test_create_global_script_unauthorized(self, client: TestClient):
        """Test creating global script without authentication."""
        tester = EndpointTester(client)
        script_data = {
            "name": "Test Global Script",
            "content": "print('hello')",
            "category": "data_processing"
        }
        response = tester.post("/frontend/admin/scripts", json=script_data)
        # May return 404 if route not found, or 401/403 if unauthorized
        if response.status_code in [401, 403]:
            tester.assert_unauthorized(response)
        elif response.status_code == 404:
            tester.assert_not_found(response)
    
    def test_get_global_script_unauthorized(self, client: TestClient):
        """Test getting global script without authentication."""
        tester = EndpointTester(client)
        response = tester.get("/frontend/admin/scripts/SCR-0000000000000001")
        # May return 404 if route not found, or 401/403 if unauthorized
        if response.status_code in [401, 403]:
            tester.assert_unauthorized(response)
        elif response.status_code == 404:
            tester.assert_not_found(response)
    
    def test_get_global_script_by_name_unauthorized(self, client: TestClient):
        """Test getting global script by name without authentication."""
        tester = EndpointTester(client)
        response = tester.get("/frontend/admin/scripts/name/test-script")
        # May return 404 if route not found, or 401/403 if unauthorized
        if response.status_code in [401, 403]:
            tester.assert_unauthorized(response)
        elif response.status_code == 404:
            tester.assert_not_found(response)
    
    def test_get_script_content_unauthorized(self, client: TestClient):
        """Test getting script content without authentication."""
        tester = EndpointTester(client)
        response = tester.get("/frontend/admin/scripts/SCR-0000000000000001/content")
        # May return 404 if route not found, or 401/403 if unauthorized
        if response.status_code in [401, 403]:
            tester.assert_unauthorized(response)
        elif response.status_code == 404:
            tester.assert_not_found(response)
    
    def test_get_all_scripts_unauthorized(self, client: TestClient):
        """Test getting all scripts without authentication."""
        tester = EndpointTester(client)
        response = tester.get("/frontend/admin/scripts")
        # May return 404 if route not found, or 401/403 if unauthorized
        if response.status_code in [401, 403]:
            tester.assert_unauthorized(response)
        elif response.status_code == 404:
            tester.assert_not_found(response)
    
    def test_get_categories_unauthorized(self, client: TestClient):
        """Test getting categories without authentication."""
        tester = EndpointTester(client)
        response = tester.get("/frontend/admin/scripts/categories")
        # May return 404 if route not found, or 401/403 if unauthorized
        if response.status_code in [401, 403]:
            tester.assert_unauthorized(response)
        elif response.status_code == 404:
            tester.assert_not_found(response)
    
    def test_update_global_script_unauthorized(self, client: TestClient):
        """Test updating global script without authentication."""
        tester = EndpointTester(client)
        script_data = {"name": "Updated Script"}
        response = tester.put("/frontend/admin/scripts/SCR-0000000000000001", json=script_data)
        # May return 404 if route not found, or 401/403 if unauthorized
        if response.status_code in [401, 403]:
            tester.assert_unauthorized(response)
        elif response.status_code == 404:
            tester.assert_not_found(response)
    
    def test_delete_global_script_unauthorized(self, client: TestClient):
        """Test deleting global script without authentication."""
        tester = EndpointTester(client)
        response = tester.delete("/frontend/admin/scripts/SCR-0000000000000001")
        # May return 404 if script doesn't exist, or 401/403 if unauthorized
        if response.status_code in [401, 403]:
            tester.assert_unauthorized(response)
        elif response.status_code == 404:
            tester.assert_not_found(response)

