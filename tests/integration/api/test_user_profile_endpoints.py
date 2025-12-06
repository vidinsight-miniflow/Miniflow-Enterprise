"""Test user profile endpoints."""

import pytest
from fastapi.testclient import TestClient
from tests.fixtures.endpoint_test_helpers import EndpointTester


class TestUserProfileEndpoints:
    """Test user profile endpoints."""
    
    def test_update_profile_unauthorized(self, client: TestClient):
        """Test updating profile without authentication."""
        tester = EndpointTester(client)
        profile_data = {"name": "Test", "surname": "User"}
        response = tester.put("/frontend/users/USR-0000000000000001/profile", json=profile_data)
        tester.assert_unauthorized(response)
    
    def test_change_username_unauthorized(self, client: TestClient):
        """Test changing username without authentication."""
        tester = EndpointTester(client)
        username_data = {"new_username": "newusername"}
        response = tester.put("/frontend/users/USR-0000000000000001/username", json=username_data)
        tester.assert_unauthorized(response)
    
    def test_change_email_unauthorized(self, client: TestClient):
        """Test changing email without authentication."""
        tester = EndpointTester(client)
        email_data = {"new_email": "new@example.com"}
        response = tester.put("/frontend/users/USR-0000000000000001/email", json=email_data)
        tester.assert_unauthorized(response)
    
    def test_change_phone_unauthorized(self, client: TestClient):
        """Test changing phone without authentication."""
        tester = EndpointTester(client)
        phone_data = {"country_code": "+1", "phone_number": "1234567890"}
        response = tester.put("/frontend/users/USR-0000000000000001/phone", json=phone_data)
        tester.assert_unauthorized(response)
    
    def test_verify_phone_unauthorized(self, client: TestClient):
        """Test verifying phone without authentication."""
        tester = EndpointTester(client)
        verify_data = {"verification_code": "123456"}
        response = tester.post("/frontend/users/USR-0000000000000001/phone/verify", json=verify_data)
        tester.assert_unauthorized(response)

