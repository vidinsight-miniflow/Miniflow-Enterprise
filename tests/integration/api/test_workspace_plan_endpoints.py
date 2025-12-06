"""Test workspace plan endpoints."""

import pytest
from fastapi.testclient import TestClient
from tests.fixtures.endpoint_test_helpers import EndpointTester


class TestWorkspacePlanEndpoints:
    """Test workspace plan endpoints."""
    
    def test_get_all_workspace_plans_unauthorized(self, client: TestClient):
        """Test getting all workspace plans without authentication."""
        tester = EndpointTester(client)
        response = tester.get("/frontend/workspace-plans")
        tester.assert_unauthorized(response)
    
    def test_get_workspace_plan_by_id_unauthorized(self, client: TestClient):
        """Test getting workspace plan by ID without authentication."""
        tester = EndpointTester(client)
        response = tester.get("/frontend/workspace-plans/PLN-0000000000000001")
        tester.assert_unauthorized(response)
    
    def test_get_workspace_plan_by_name_unauthorized(self, client: TestClient):
        """Test getting workspace plan by name without authentication."""
        tester = EndpointTester(client)
        response = tester.get("/frontend/workspace-plans/name/free")
        tester.assert_unauthorized(response)
    
    def test_get_workspace_limits_unauthorized(self, client: TestClient):
        """Test getting workspace limits without authentication."""
        tester = EndpointTester(client)
        response = tester.get("/frontend/workspace-plans/PLN-0000000000000001/limits")
        tester.assert_unauthorized(response)
    
    def test_get_monthly_limits_unauthorized(self, client: TestClient):
        """Test getting monthly limits without authentication."""
        tester = EndpointTester(client)
        response = tester.get("/frontend/workspace-plans/PLN-0000000000000001/monthly-limits")
        tester.assert_unauthorized(response)
    
    def test_get_feature_flags_unauthorized(self, client: TestClient):
        """Test getting feature flags without authentication."""
        tester = EndpointTester(client)
        response = tester.get("/frontend/workspace-plans/PLN-0000000000000001/features")
        tester.assert_unauthorized(response)
    
    def test_get_api_limits_unauthorized(self, client: TestClient):
        """Test getting API limits without authentication."""
        tester = EndpointTester(client)
        response = tester.get("/frontend/workspace-plans/PLN-0000000000000001/api-limits")
        tester.assert_unauthorized(response)
    
    def test_get_pricing_unauthorized(self, client: TestClient):
        """Test getting pricing without authentication."""
        tester = EndpointTester(client)
        response = tester.get("/frontend/workspace-plans/PLN-0000000000000001/pricing")
        tester.assert_unauthorized(response)
    
    def test_get_all_api_rate_limits_unauthorized(self, client: TestClient):
        """Test getting all API rate limits without authentication."""
        tester = EndpointTester(client)
        response = tester.get("/frontend/workspace-plans/api-rate-limits/all")
        tester.assert_unauthorized(response)

