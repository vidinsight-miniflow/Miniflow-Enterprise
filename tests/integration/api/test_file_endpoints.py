"""Test file endpoints."""

import pytest
from fastapi.testclient import TestClient
from tests.fixtures.endpoint_test_helpers import EndpointTester
from io import BytesIO


class TestFileEndpoints:
    """Test file endpoints."""
    
    def test_upload_file_unauthorized(self, client: TestClient):
        """Test uploading file without authentication."""
        tester = EndpointTester(client)
        file_data = BytesIO(b"test file content")
        files = {"file": ("test.txt", file_data, "text/plain")}
        response = tester.client.post(
            "/frontend/workspaces/WSP-0000000000000001/files",
            files=files,
            headers=tester.base_headers
        )
        assert response.status_code in [401, 403]
    
    def test_get_file_unauthorized(self, client: TestClient):
        """Test getting file without authentication."""
        tester = EndpointTester(client)
        response = tester.get("/frontend/workspaces/WSP-0000000000000001/files/FIL-0000000000000001")
        tester.assert_unauthorized(response)
    
    def test_get_all_files_unauthorized(self, client: TestClient):
        """Test getting all files without authentication."""
        tester = EndpointTester(client)
        response = tester.get("/frontend/workspaces/WSP-0000000000000001/files")
        tester.assert_unauthorized(response)
    
    def test_download_file_unauthorized(self, client: TestClient):
        """Test downloading file without authentication."""
        tester = EndpointTester(client)
        response = tester.get("/frontend/workspaces/WSP-0000000000000001/files/FIL-0000000000000001/download")
        tester.assert_unauthorized(response)
    
    def test_update_file_unauthorized(self, client: TestClient):
        """Test updating file without authentication."""
        tester = EndpointTester(client)
        file_data = {"name": "Updated File"}
        response = tester.put("/frontend/workspaces/WSP-0000000000000001/files/FIL-0000000000000001", json=file_data)
        tester.assert_unauthorized(response)
    
    def test_delete_file_unauthorized(self, client: TestClient):
        """Test deleting file without authentication."""
        tester = EndpointTester(client)
        response = tester.delete("/frontend/workspaces/WSP-0000000000000001/files/FIL-0000000000000001")
        tester.assert_unauthorized(response)

