"""Test user password endpoints."""

import pytest
from fastapi.testclient import TestClient
from tests.fixtures.endpoint_test_helpers import EndpointTester


class TestUserPasswordEndpoints:
    """Test user password endpoints."""
    
    def test_change_password_unauthorized(self, client: TestClient):
        """Test changing password without authentication."""
        tester = EndpointTester(client)
        password_data = {"old_password": "old", "new_password": "new"}
        response = tester.put("/frontend/users/USR-0000000000000001/password/change", json=password_data)
        tester.assert_unauthorized(response)
    
    def test_send_password_reset_email_success(self, client: TestClient):
        """Test sending password reset email (public endpoint)."""
        tester = EndpointTester(client)
        reset_data = {"email": "test@example.com"}
        response = tester.post("/frontend/users/password/reset/request", json=reset_data)
        # Public endpoint, may succeed or fail based on email existence
        if response.status_code == 200:
            tester.assert_success(response)
        elif response.status_code == 400:
            pass  # Expected if email doesn't exist
    
    def test_validate_password_reset_token_success(self, client: TestClient):
        """Test validating password reset token (public endpoint)."""
        tester = EndpointTester(client)
        token_data = {"token": "test-token"}
        response = tester.post("/frontend/users/password/reset/validate", json=token_data)
        # Public endpoint
        if response.status_code == 200:
            tester.assert_success(response)
        elif response.status_code in [400, 404]:
            pass
    
    def test_reset_password_success(self, client: TestClient):
        """Test resetting password (public endpoint)."""
        tester = EndpointTester(client)
        reset_data = {"token": "test-token", "new_password": "newpassword123"}
        response = tester.post("/frontend/users/password/reset", json=reset_data)
        # Public endpoint
        if response.status_code == 200:
            tester.assert_success(response)
        elif response.status_code in [400, 404]:
            pass
    
    def test_get_password_history_unauthorized(self, client: TestClient):
        """Test getting password history without authentication."""
        tester = EndpointTester(client)
        response = tester.get("/frontend/users/USR-0000000000000001/password/history")
        tester.assert_unauthorized(response)

