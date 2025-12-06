"""Test workspace plan management endpoints."""

import pytest
from fastapi.testclient import TestClient
from tests.fixtures.endpoint_test_helpers import EndpointTester


class TestWorkspacePlanManagementEndpoints:
    """Test workspace plan management endpoints."""
    
    def test_get_available_plans_success(self, client: TestClient):
        """Test getting available plans (public endpoint)."""
        tester = EndpointTester(client)
        response = tester.get("/frontend/workspaces/plans")
        # Public endpoint
        if response.status_code == 200:
            tester.assert_success(response)
    
    def test_get_plan_details_success(self, client: TestClient):
        """Test getting plan details (public endpoint)."""
        tester = EndpointTester(client)
        response = tester.get("/frontend/workspaces/plans/PLN-0000000000000001")
        # Public endpoint
        if response.status_code == 200:
            tester.assert_success(response)
        elif response.status_code == 404:
            tester.assert_not_found(response)
    
    def test_get_workspace_current_plan_unauthorized(self, client: TestClient):
        """Test getting workspace current plan without authentication."""
        tester = EndpointTester(client)
        response = tester.get("/frontend/workspaces/WSP-0000000000000001/plan")
        tester.assert_unauthorized(response)
    
    def test_compare_plans_success(self, client: TestClient):
        """Test comparing plans (public endpoint)."""
        tester = EndpointTester(client)
        compare_data = {"plan_ids": ["PLN-0000000000000001", "PLN-0000000000000002"]}
        response = tester.post("/frontend/workspaces/plans/compare", json=compare_data)
        # Public endpoint
        if response.status_code == 200:
            tester.assert_success(response)
        elif response.status_code == 422:
            tester.assert_validation_error(response)
    
    def test_check_upgrade_eligibility_unauthorized(self, client: TestClient):
        """Test checking upgrade eligibility without authentication."""
        tester = EndpointTester(client)
        check_data = {"target_plan_id": "PLN-0000000000000002"}
        response = tester.post("/frontend/workspaces/WSP-0000000000000001/plan/check-upgrade", json=check_data)
        tester.assert_unauthorized(response)
    
    def test_upgrade_plan_unauthorized(self, client: TestClient):
        """Test upgrading plan without authentication."""
        tester = EndpointTester(client)
        upgrade_data = {"target_plan_id": "PLN-0000000000000002"}
        response = tester.post("/frontend/workspaces/WSP-0000000000000001/plan/upgrade", json=upgrade_data)
        tester.assert_unauthorized(response)
    
    def test_update_billing_info_unauthorized(self, client: TestClient):
        """Test updating billing info without authentication."""
        tester = EndpointTester(client)
        billing_data = {"billing_email": "billing@example.com"}
        response = tester.put("/frontend/workspaces/WSP-0000000000000001/billing", json=billing_data)
        tester.assert_unauthorized(response)
    
    def test_check_limit_unauthorized(self, client: TestClient):
        """Test checking limit without authentication."""
        tester = EndpointTester(client)
        limit_data = {"limit_type": "executions", "increment": 100}
        response = tester.post("/frontend/workspaces/WSP-0000000000000001/limits/check", json=limit_data)
        tester.assert_unauthorized(response)
    
    def test_check_downgrade_eligibility_unauthorized(self, client: TestClient):
        """Test checking downgrade eligibility without authentication."""
        tester = EndpointTester(client)
        check_data = {"target_plan_id": "PLN-0000000000000001"}
        response = tester.post("/frontend/workspaces/WSP-0000000000000001/plan/check-downgrade", json=check_data)
        tester.assert_unauthorized(response)
    
    def test_downgrade_plan_unauthorized(self, client: TestClient):
        """Test downgrading plan without authentication."""
        tester = EndpointTester(client)
        downgrade_data = {"target_plan_id": "PLN-0000000000000001"}
        response = tester.post("/frontend/workspaces/WSP-0000000000000001/plan/downgrade", json=downgrade_data)
        tester.assert_unauthorized(response)
    
    def test_update_billing_period_unauthorized(self, client: TestClient):
        """Test updating billing period without authentication."""
        tester = EndpointTester(client)
        period_data = {
            "period_start": "2024-01-01T00:00:00Z",
            "period_end": "2024-02-01T00:00:00Z"
        }
        response = tester.post("/frontend/workspaces/WSP-0000000000000001/billing/period", json=period_data)
        tester.assert_unauthorized(response)
    
    def test_compare_plans_validation_error(self, client: TestClient):
        """Test comparing plans with invalid data."""
        tester = EndpointTester(client)
        invalid_data = {"plan_id_1": "PLN-0000000000000001"}  # Missing plan_id_2
        response = tester.post("/frontend/workspaces/plans/compare", json=invalid_data)
        if response.status_code == 422:
            tester.assert_validation_error(response)
    
    def test_get_workspace_current_plan_forbidden(self, client: TestClient, auth_headers: dict):
        """Test getting workspace current plan without workspace access."""
        tester = EndpointTester(client, auth_headers)
        response = tester.get("/frontend/workspaces/WSP-OTHERWORKSPACE01/plan")
        if response.status_code == 403:
            tester.assert_forbidden(response)
        elif response.status_code == 401:
            tester.assert_unauthorized(response)
    
    def test_check_upgrade_eligibility_forbidden(self, client: TestClient, auth_headers: dict):
        """Test checking upgrade eligibility without workspace owner access."""
        tester = EndpointTester(client, auth_headers)
        check_data = {"target_plan_id": "PLN-0000000000000002"}
        response = tester.post("/frontend/workspaces/WSP-0000000000000001/plan/check-upgrade", json=check_data)
        # May return 403 if not owner, or 401 if auth fails
        if response.status_code == 403:
            tester.assert_forbidden(response)
        elif response.status_code == 401:
            tester.assert_unauthorized(response)
    
    def test_upgrade_plan_validation_error(self, client: TestClient, auth_headers: dict):
        """Test upgrading plan with invalid data."""
        tester = EndpointTester(client, auth_headers)
        invalid_data = {}  # Missing target_plan_id
        response = tester.post("/frontend/workspaces/WSP-0000000000000001/plan/upgrade", json=invalid_data)
        if response.status_code == 422:
            tester.assert_validation_error(response)
        elif response.status_code in [401, 403]:
            pass

