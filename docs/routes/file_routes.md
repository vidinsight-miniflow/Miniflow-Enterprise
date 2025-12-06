# File Routes API Documentation

## Base URL
```
{{base_url}}/frontend/workspaces
```

## Endpoints

### 1. Upload File

Upload a file.

**Endpoint:** `POST {{base_url}}/frontend/workspaces/{{workspace_id}}/files`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: multipart/form-data
```

**Path Parameters:**
- `workspace_id` (string, required) - Workspace ID

**Form Data:**
- `file` (file, required) - File to upload
- `name` (string, optional) - File name (auto-generated if not provided)
- `description` (string, optional) - File description
- `tags` (string, optional) - Tags (comma-separated)

**Request Body:**
```
Content-Type: multipart/form-data

file: [binary file data]
name: "my-file.txt"
description: "File description"
tags: "document,text"
```

**Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "File uploaded successfully.",
  "traceId": "{{trace_id}}",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "id": "FIL-1234567890ABCDEF"
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Workspace access denied
- `400 Bad Request` - File size exceeds limit or storage limit exceeded
- `422 Validation Error` - Validation failed
- `500 Internal Server Error` - Server error

---

### 2. Get File

Get file details.

**Endpoint:** `GET {{base_url}}/frontend/workspaces/{{workspace_id}}/files/{{file_id}}`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `workspace_id` (string, required) - Workspace ID
- `file_id` (string, required) - File ID

**Request Body:**
None

**Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": null,
  "traceId": "{{trace_id}}",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "id": "FIL-1234567890ABCDEF",
    "workspace_id": "WSP-1234567890ABCDEF",
    "owner_id": "USR-1234567890ABCDEF",
    "name": "my-file.txt",
    "original_filename": "my-file.txt",
    "file_size": 1024,
    "file_size_mb": 0.001,
    "mime_type": "text/plain",
    "file_extension": ".txt",
    "description": "File description",
    "tags": ["document", "text"],
    "file_metadata": null,
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Workspace access denied
- `404 Not Found` - File not found
- `500 Internal Server Error` - Server error

---

### 3. Get Workspace Files

Get all workspace files.

**Endpoint:** `GET {{base_url}}/frontend/workspaces/{{workspace_id}}/files`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `workspace_id` (string, required) - Workspace ID

**Request Body:**
None

**Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": null,
  "traceId": "{{trace_id}}",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "workspace_id": "WSP-1234567890ABCDEF",
    "files": [
      {
        "id": "FIL-1234567890ABCDEF",
        "name": "my-file.txt",
        "original_filename": "my-file.txt",
        "file_size": 1024,
        "file_size_mb": 0.001,
        "mime_type": "text/plain",
        "file_extension": ".txt",
        "description": "File description",
        "tags": ["document", "text"],
        "created_at": "2024-01-01T00:00:00Z"
      }
    ],
    "count": 1,
    "total_size_bytes": 1024,
    "total_size_mb": 0.001
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Workspace access denied
- `500 Internal Server Error` - Server error

---

### 4. Download File

Download file content.

**Endpoint:** `GET {{base_url}}/frontend/workspaces/{{workspace_id}}/files/{{file_id}}/download`

**Headers:**
```
Authorization: Bearer {{access_token}}
```

**Path Parameters:**
- `workspace_id` (string, required) - Workspace ID
- `file_id` (string, required) - File ID

**Request Body:**
None

**Response (200 OK):**
```
Content-Type: [file mime type]
Content-Disposition: attachment; filename="my-file.txt"

[binary file content]
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Workspace access denied
- `404 Not Found` - File not found
- `500 Internal Server Error` - Server error

---

### 5. Update File

Update file metadata.

**Endpoint:** `PUT {{base_url}}/frontend/workspaces/{{workspace_id}}/files/{{file_id}}`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `workspace_id` (string, required) - Workspace ID
- `file_id` (string, required) - File ID

**Request Body:**
```json
{
  "name": "updated-file.txt",
  "description": "Updated description",
  "tags": ["document", "text", "updated"]
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "File metadata updated successfully.",
  "traceId": "{{trace_id}}",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "id": "FIL-1234567890ABCDEF",
    "workspace_id": "WSP-1234567890ABCDEF",
    "owner_id": "USR-1234567890ABCDEF",
    "name": "updated-file.txt",
    "original_filename": "my-file.txt",
    "file_size": 1024,
    "file_size_mb": 0.001,
    "mime_type": "text/plain",
    "file_extension": ".txt",
    "description": "Updated description",
    "tags": ["document", "text", "updated"],
    "file_metadata": null,
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Workspace access denied
- `404 Not Found` - File not found
- `422 Validation Error` - Validation failed
- `500 Internal Server Error` - Server error

---

### 6. Delete File

Delete file.

**Endpoint:** `DELETE {{base_url}}/frontend/workspaces/{{workspace_id}}/files/{{file_id}}`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `workspace_id` (string, required) - Workspace ID
- `file_id` (string, required) - File ID

**Request Body:**
None

**Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "File deleted successfully.",
  "traceId": "{{trace_id}}",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "success": true,
    "deleted_id": "FIL-1234567890ABCDEF"
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Workspace access denied
- `404 Not Found` - File not found
- `500 Internal Server Error` - Server error

