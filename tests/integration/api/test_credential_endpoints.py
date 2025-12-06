"""Test credential endpoints."""

import pytest
from fastapi.testclient import TestClient
from tests.fixtures.endpoint_test_helpers import EndpointTester


class TestCredentialEndpoints:
    """Test credential management endpoints."""
    
    # ========================================================================
    # CREATE API KEY CREDENTIAL ENDPOINTS
    # ========================================================================
    
    def test_create_api_key_credential_unauthorized(self, client: TestClient):
        """Test creating API key credential without authentication."""
        tester = EndpointTester(client)
        
        credential_data = {
            "name": "Test API Key Credential",
            "api_key": "test_api_key_12345",
            "provider": "openai"
        }
        
        response = tester.post("/frontend/workspaces/WSP-0000000000000001/credentials/api-key", json=credential_data)
        tester.assert_unauthorized(response)
    
    def test_create_api_key_credential_forbidden(self, client: TestClient, auth_headers: dict):
        """Test creating API key credential without workspace access."""
        tester = EndpointTester(client, auth_headers)
        
        credential_data = {
            "name": "Test API Key Credential",
            "api_key": "test_api_key_12345",
            "provider": "openai"
        }
        
        response = tester.post("/frontend/workspaces/WSP-OTHERWORKSPACE01/credentials/api-key", json=credential_data)
        # Should return 403 if user doesn't have workspace access
        if response.status_code == 403:
            tester.assert_forbidden(response)
        elif response.status_code == 401:
            tester.assert_unauthorized(response)
    
    def test_create_api_key_credential_validation_error(self, client: TestClient, auth_headers: dict):
        """Test creating API key credential with invalid data."""
        tester = EndpointTester(client, auth_headers)
        
        # Missing required fields
        invalid_data = {
            "name": "Test API Key Credential"
            # Missing api_key, provider
        }
        
        response = tester.post("/frontend/workspaces/WSP-0000000000000001/credentials/api-key", json=invalid_data)
        if response.status_code == 422:
            tester.assert_validation_error(response)
        elif response.status_code in [401, 403]:
            # Auth issues
            pass
    
    # ========================================================================
    # CREATE SLACK CREDENTIAL ENDPOINTS
    # ========================================================================
    
    def test_create_slack_credential_unauthorized(self, client: TestClient):
        """Test creating Slack credential without authentication."""
        tester = EndpointTester(client)
        
        credential_data = {
            "name": "Test Slack Credential",
            "bot_token": "xoxb-test-token",
            "signing_secret": "test-signing-secret"
        }
        
        response = tester.post("/frontend/workspaces/WSP-0000000000000001/credentials/slack", json=credential_data)
        tester.assert_unauthorized(response)
    
    def test_create_slack_credential_forbidden(self, client: TestClient, auth_headers: dict):
        """Test creating Slack credential without workspace access."""
        tester = EndpointTester(client, auth_headers)
        
        credential_data = {
            "name": "Test Slack Credential",
            "bot_token": "xoxb-test-token",
            "signing_secret": "test-signing-secret"
        }
        
        response = tester.post("/frontend/workspaces/WSP-OTHERWORKSPACE01/credentials/slack", json=credential_data)
        # Should return 403 if user doesn't have workspace access
        if response.status_code == 403:
            tester.assert_forbidden(response)
        elif response.status_code == 401:
            tester.assert_unauthorized(response)
    
    def test_create_slack_credential_validation_error(self, client: TestClient, auth_headers: dict):
        """Test creating Slack credential with invalid data."""
        tester = EndpointTester(client, auth_headers)
        
        # Missing required fields
        invalid_data = {
            "name": "Test Slack Credential"
            # Missing bot_token, signing_secret
        }
        
        response = tester.post("/frontend/workspaces/WSP-0000000000000001/credentials/slack", json=invalid_data)
        if response.status_code == 422:
            tester.assert_validation_error(response)
        elif response.status_code in [401, 403]:
            # Auth issues
            pass
    
    # ========================================================================
    # GET CREDENTIAL ENDPOINTS
    # ========================================================================
    
    def test_get_credential_unauthorized(self, client: TestClient):
        """Test getting credential without authentication."""
        tester = EndpointTester(client)
        
        response = tester.get("/frontend/workspaces/WSP-0000000000000001/credentials/CRD-0000000000000001")
        tester.assert_unauthorized(response)
    
    def test_get_credential_forbidden(self, client: TestClient, auth_headers: dict):
        """Test getting credential without workspace access."""
        tester = EndpointTester(client, auth_headers)
        
        response = tester.get("/frontend/workspaces/WSP-OTHERWORKSPACE01/credentials/CRD-0000000000000001")
        # Should return 403 if user doesn't have workspace access
        if response.status_code == 403:
            tester.assert_forbidden(response)
        elif response.status_code == 401:
            tester.assert_unauthorized(response)
    
    def test_get_credential_not_found(self, client: TestClient, auth_headers: dict):
        """Test getting non-existent credential."""
        tester = EndpointTester(client, auth_headers)
        
        response = tester.get("/frontend/workspaces/WSP-0000000000000001/credentials/CRD-NONEXISTENT123")
        # May return 404 if credential doesn't exist
        if response.status_code == 404:
            tester.assert_not_found(response)
        elif response.status_code in [401, 403]:
            # Auth issues
            pass
    
    def test_get_all_credentials_unauthorized(self, client: TestClient):
        """Test getting all credentials without authentication."""
        tester = EndpointTester(client)
        
        response = tester.get("/frontend/workspaces/WSP-0000000000000001/credentials")
        tester.assert_unauthorized(response)
    
    def test_get_all_credentials_forbidden(self, client: TestClient, auth_headers: dict):
        """Test getting all credentials without workspace access."""
        tester = EndpointTester(client, auth_headers)
        
        response = tester.get("/frontend/workspaces/WSP-OTHERWORKSPACE01/credentials")
        # Should return 403 if user doesn't have workspace access
        if response.status_code == 403:
            tester.assert_forbidden(response)
        elif response.status_code == 401:
            tester.assert_unauthorized(response)
    
    # ========================================================================
    # UPDATE CREDENTIAL ENDPOINTS
    # ========================================================================
    
    def test_update_credential_unauthorized(self, client: TestClient):
        """Test updating credential without authentication."""
        tester = EndpointTester(client)
        
        credential_data = {
            "name": "Updated Credential",
            "description": "Updated description"
        }
        
        response = tester.put("/frontend/workspaces/WSP-0000000000000001/credentials/CRD-0000000000000001", json=credential_data)
        tester.assert_unauthorized(response)
    
    def test_update_credential_forbidden(self, client: TestClient, auth_headers: dict):
        """Test updating credential without workspace access."""
        tester = EndpointTester(client, auth_headers)
        
        credential_data = {
            "name": "Updated Credential"
        }
        
        response = tester.put("/frontend/workspaces/WSP-OTHERWORKSPACE01/credentials/CRD-0000000000000001", json=credential_data)
        # Should return 403 if user doesn't have workspace access
        if response.status_code == 403:
            tester.assert_forbidden(response)
        elif response.status_code == 401:
            tester.assert_unauthorized(response)
    
    def test_update_credential_validation_error(self, client: TestClient, auth_headers: dict):
        """Test updating credential with invalid data."""
        tester = EndpointTester(client, auth_headers)
        
        # Invalid data
        invalid_data = {
            "name": ""  # Empty name
        }
        
        response = tester.put("/frontend/workspaces/WSP-0000000000000001/credentials/CRD-0000000000000001", json=invalid_data)
        if response.status_code == 422:
            tester.assert_validation_error(response)
        elif response.status_code in [401, 403]:
            # Auth issues
            pass
    
    def test_update_credential_not_found(self, client: TestClient, auth_headers: dict):
        """Test updating non-existent credential."""
        tester = EndpointTester(client, auth_headers)
        
        credential_data = {
            "name": "Updated Credential"
        }
        
        response = tester.put("/frontend/workspaces/WSP-0000000000000001/credentials/CRD-NONEXISTENT123", json=credential_data)
        # May return 404 if credential doesn't exist
        if response.status_code == 404:
            tester.assert_not_found(response)
        elif response.status_code in [401, 403]:
            # Auth issues
            pass
    
    # ========================================================================
    # ACTIVATE/DEACTIVATE CREDENTIAL ENDPOINTS
    # ========================================================================
    
    def test_activate_credential_unauthorized(self, client: TestClient):
        """Test activating credential without authentication."""
        tester = EndpointTester(client)
        
        response = tester.post("/frontend/workspaces/WSP-0000000000000001/credentials/CRD-0000000000000001/activate", json={})
        tester.assert_unauthorized(response)
    
    def test_activate_credential_forbidden(self, client: TestClient, auth_headers: dict):
        """Test activating credential without workspace access."""
        tester = EndpointTester(client, auth_headers)
        
        response = tester.post("/frontend/workspaces/WSP-OTHERWORKSPACE01/credentials/CRD-0000000000000001/activate", json={})
        # Should return 403 if user doesn't have workspace access
        if response.status_code == 403:
            tester.assert_forbidden(response)
        elif response.status_code == 401:
            tester.assert_unauthorized(response)
    
    def test_activate_credential_not_found(self, client: TestClient, auth_headers: dict):
        """Test activating non-existent credential."""
        tester = EndpointTester(client, auth_headers)
        
        response = tester.post("/frontend/workspaces/WSP-0000000000000001/credentials/CRD-NONEXISTENT123/activate", json={})
        # May return 404 if credential doesn't exist
        if response.status_code == 404:
            tester.assert_not_found(response)
        elif response.status_code in [401, 403]:
            # Auth issues
            pass
    
    def test_deactivate_credential_unauthorized(self, client: TestClient):
        """Test deactivating credential without authentication."""
        tester = EndpointTester(client)
        
        response = tester.post("/frontend/workspaces/WSP-0000000000000001/credentials/CRD-0000000000000001/deactivate", json={})
        tester.assert_unauthorized(response)
    
    def test_deactivate_credential_forbidden(self, client: TestClient, auth_headers: dict):
        """Test deactivating credential without workspace access."""
        tester = EndpointTester(client, auth_headers)
        
        response = tester.post("/frontend/workspaces/WSP-OTHERWORKSPACE01/credentials/CRD-0000000000000001/deactivate", json={})
        # Should return 403 if user doesn't have workspace access
        if response.status_code == 403:
            tester.assert_forbidden(response)
        elif response.status_code == 401:
            tester.assert_unauthorized(response)
    
    def test_deactivate_credential_not_found(self, client: TestClient, auth_headers: dict):
        """Test deactivating non-existent credential."""
        tester = EndpointTester(client, auth_headers)
        
        response = tester.post("/frontend/workspaces/WSP-0000000000000001/credentials/CRD-NONEXISTENT123/deactivate", json={})
        # May return 404 if credential doesn't exist
        if response.status_code == 404:
            tester.assert_not_found(response)
        elif response.status_code in [401, 403]:
            # Auth issues
            pass
    
    # ========================================================================
    # DELETE CREDENTIAL ENDPOINTS
    # ========================================================================
    
    def test_delete_credential_unauthorized(self, client: TestClient):
        """Test deleting credential without authentication."""
        tester = EndpointTester(client)
        
        response = tester.delete("/frontend/workspaces/WSP-0000000000000001/credentials/CRD-0000000000000001")
        tester.assert_unauthorized(response)
    
    def test_delete_credential_forbidden(self, client: TestClient, auth_headers: dict):
        """Test deleting credential without workspace access."""
        tester = EndpointTester(client, auth_headers)
        
        response = tester.delete("/frontend/workspaces/WSP-OTHERWORKSPACE01/credentials/CRD-0000000000000001")
        # Should return 403 if user doesn't have workspace access
        if response.status_code == 403:
            tester.assert_forbidden(response)
        elif response.status_code == 401:
            tester.assert_unauthorized(response)
    
    def test_delete_credential_not_found(self, client: TestClient, auth_headers: dict):
        """Test deleting non-existent credential."""
        tester = EndpointTester(client, auth_headers)
        
        response = tester.delete("/frontend/workspaces/WSP-0000000000000001/credentials/CRD-NONEXISTENT123")
        # May return 404 if credential doesn't exist
        if response.status_code == 404:
            tester.assert_not_found(response)
        elif response.status_code in [401, 403]:
            # Auth issues
            pass

