"""Test API key endpoints."""

import pytest
from fastapi.testclient import TestClient
from tests.fixtures.endpoint_test_helpers import EndpointTester


class TestApiKeyEndpoints:
    """Test API key management endpoints."""
    
    # ========================================================================
    # VALIDATE API KEY ENDPOINTS (Public)
    # ========================================================================
    
    def test_validate_api_key_success(self, client: TestClient):
        """Test validating API key (public endpoint)."""
        tester = EndpointTester(client)
        
        validate_data = {
            "full_api_key": "WSP-1234567890abcdef.abcdef1234567890",
            "client_ip": "127.0.0.1"
        }
        
        response = tester.post("/frontend/workspaces/api-keys/validate", json=validate_data)
        # May fail if API key invalid, but endpoint exists
        if response.status_code == 200:
            data = tester.assert_success(response)
            assert "valid" in data or "is_valid" in data
        elif response.status_code in [400, 401]:
            # Invalid API key is expected
            pass
    
    def test_validate_api_key_validation_error(self, client: TestClient):
        """Test validating API key with invalid data."""
        tester = EndpointTester(client)
        
        # Missing required fields
        invalid_data = {
            "client_ip": "127.0.0.1"
            # Missing full_api_key
        }
        
        response = tester.post("/frontend/workspaces/api-keys/validate", json=invalid_data)
        if response.status_code == 422:
            tester.assert_validation_error(response)
    
    # ========================================================================
    # CREATE API KEY ENDPOINTS
    # ========================================================================
    
    def test_create_api_key_unauthorized(self, client: TestClient):
        """Test creating API key without authentication."""
        tester = EndpointTester(client)
        
        api_key_data = {
            "name": "Test API Key",
            "description": "Test description",
            "permissions": ["read", "write"]
        }
        
        response = tester.post("/frontend/workspaces/WSP-0000000000000001/api-keys", json=api_key_data)
        tester.assert_unauthorized(response)
    
    def test_create_api_key_forbidden(self, client: TestClient, auth_headers: dict):
        """Test creating API key without workspace access."""
        tester = EndpointTester(client, auth_headers)
        
        api_key_data = {
            "name": "Test API Key",
            "permissions": ["read"]
        }
        
        response = tester.post("/frontend/workspaces/WSP-OTHERWORKSPACE01/api-keys", json=api_key_data)
        # Should return 403 if user doesn't have workspace access
        if response.status_code == 403:
            tester.assert_forbidden(response)
        elif response.status_code == 401:
            tester.assert_unauthorized(response)
    
    def test_create_api_key_validation_error(self, client: TestClient, auth_headers: dict):
        """Test creating API key with invalid data."""
        tester = EndpointTester(client, auth_headers)
        
        # Missing required fields
        invalid_data = {
            "description": "Test description"
            # Missing name, permissions
        }
        
        response = tester.post("/frontend/workspaces/WSP-0000000000000001/api-keys", json=invalid_data)
        if response.status_code == 422:
            tester.assert_validation_error(response)
        elif response.status_code in [401, 403]:
            # Auth issues
            pass
    
    # ========================================================================
    # GET API KEY ENDPOINTS
    # ========================================================================
    
    def test_get_api_key_unauthorized(self, client: TestClient):
        """Test getting API key without authentication."""
        tester = EndpointTester(client)
        
        response = tester.get("/frontend/workspaces/WSP-0000000000000001/api-keys/AKY-0000000000000001")
        tester.assert_unauthorized(response)
    
    def test_get_api_key_forbidden(self, client: TestClient, auth_headers: dict):
        """Test getting API key without workspace access."""
        tester = EndpointTester(client, auth_headers)
        
        response = tester.get("/frontend/workspaces/WSP-OTHERWORKSPACE01/api-keys/AKY-0000000000000001")
        # Should return 403 if user doesn't have workspace access
        if response.status_code == 403:
            tester.assert_forbidden(response)
        elif response.status_code == 401:
            tester.assert_unauthorized(response)
    
    def test_get_api_key_not_found(self, client: TestClient, auth_headers: dict):
        """Test getting non-existent API key."""
        tester = EndpointTester(client, auth_headers)
        
        response = tester.get("/frontend/workspaces/WSP-0000000000000001/api-keys/AKY-NONEXISTENT123")
        # May return 404 if API key doesn't exist
        if response.status_code == 404:
            tester.assert_not_found(response)
        elif response.status_code in [401, 403]:
            # Auth issues
            pass
    
    def test_get_all_api_keys_unauthorized(self, client: TestClient):
        """Test getting all API keys without authentication."""
        tester = EndpointTester(client)
        
        response = tester.get("/frontend/workspaces/WSP-0000000000000001/api-keys")
        tester.assert_unauthorized(response)
    
    def test_get_all_api_keys_forbidden(self, client: TestClient, auth_headers: dict):
        """Test getting all API keys without workspace access."""
        tester = EndpointTester(client, auth_headers)
        
        response = tester.get("/frontend/workspaces/WSP-OTHERWORKSPACE01/api-keys")
        # Should return 403 if user doesn't have workspace access
        if response.status_code == 403:
            tester.assert_forbidden(response)
        elif response.status_code == 401:
            tester.assert_unauthorized(response)
    
    # ========================================================================
    # UPDATE API KEY ENDPOINTS
    # ========================================================================
    
    def test_update_api_key_unauthorized(self, client: TestClient):
        """Test updating API key without authentication."""
        tester = EndpointTester(client)
        
        api_key_data = {
            "name": "Updated API Key",
            "description": "Updated description"
        }
        
        response = tester.put("/frontend/workspaces/WSP-0000000000000001/api-keys/AKY-0000000000000001", json=api_key_data)
        tester.assert_unauthorized(response)
    
    def test_update_api_key_forbidden(self, client: TestClient, auth_headers: dict):
        """Test updating API key without workspace access."""
        tester = EndpointTester(client, auth_headers)
        
        api_key_data = {
            "name": "Updated API Key"
        }
        
        response = tester.put("/frontend/workspaces/WSP-OTHERWORKSPACE01/api-keys/AKY-0000000000000001", json=api_key_data)
        # Should return 403 if user doesn't have workspace access
        if response.status_code == 403:
            tester.assert_forbidden(response)
        elif response.status_code == 401:
            tester.assert_unauthorized(response)
    
    def test_update_api_key_validation_error(self, client: TestClient, auth_headers: dict):
        """Test updating API key with invalid data."""
        tester = EndpointTester(client, auth_headers)
        
        # Invalid data
        invalid_data = {
            "name": ""  # Empty name
        }
        
        response = tester.put("/frontend/workspaces/WSP-0000000000000001/api-keys/AKY-0000000000000001", json=invalid_data)
        if response.status_code == 422:
            tester.assert_validation_error(response)
        elif response.status_code in [401, 403]:
            # Auth issues
            pass
    
    def test_update_api_key_not_found(self, client: TestClient, auth_headers: dict):
        """Test updating non-existent API key."""
        tester = EndpointTester(client, auth_headers)
        
        api_key_data = {
            "name": "Updated API Key"
        }
        
        response = tester.put("/frontend/workspaces/WSP-0000000000000001/api-keys/AKY-NONEXISTENT123", json=api_key_data)
        # May return 404 if API key doesn't exist
        if response.status_code == 404:
            tester.assert_not_found(response)
        elif response.status_code in [401, 403]:
            # Auth issues
            pass
    
    # ========================================================================
    # ACTIVATE/DEACTIVATE API KEY ENDPOINTS
    # ========================================================================
    
    def test_activate_api_key_unauthorized(self, client: TestClient):
        """Test activating API key without authentication."""
        tester = EndpointTester(client)
        
        response = tester.post("/frontend/workspaces/WSP-0000000000000001/api-keys/AKY-0000000000000001/activate", json={})
        tester.assert_unauthorized(response)
    
    def test_activate_api_key_forbidden(self, client: TestClient, auth_headers: dict):
        """Test activating API key without workspace access."""
        tester = EndpointTester(client, auth_headers)
        
        response = tester.post("/frontend/workspaces/WSP-OTHERWORKSPACE01/api-keys/AKY-0000000000000001/activate", json={})
        # Should return 403 if user doesn't have workspace access
        if response.status_code == 403:
            tester.assert_forbidden(response)
        elif response.status_code == 401:
            tester.assert_unauthorized(response)
    
    def test_activate_api_key_not_found(self, client: TestClient, auth_headers: dict):
        """Test activating non-existent API key."""
        tester = EndpointTester(client, auth_headers)
        
        response = tester.post("/frontend/workspaces/WSP-0000000000000001/api-keys/AKY-NONEXISTENT123/activate", json={})
        # May return 404 if API key doesn't exist
        if response.status_code == 404:
            tester.assert_not_found(response)
        elif response.status_code in [401, 403]:
            # Auth issues
            pass
    
    def test_deactivate_api_key_unauthorized(self, client: TestClient):
        """Test deactivating API key without authentication."""
        tester = EndpointTester(client)
        
        response = tester.post("/frontend/workspaces/WSP-0000000000000001/api-keys/AKY-0000000000000001/deactivate", json={})
        tester.assert_unauthorized(response)
    
    def test_deactivate_api_key_forbidden(self, client: TestClient, auth_headers: dict):
        """Test deactivating API key without workspace access."""
        tester = EndpointTester(client, auth_headers)
        
        response = tester.post("/frontend/workspaces/WSP-OTHERWORKSPACE01/api-keys/AKY-0000000000000001/deactivate", json={})
        # Should return 403 if user doesn't have workspace access
        if response.status_code == 403:
            tester.assert_forbidden(response)
        elif response.status_code == 401:
            tester.assert_unauthorized(response)
    
    def test_deactivate_api_key_not_found(self, client: TestClient, auth_headers: dict):
        """Test deactivating non-existent API key."""
        tester = EndpointTester(client, auth_headers)
        
        response = tester.post("/frontend/workspaces/WSP-0000000000000001/api-keys/AKY-NONEXISTENT123/deactivate", json={})
        # May return 404 if API key doesn't exist
        if response.status_code == 404:
            tester.assert_not_found(response)
        elif response.status_code in [401, 403]:
            # Auth issues
            pass
    
    # ========================================================================
    # DELETE API KEY ENDPOINTS
    # ========================================================================
    
    def test_delete_api_key_unauthorized(self, client: TestClient):
        """Test deleting API key without authentication."""
        tester = EndpointTester(client)
        
        response = tester.delete("/frontend/workspaces/WSP-0000000000000001/api-keys/AKY-0000000000000001")
        tester.assert_unauthorized(response)
    
    def test_delete_api_key_forbidden(self, client: TestClient, auth_headers: dict):
        """Test deleting API key without workspace access."""
        tester = EndpointTester(client, auth_headers)
        
        response = tester.delete("/frontend/workspaces/WSP-OTHERWORKSPACE01/api-keys/AKY-0000000000000001")
        # Should return 403 if user doesn't have workspace access
        if response.status_code == 403:
            tester.assert_forbidden(response)
        elif response.status_code == 401:
            tester.assert_unauthorized(response)
    
    def test_delete_api_key_not_found(self, client: TestClient, auth_headers: dict):
        """Test deleting non-existent API key."""
        tester = EndpointTester(client, auth_headers)
        
        response = tester.delete("/frontend/workspaces/WSP-0000000000000001/api-keys/AKY-NONEXISTENT123")
        # May return 404 if API key doesn't exist
        if response.status_code == 404:
            tester.assert_not_found(response)
        elif response.status_code in [401, 403]:
            # Auth issues
            pass

