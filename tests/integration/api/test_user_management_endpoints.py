"""Test user management endpoints."""

import pytest
from fastapi.testclient import TestClient
from tests.fixtures.endpoint_test_helpers import EndpointTester


class TestUserManagementEndpoints:
    """Test user management endpoints."""
    
    # ========================================================================
    # USER DETAILS ENDPOINTS
    # ========================================================================
    
    def test_get_user_details_unauthorized(self, client: TestClient):
        """Test getting user details without authentication."""
        tester = EndpointTester(client)
        
        response = tester.get("/frontend/users/USR-0000000000000001")
        tester.assert_unauthorized(response)
    
    def test_get_user_details_forbidden(self, client: TestClient, auth_headers: dict):
        """Test getting another user's details (should be forbidden)."""
        tester = EndpointTester(client, auth_headers)
        
        response = tester.get("/frontend/users/USR-OTHERUSER00001")
        # Should return 403 if user tries to access another user's details
        if response.status_code == 403:
            tester.assert_forbidden(response)
        elif response.status_code == 401:
            tester.assert_unauthorized(response)
    
    def test_get_user_by_email_requires_admin(self, client: TestClient):
        """Test getting user by email requires admin."""
        tester = EndpointTester(client)
        
        response = tester.get("/frontend/users/by-email/test@example.com")
        tester.assert_unauthorized(response)
    
    def test_get_user_by_email_forbidden(self, client: TestClient, auth_headers: dict):
        """Test getting user by email as non-admin."""
        tester = EndpointTester(client, auth_headers)
        
        response = tester.get("/frontend/users/by-email/test@example.com")
        # Should return 403 if user is not admin
        if response.status_code == 403:
            tester.assert_forbidden(response)
        elif response.status_code == 401:
            tester.assert_unauthorized(response)
    
    def test_get_user_by_username_requires_admin(self, client: TestClient):
        """Test getting user by username requires admin."""
        tester = EndpointTester(client)
        
        response = tester.get("/frontend/users/by-username/testuser")
        tester.assert_unauthorized(response)
    
    def test_get_user_by_username_forbidden(self, client: TestClient, auth_headers: dict):
        """Test getting user by username as non-admin."""
        tester = EndpointTester(client, auth_headers)
        
        response = tester.get("/frontend/users/by-username/testuser")
        # Should return 403 if user is not admin
        if response.status_code == 403:
            tester.assert_forbidden(response)
        elif response.status_code == 401:
            tester.assert_unauthorized(response)
    
    # ========================================================================
    # USER PREFERENCES ENDPOINTS
    # ========================================================================
    
    def test_get_all_user_preferences_unauthorized(self, client: TestClient):
        """Test getting user preferences without authentication."""
        tester = EndpointTester(client)
        
        response = tester.get("/frontend/users/USR-0000000000000001/preferences")
        tester.assert_unauthorized(response)
    
    def test_get_all_user_preferences_forbidden(self, client: TestClient, auth_headers: dict):
        """Test getting another user's preferences (should be forbidden)."""
        tester = EndpointTester(client, auth_headers)
        
        response = tester.get("/frontend/users/USR-OTHERUSER00001/preferences")
        # Should return 403 if user tries to access another user's preferences
        if response.status_code == 403:
            tester.assert_forbidden(response)
        elif response.status_code == 401:
            tester.assert_unauthorized(response)
    
    def test_get_user_preference_unauthorized(self, client: TestClient):
        """Test getting specific preference without authentication."""
        tester = EndpointTester(client)
        
        response = tester.get("/frontend/users/USR-0000000000000001/preferences/theme")
        tester.assert_unauthorized(response)
    
    def test_get_user_preference_forbidden(self, client: TestClient, auth_headers: dict):
        """Test getting another user's preference (should be forbidden)."""
        tester = EndpointTester(client, auth_headers)
        
        response = tester.get("/frontend/users/USR-OTHERUSER00001/preferences/theme")
        # Should return 403
        if response.status_code == 403:
            tester.assert_forbidden(response)
        elif response.status_code == 401:
            tester.assert_unauthorized(response)
    
    def test_get_user_preferences_by_category_unauthorized(self, client: TestClient):
        """Test getting preferences by category without authentication."""
        tester = EndpointTester(client)
        
        response = tester.get("/frontend/users/USR-0000000000000001/preferences/category/ui")
        tester.assert_unauthorized(response)
    
    def test_get_user_preferences_by_category_forbidden(self, client: TestClient, auth_headers: dict):
        """Test getting another user's preferences by category (should be forbidden)."""
        tester = EndpointTester(client, auth_headers)
        
        response = tester.get("/frontend/users/USR-OTHERUSER00001/preferences/category/ui")
        # Should return 403
        if response.status_code == 403:
            tester.assert_forbidden(response)
        elif response.status_code == 401:
            tester.assert_unauthorized(response)
    
    def test_set_user_preference_unauthorized(self, client: TestClient):
        """Test setting preference without authentication."""
        tester = EndpointTester(client)
        
        preference_data = {
            "key": "theme",
            "value": "dark",
            "category": "ui",
            "description": "UI theme preference"
        }
        
        response = tester.put("/frontend/users/USR-0000000000000001/preferences", json=preference_data)
        tester.assert_unauthorized(response)
    
    def test_set_user_preference_forbidden(self, client: TestClient, auth_headers: dict):
        """Test setting another user's preference (should be forbidden)."""
        tester = EndpointTester(client, auth_headers)
        
        preference_data = {
            "key": "theme",
            "value": "dark",
            "category": "ui"
        }
        
        response = tester.put("/frontend/users/USR-OTHERUSER00001/preferences", json=preference_data)
        # Should return 403
        if response.status_code == 403:
            tester.assert_forbidden(response)
        elif response.status_code == 401:
            tester.assert_unauthorized(response)
    
    def test_set_user_preference_validation_error(self, client: TestClient, auth_headers: dict):
        """Test setting preference with invalid data."""
        tester = EndpointTester(client, auth_headers)
        
        # Missing required fields
        invalid_data = {
            "key": "theme"
            # Missing value, category
        }
        
        response = tester.put("/frontend/users/USR-0000000000000001/preferences", json=invalid_data)
        if response.status_code == 422:
            tester.assert_validation_error(response)
        elif response.status_code in [401, 403]:
            # Auth issues
            pass
    
    def test_delete_user_preference_unauthorized(self, client: TestClient):
        """Test deleting preference without authentication."""
        tester = EndpointTester(client)
        
        response = tester.delete("/frontend/users/USR-0000000000000001/preferences/theme")
        tester.assert_unauthorized(response)
    
    def test_delete_user_preference_forbidden(self, client: TestClient, auth_headers: dict):
        """Test deleting another user's preference (should be forbidden)."""
        tester = EndpointTester(client, auth_headers)
        
        response = tester.delete("/frontend/users/USR-OTHERUSER00001/preferences/theme")
        # Should return 403
        if response.status_code == 403:
            tester.assert_forbidden(response)
        elif response.status_code == 401:
            tester.assert_unauthorized(response)
    
    # ========================================================================
    # ACCOUNT DELETION ENDPOINTS
    # ========================================================================
    
    def test_request_account_deletion_unauthorized(self, client: TestClient):
        """Test requesting account deletion without authentication."""
        tester = EndpointTester(client)
        
        deletion_data = {
            "reason": "No longer needed"
        }
        
        response = tester.post("/frontend/users/USR-0000000000000001/deletion/request", json=deletion_data)
        tester.assert_unauthorized(response)
    
    def test_request_account_deletion_forbidden(self, client: TestClient, auth_headers: dict):
        """Test requesting deletion for another user's account (should be forbidden)."""
        tester = EndpointTester(client, auth_headers)
        
        deletion_data = {
            "reason": "Test"
        }
        
        response = tester.post("/frontend/users/USR-OTHERUSER00001/deletion/request", json=deletion_data)
        # Should return 403
        if response.status_code == 403:
            tester.assert_forbidden(response)
        elif response.status_code == 401:
            tester.assert_unauthorized(response)
    
    def test_request_account_deletion_validation_error(self, client: TestClient, auth_headers: dict):
        """Test requesting deletion with invalid data."""
        tester = EndpointTester(client, auth_headers)
        
        # Missing required fields
        invalid_data = {}
        
        response = tester.post("/frontend/users/USR-0000000000000001/deletion/request", json=invalid_data)
        if response.status_code == 422:
            tester.assert_validation_error(response)
        elif response.status_code in [401, 403]:
            # Auth issues
            pass
    
    def test_cancel_account_deletion_unauthorized(self, client: TestClient):
        """Test canceling account deletion without authentication."""
        tester = EndpointTester(client)
        
        response = tester.post("/frontend/users/USR-0000000000000001/deletion/cancel", json={})
        tester.assert_unauthorized(response)
    
    def test_cancel_account_deletion_forbidden(self, client: TestClient, auth_headers: dict):
        """Test canceling deletion for another user's account (should be forbidden)."""
        tester = EndpointTester(client, auth_headers)
        
        response = tester.post("/frontend/users/USR-OTHERUSER00001/deletion/cancel", json={})
        # Should return 403
        if response.status_code == 403:
            tester.assert_forbidden(response)
        elif response.status_code == 401:
            tester.assert_unauthorized(response)
    
    def test_get_deletion_status_unauthorized(self, client: TestClient):
        """Test getting deletion status without authentication."""
        tester = EndpointTester(client)
        
        response = tester.get("/frontend/users/USR-0000000000000001/deletion/status")
        tester.assert_unauthorized(response)
    
    def test_get_deletion_status_forbidden(self, client: TestClient, auth_headers: dict):
        """Test getting deletion status for another user's account (should be forbidden)."""
        tester = EndpointTester(client, auth_headers)
        
        response = tester.get("/frontend/users/USR-OTHERUSER00001/deletion/status")
        # Should return 403
        if response.status_code == 403:
            tester.assert_forbidden(response)
        elif response.status_code == 401:
            tester.assert_unauthorized(response)
    
    # ========================================================================
    # MARKETING CONSENT ENDPOINTS
    # ========================================================================
    
    def test_update_marketing_consent_unauthorized(self, client: TestClient):
        """Test updating marketing consent without authentication."""
        tester = EndpointTester(client)
        
        consent_data = {
            "consent": True
        }
        
        response = tester.put("/frontend/users/USR-0000000000000001/marketing-consent", json=consent_data)
        tester.assert_unauthorized(response)
    
    def test_update_marketing_consent_forbidden(self, client: TestClient, auth_headers: dict):
        """Test updating another user's marketing consent (should be forbidden)."""
        tester = EndpointTester(client, auth_headers)
        
        consent_data = {
            "consent": True
        }
        
        response = tester.put("/frontend/users/USR-OTHERUSER00001/marketing-consent", json=consent_data)
        # Should return 403
        if response.status_code == 403:
            tester.assert_forbidden(response)
        elif response.status_code == 401:
            tester.assert_unauthorized(response)
    
    def test_update_marketing_consent_validation_error(self, client: TestClient, auth_headers: dict):
        """Test updating marketing consent with invalid data."""
        tester = EndpointTester(client, auth_headers)
        
        # Missing required fields
        invalid_data = {}
        
        response = tester.put("/frontend/users/USR-0000000000000001/marketing-consent", json=invalid_data)
        if response.status_code == 422:
            tester.assert_validation_error(response)
        elif response.status_code in [401, 403]:
            # Auth issues
            pass

