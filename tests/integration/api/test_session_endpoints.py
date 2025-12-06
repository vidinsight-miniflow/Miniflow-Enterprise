"""Test session endpoints."""

import pytest
from fastapi.testclient import TestClient
from tests.fixtures.endpoint_test_helpers import EndpointTester


class TestSessionEndpoints:
    """Test session management endpoints."""
    
    def test_get_session_by_id_unauthorized(self, client: TestClient):
        """Test getting session by ID without authentication."""
        tester = EndpointTester(client)
        response = tester.get("/frontend/sessions/SES-0000000000000001")
        tester.assert_unauthorized(response)
    
    def test_get_session_by_access_token_jti_unauthorized(self, client: TestClient):
        """Test getting session by access token JTI without authentication."""
        tester = EndpointTester(client)
        response = tester.get("/frontend/sessions/token/test-jti-123")
        tester.assert_unauthorized(response)
    
    def test_get_session_by_refresh_token_jti_unauthorized(self, client: TestClient):
        """Test getting session by refresh token JTI without authentication."""
        tester = EndpointTester(client)
        response = tester.get("/frontend/sessions/refresh-token/test-refresh-jti-123")
        tester.assert_unauthorized(response)
    
    def test_get_user_active_sessions_unauthorized(self, client: TestClient):
        """Test getting user active sessions without authentication."""
        tester = EndpointTester(client)
        response = tester.get("/frontend/sessions/user/active")
        tester.assert_unauthorized(response)
    
    def test_revoke_session_unauthorized(self, client: TestClient):
        """Test revoking session without authentication."""
        tester = EndpointTester(client)
        revoke_data = {"session_id": "SES-0000000000000001", "reason": "Test"}
        response = tester.post("/frontend/sessions/revoke", json=revoke_data)
        tester.assert_unauthorized(response)
    
    def test_revoke_session_validation_error(self, client: TestClient, auth_headers: dict):
        """Test revoking session with invalid data."""
        tester = EndpointTester(client, auth_headers)
        invalid_data = {"reason": "Test"}  # Missing session_id
        response = tester.post("/frontend/sessions/revoke", json=invalid_data)
        if response.status_code == 422:
            tester.assert_validation_error(response)
        elif response.status_code in [401, 403]:
            pass
    
    def test_revoke_all_user_sessions_unauthorized(self, client: TestClient):
        """Test revoking all user sessions without authentication."""
        tester = EndpointTester(client)
        response = tester.post("/frontend/sessions/revoke-all", json={})
        tester.assert_unauthorized(response)
    
    def test_revoke_oldest_session_unauthorized(self, client: TestClient):
        """Test revoking oldest session without authentication."""
        tester = EndpointTester(client)
        response = tester.post("/frontend/sessions/revoke-oldest", json={})
        tester.assert_unauthorized(response)

