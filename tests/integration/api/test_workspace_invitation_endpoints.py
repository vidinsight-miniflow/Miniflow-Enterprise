"""Test workspace invitation endpoints."""

import pytest
from fastapi.testclient import TestClient
from tests.fixtures.endpoint_test_helpers import EndpointTester


class TestWorkspaceInvitationEndpoints:
    """Test workspace invitation endpoints."""
    
    def test_get_user_pending_invitations_unauthorized(self, client: TestClient):
        """Test getting user pending invitations without authentication."""
        tester = EndpointTester(client)
        response = tester.get("/frontend/workspaces/user/USR-0000000000000001/invitations/pending")
        tester.assert_unauthorized(response)
    
    def test_get_workspace_invitations_unauthorized(self, client: TestClient):
        """Test getting workspace invitations without authentication."""
        tester = EndpointTester(client)
        response = tester.get("/frontend/workspaces/WSP-0000000000000001/invitations")
        tester.assert_unauthorized(response)
    
    def test_invite_user_unauthorized(self, client: TestClient):
        """Test inviting user without authentication."""
        tester = EndpointTester(client)
        invite_data = {"email": "newuser@example.com", "role_id": "ROL-0000000000000001"}
        response = tester.post("/frontend/workspaces/WSP-0000000000000001/invitations", json=invite_data)
        tester.assert_unauthorized(response)
    
    def test_accept_invitation_unauthorized(self, client: TestClient):
        """Test accepting invitation without authentication."""
        tester = EndpointTester(client)
        response = tester.post("/frontend/workspaces/invitations/INV-0000000000000001/accept", json={})
        tester.assert_unauthorized(response)
    
    def test_decline_invitation_unauthorized(self, client: TestClient):
        """Test declining invitation without authentication."""
        tester = EndpointTester(client)
        response = tester.post("/frontend/workspaces/invitations/INV-0000000000000001/decline", json={})
        tester.assert_unauthorized(response)
    
    def test_cancel_invitation_unauthorized(self, client: TestClient):
        """Test canceling invitation without authentication."""
        tester = EndpointTester(client)
        response = tester.post("/frontend/workspaces/WSP-0000000000000001/invitations/INV-0000000000000001/cancel", json={})
        tester.assert_unauthorized(response)
    
    def test_resend_invitation_unauthorized(self, client: TestClient):
        """Test resending invitation without authentication."""
        tester = EndpointTester(client)
        response = tester.post("/frontend/workspaces/WSP-0000000000000001/invitations/INV-0000000000000001/resend", json={})
        tester.assert_unauthorized(response)

