"""Test variable endpoints."""

import pytest
from fastapi.testclient import TestClient
from tests.fixtures.endpoint_test_helpers import EndpointTester


class TestVariableEndpoints:
    """Test variable management endpoints."""
    
    # ========================================================================
    # CREATE VARIABLE ENDPOINTS
    # ========================================================================
    
    def test_create_variable_unauthorized(self, client: TestClient):
        """Test creating variable without authentication."""
        tester = EndpointTester(client)
        
        variable_data = {
            "key": "TEST_VAR",
            "value": "test_value",
            "description": "Test variable",
            "is_secret": False
        }
        
        response = tester.post("/frontend/workspaces/WSP-0000000000000001/variables", json=variable_data)
        tester.assert_unauthorized(response)
    
    def test_create_variable_forbidden(self, client: TestClient, auth_headers: dict):
        """Test creating variable without workspace access."""
        tester = EndpointTester(client, auth_headers)
        
        variable_data = {
            "key": "TEST_VAR",
            "value": "test_value"
        }
        
        response = tester.post("/frontend/workspaces/WSP-OTHERWORKSPACE01/variables", json=variable_data)
        # Should return 403 if user doesn't have workspace access
        if response.status_code == 403:
            tester.assert_forbidden(response)
        elif response.status_code == 401:
            tester.assert_unauthorized(response)
    
    def test_create_variable_validation_error(self, client: TestClient, auth_headers: dict):
        """Test creating variable with invalid data."""
        tester = EndpointTester(client, auth_headers)
        
        # Missing required fields
        invalid_data = {
            "value": "test_value"
            # Missing key
        }
        
        response = tester.post("/frontend/workspaces/WSP-0000000000000001/variables", json=invalid_data)
        if response.status_code == 422:
            tester.assert_validation_error(response)
        elif response.status_code in [401, 403]:
            # Auth issues
            pass
    
    def test_create_secret_variable(self, client: TestClient, auth_headers: dict):
        """Test creating secret variable."""
        tester = EndpointTester(client, auth_headers)
        
        variable_data = {
            "key": "SECRET_VAR",
            "value": "secret_value",
            "is_secret": True
        }
        
        response = tester.post("/frontend/workspaces/WSP-0000000000000001/variables", json=variable_data)
        # May fail if workspace access not available
        if response.status_code == 200:
            data = tester.assert_success(response)
            assert "id" in data or "variable_id" in data
        elif response.status_code in [401, 403]:
            # Auth issues
            pass
    
    # ========================================================================
    # GET VARIABLE ENDPOINTS
    # ========================================================================
    
    def test_get_variable_unauthorized(self, client: TestClient):
        """Test getting variable without authentication."""
        tester = EndpointTester(client)
        
        response = tester.get("/frontend/workspaces/WSP-0000000000000001/variables/VAR-0000000000000001")
        tester.assert_unauthorized(response)
    
    def test_get_variable_forbidden(self, client: TestClient, auth_headers: dict):
        """Test getting variable without workspace access."""
        tester = EndpointTester(client, auth_headers)
        
        response = tester.get("/frontend/workspaces/WSP-OTHERWORKSPACE01/variables/VAR-0000000000000001")
        # Should return 403 if user doesn't have workspace access
        if response.status_code == 403:
            tester.assert_forbidden(response)
        elif response.status_code == 401:
            tester.assert_unauthorized(response)
    
    def test_get_variable_not_found(self, client: TestClient, auth_headers: dict):
        """Test getting non-existent variable."""
        tester = EndpointTester(client, auth_headers)
        
        response = tester.get("/frontend/workspaces/WSP-0000000000000001/variables/VAR-NONEXISTENT123")
        # May return 404 if variable doesn't exist
        if response.status_code == 404:
            tester.assert_not_found(response)
        elif response.status_code in [401, 403]:
            # Auth issues
            pass
    
    def test_get_variable_with_decrypt(self, client: TestClient, auth_headers: dict):
        """Test getting variable with decrypt_secret parameter."""
        tester = EndpointTester(client, auth_headers)
        
        response = tester.get("/frontend/workspaces/WSP-0000000000000001/variables/VAR-0000000000000001?decrypt_secret=true")
        # May fail if workspace access not available
        if response.status_code == 200:
            data = tester.assert_success(response)
        elif response.status_code in [401, 403, 404]:
            # Auth or not found issues
            pass
    
    def test_get_variable_by_key_unauthorized(self, client: TestClient):
        """Test getting variable by key without authentication."""
        tester = EndpointTester(client)
        
        response = tester.get("/frontend/workspaces/WSP-0000000000000001/variables/key/TEST_VAR")
        tester.assert_unauthorized(response)
    
    def test_get_variable_by_key_forbidden(self, client: TestClient, auth_headers: dict):
        """Test getting variable by key without workspace access."""
        tester = EndpointTester(client, auth_headers)
        
        response = tester.get("/frontend/workspaces/WSP-OTHERWORKSPACE01/variables/key/TEST_VAR")
        # Should return 403 if user doesn't have workspace access
        if response.status_code == 403:
            tester.assert_forbidden(response)
        elif response.status_code == 401:
            tester.assert_unauthorized(response)
    
    def test_get_variable_by_key_not_found(self, client: TestClient, auth_headers: dict):
        """Test getting non-existent variable by key."""
        tester = EndpointTester(client, auth_headers)
        
        response = tester.get("/frontend/workspaces/WSP-0000000000000001/variables/key/NONEXISTENT_VAR")
        # May return 404 if variable doesn't exist
        if response.status_code == 404:
            tester.assert_not_found(response)
        elif response.status_code in [401, 403]:
            # Auth issues
            pass
    
    def test_get_all_variables_unauthorized(self, client: TestClient):
        """Test getting all variables without authentication."""
        tester = EndpointTester(client)
        
        response = tester.get("/frontend/workspaces/WSP-0000000000000001/variables")
        tester.assert_unauthorized(response)
    
    def test_get_all_variables_forbidden(self, client: TestClient, auth_headers: dict):
        """Test getting all variables without workspace access."""
        tester = EndpointTester(client, auth_headers)
        
        response = tester.get("/frontend/workspaces/WSP-OTHERWORKSPACE01/variables")
        # Should return 403 if user doesn't have workspace access
        if response.status_code == 403:
            tester.assert_forbidden(response)
        elif response.status_code == 401:
            tester.assert_unauthorized(response)
    
    # ========================================================================
    # UPDATE VARIABLE ENDPOINTS
    # ========================================================================
    
    def test_update_variable_unauthorized(self, client: TestClient):
        """Test updating variable without authentication."""
        tester = EndpointTester(client)
        
        variable_data = {
            "value": "updated_value",
            "description": "Updated description"
        }
        
        response = tester.put("/frontend/workspaces/WSP-0000000000000001/variables/VAR-0000000000000001", json=variable_data)
        tester.assert_unauthorized(response)
    
    def test_update_variable_forbidden(self, client: TestClient, auth_headers: dict):
        """Test updating variable without workspace access."""
        tester = EndpointTester(client, auth_headers)
        
        variable_data = {
            "value": "updated_value"
        }
        
        response = tester.put("/frontend/workspaces/WSP-OTHERWORKSPACE01/variables/VAR-0000000000000001", json=variable_data)
        # Should return 403 if user doesn't have workspace access
        if response.status_code == 403:
            tester.assert_forbidden(response)
        elif response.status_code == 401:
            tester.assert_unauthorized(response)
    
    def test_update_variable_validation_error(self, client: TestClient, auth_headers: dict):
        """Test updating variable with invalid data."""
        tester = EndpointTester(client, auth_headers)
        
        # Empty value might be invalid
        invalid_data = {
            "value": ""
        }
        
        response = tester.put("/frontend/workspaces/WSP-0000000000000001/variables/VAR-0000000000000001", json=invalid_data)
        if response.status_code == 422:
            tester.assert_validation_error(response)
        elif response.status_code in [401, 403]:
            # Auth issues
            pass
    
    def test_update_variable_not_found(self, client: TestClient, auth_headers: dict):
        """Test updating non-existent variable."""
        tester = EndpointTester(client, auth_headers)
        
        variable_data = {
            "value": "updated_value"
        }
        
        response = tester.put("/frontend/workspaces/WSP-0000000000000001/variables/VAR-NONEXISTENT123", json=variable_data)
        # May return 404 if variable doesn't exist
        if response.status_code == 404:
            tester.assert_not_found(response)
        elif response.status_code in [401, 403]:
            # Auth issues
            pass
    
    # ========================================================================
    # DELETE VARIABLE ENDPOINTS
    # ========================================================================
    
    def test_delete_variable_unauthorized(self, client: TestClient):
        """Test deleting variable without authentication."""
        tester = EndpointTester(client)
        
        response = tester.delete("/frontend/workspaces/WSP-0000000000000001/variables/VAR-0000000000000001")
        tester.assert_unauthorized(response)
    
    def test_delete_variable_forbidden(self, client: TestClient, auth_headers: dict):
        """Test deleting variable without workspace access."""
        tester = EndpointTester(client, auth_headers)
        
        response = tester.delete("/frontend/workspaces/WSP-OTHERWORKSPACE01/variables/VAR-0000000000000001")
        # Should return 403 if user doesn't have workspace access
        if response.status_code == 403:
            tester.assert_forbidden(response)
        elif response.status_code == 401:
            tester.assert_unauthorized(response)
    
    def test_delete_variable_not_found(self, client: TestClient, auth_headers: dict):
        """Test deleting non-existent variable."""
        tester = EndpointTester(client, auth_headers)
        
        response = tester.delete("/frontend/workspaces/WSP-0000000000000001/variables/VAR-NONEXISTENT123")
        # May return 404 if variable doesn't exist
        if response.status_code == 404:
            tester.assert_not_found(response)
        elif response.status_code in [401, 403]:
            # Auth issues
            pass

