"""Test script testing endpoints."""

import pytest
from fastapi.testclient import TestClient
from tests.fixtures.endpoint_test_helpers import EndpointTester


class TestScriptTestingEndpoints:
    """Test script testing endpoints."""
    
    def test_mark_test_passed_unauthorized(self, client: TestClient):
        """Test marking test as passed without authentication."""
        tester = EndpointTester(client)
        test_data = {"test_result": "All tests passed"}
        response = tester.post("/frontend/workspaces/WSP-0000000000000001/scripts/SCR-0000000000000001/test/passed", json=test_data)
        tester.assert_unauthorized(response)
    
    def test_mark_test_failed_unauthorized(self, client: TestClient):
        """Test marking test as failed without authentication."""
        tester = EndpointTester(client)
        test_data = {"error_message": "Test failed"}
        response = tester.post("/frontend/workspaces/WSP-0000000000000001/scripts/SCR-0000000000000001/test/failed", json=test_data)
        tester.assert_unauthorized(response)
    
    def test_mark_test_skipped_unauthorized(self, client: TestClient):
        """Test marking test as skipped without authentication."""
        tester = EndpointTester(client)
        test_data = {"reason": "Not applicable"}
        response = tester.post("/frontend/workspaces/WSP-0000000000000001/scripts/SCR-0000000000000001/test/skipped", json=test_data)
        tester.assert_unauthorized(response)
    
    def test_reset_test_status_unauthorized(self, client: TestClient):
        """Test resetting test status without authentication."""
        tester = EndpointTester(client)
        response = tester.post("/frontend/workspaces/WSP-0000000000000001/scripts/SCR-0000000000000001/test/reset", json={})
        tester.assert_unauthorized(response)
    
    def test_get_test_status_unauthorized(self, client: TestClient):
        """Test getting test status without authentication."""
        tester = EndpointTester(client)
        response = tester.get("/frontend/workspaces/WSP-0000000000000001/scripts/SCR-0000000000000001/test/status")
        tester.assert_unauthorized(response)
    
    def test_get_untested_scripts_unauthorized(self, client: TestClient):
        """Test getting untested scripts without authentication."""
        tester = EndpointTester(client)
        response = tester.get("/frontend/workspaces/WSP-0000000000000001/scripts/untested")
        tester.assert_unauthorized(response)
    
    def test_get_failed_scripts_unauthorized(self, client: TestClient):
        """Test getting failed scripts without authentication."""
        tester = EndpointTester(client)
        response = tester.get("/frontend/workspaces/WSP-0000000000000001/scripts/failed")
        tester.assert_unauthorized(response)
    
    def test_update_test_results_unauthorized(self, client: TestClient):
        """Test updating test results without authentication."""
        tester = EndpointTester(client)
        results_data = {"passed": 10, "failed": 2, "skipped": 1}
        response = tester.put("/frontend/workspaces/WSP-0000000000000001/scripts/SCR-0000000000000001/test/results", json=results_data)
        tester.assert_unauthorized(response)
    
    def test_update_test_coverage_unauthorized(self, client: TestClient):
        """Test updating test coverage without authentication."""
        tester = EndpointTester(client)
        coverage_data = {"coverage_percentage": 85.5}
        response = tester.put("/frontend/workspaces/WSP-0000000000000001/scripts/SCR-0000000000000001/test/coverage", json=coverage_data)
        tester.assert_unauthorized(response)

