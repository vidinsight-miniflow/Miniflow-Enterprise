"""Endpoint test helper utilities."""

from typing import Dict, Any, Optional
from fastapi.testclient import TestClient


class EndpointTester:
    """Helper class for endpoint testing."""
    
    def __init__(self, client: TestClient, base_headers: Optional[Dict] = None):
        self.client = client
        self.base_headers = base_headers or {}
    
    def assert_success(self, response, expected_status: int = 200) -> Dict[str, Any]:
        """Assert successful response."""
        assert response.status_code == expected_status, (
            f"Expected status {expected_status}, got {response.status_code}. "
            f"Response: {response.text}"
        )
        data = response.json()
        assert data["success"] is True, f"Expected success=True, got {data.get('success')}. Response: {data}"
        assert "data" in data, f"Expected 'data' key in response. Response: {data}"
        return data["data"]
    
    def assert_error(self, response, expected_status: int, error_code: Optional[str] = None) -> Dict[str, Any]:
        """Assert error response."""
        assert response.status_code == expected_status, (
            f"Expected status {expected_status}, got {response.status_code}. "
            f"Response: {response.text}"
        )
        data = response.json()
        # Check both 'success' and 'status' keys (different error formats)
        if "success" in data:
            assert data["success"] is False, f"Expected success=False, got {data.get('success')}. Response: {data}"
        elif "status" in data:
            assert data["status"] in ["error", "failed"], f"Expected status='error' or 'failed', got {data.get('status')}. Response: {data}"
        if error_code:
            assert data.get("error_code") == error_code, (
                f"Expected error_code={error_code}, got {data.get('error_code')}. Response: {data}"
            )
        return data
    
    def assert_unauthorized(self, response) -> Dict[str, Any]:
        """Assert unauthorized response (401 or 403).
        
        Note: FastAPI HTTPBearer returns 403 when no token is provided,
        so we accept both 401 and 403 as unauthorized responses.
        """
        assert response.status_code in [401, 403], (
            f"Expected status 401 or 403, got {response.status_code}. "
            f"Response: {response.text}"
        )
        return response.json()
    
    def assert_forbidden(self, response) -> Dict[str, Any]:
        """Assert forbidden response (403)."""
        return self.assert_error(response, 403)
    
    def assert_not_found(self, response) -> Dict[str, Any]:
        """Assert not found response (404)."""
        return self.assert_error(response, 404)
    
    def assert_validation_error(self, response) -> Dict[str, Any]:
        """Assert validation error (422)."""
        assert response.status_code == 422, (
            f"Expected status 422, got {response.status_code}. Response: {response.text}"
        )
        return response.json()
    
    def get(self, url: str, headers: Optional[Dict] = None, **kwargs):
        """GET request with base headers."""
        merged_headers = {**self.base_headers, **(headers or {})}
        return self.client.get(url, headers=merged_headers, **kwargs)
    
    def post(self, url: str, json: Dict, headers: Optional[Dict] = None, **kwargs):
        """POST request with base headers."""
        merged_headers = {**self.base_headers, **(headers or {})}
        return self.client.post(url, json=json, headers=merged_headers, **kwargs)
    
    def put(self, url: str, json: Optional[Dict] = None, headers: Optional[Dict] = None, **kwargs):
        """PUT request with base headers.
        
        Args:
            url: Request URL
            json: Optional JSON body (None for empty body)
            headers: Optional additional headers
            **kwargs: Additional arguments for client.put()
        """
        merged_headers = {**self.base_headers, **(headers or {})}
        if json is not None:
            return self.client.put(url, json=json, headers=merged_headers, **kwargs)
        else:
            return self.client.put(url, headers=merged_headers, **kwargs)
    
    def delete(self, url: str, headers: Optional[Dict] = None, **kwargs):
        """DELETE request with base headers."""
        merged_headers = {**self.base_headers, **(headers or {})}
        return self.client.delete(url, headers=merged_headers, **kwargs)

