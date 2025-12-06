"""Test login history endpoints."""

import pytest
from fastapi.testclient import TestClient
from tests.fixtures.endpoint_test_helpers import EndpointTester


class TestLoginHistoryEndpoints:
    """Test login history endpoints."""
    
    def test_get_user_login_history_unauthorized(self, client: TestClient):
        """Test getting user login history without authentication."""
        tester = EndpointTester(client)
        response = tester.get("/frontend/login-history/user")
        tester.assert_unauthorized(response)
    
    def test_get_login_history_by_id_unauthorized(self, client: TestClient):
        """Test getting login history by ID without authentication."""
        tester = EndpointTester(client)
        response = tester.get("/frontend/login-history/LHI-0000000000000001")
        tester.assert_unauthorized(response)
    
    def test_check_rate_limit_unauthorized(self, client: TestClient):
        """Test checking rate limit without authentication."""
        tester = EndpointTester(client)
        response = tester.get("/frontend/login-history/user/rate-limit-check")
        tester.assert_unauthorized(response)

