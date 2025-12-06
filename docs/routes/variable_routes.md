# Variable Routes API Documentation

## Base URL
```
{{base_url}}/frontend/workspaces
```

## Endpoints

### 1. Create Variable

Create a new environment variable.

**Endpoint:** `POST {{base_url}}/frontend/workspaces/{{workspace_id}}/variables`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `workspace_id` (string, required) - Workspace ID

**Request Body:**
```json
{
  "key": "API_KEY",
  "value": "secret-value-123",
  "description": "API key for external service",
  "is_secret": true
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "Variable created successfully.",
  "traceId": "{{trace_id}}",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "id": "VAR-1234567890ABCDEF"
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Workspace access denied
- `400 Bad Request` - Variable key already exists
- `422 Validation Error` - Validation failed
- `500 Internal Server Error` - Server error

---

### 2. Get Variable

Get variable details.

**Endpoint:** `GET {{base_url}}/frontend/workspaces/{{workspace_id}}/variables/{{variable_id}}`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `workspace_id` (string, required) - Workspace ID
- `variable_id` (string, required) - Variable ID

**Query Parameters:**
- `decrypt_secret` (boolean, optional, default: false) - Decrypt secret value

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
    "id": "VAR-1234567890ABCDEF",
    "workspace_id": "WSP-1234567890ABCDEF",
    "owner_id": "USR-1234567890ABCDEF",
    "key": "API_KEY",
    "value": "secret-value-123",
    "description": "API key for external service",
    "is_secret": true,
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Workspace access denied
- `404 Not Found` - Variable not found
- `500 Internal Server Error` - Server error

---

### 3. Get Variable by Key

Get variable by key.

**Endpoint:** `GET {{base_url}}/frontend/workspaces/{{workspace_id}}/variables/key/{{key}}`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `workspace_id` (string, required) - Workspace ID
- `key` (string, required) - Variable key

**Query Parameters:**
- `decrypt_secret` (boolean, optional, default: false) - Decrypt secret value

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
    "id": "VAR-1234567890ABCDEF",
    "workspace_id": "WSP-1234567890ABCDEF",
    "owner_id": "USR-1234567890ABCDEF",
    "key": "API_KEY",
    "value": "secret-value-123",
    "description": "API key for external service",
    "is_secret": true,
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Workspace access denied
- `404 Not Found` - Variable not found
- `500 Internal Server Error` - Server error

---

### 4. Get Workspace Variables

Get all workspace variables.

**Endpoint:** `GET {{base_url}}/frontend/workspaces/{{workspace_id}}/variables`

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
    "variables": [
      {
        "id": "VAR-1234567890ABCDEF",
        "key": "API_KEY",
        "value": "****",
        "description": "API key for external service",
        "is_secret": true,
        "created_at": "2024-01-01T00:00:00Z"
      }
    ],
    "count": 1
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Workspace access denied
- `500 Internal Server Error` - Server error

---

### 5. Update Variable

Update variable.

**Endpoint:** `PUT {{base_url}}/frontend/workspaces/{{workspace_id}}/variables/{{variable_id}}`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `workspace_id` (string, required) - Workspace ID
- `variable_id` (string, required) - Variable ID

**Request Body:**
```json
{
  "key": "UPDATED_API_KEY",
  "value": "new-secret-value",
  "description": "Updated description",
  "is_secret": true
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "Variable updated successfully.",
  "traceId": "{{trace_id}}",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "id": "VAR-1234567890ABCDEF",
    "workspace_id": "WSP-1234567890ABCDEF",
    "owner_id": "USR-1234567890ABCDEF",
    "key": "UPDATED_API_KEY",
    "value": "new-secret-value",
    "description": "Updated description",
    "is_secret": true,
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Workspace access denied
- `404 Not Found` - Variable not found
- `400 Bad Request` - Variable key already exists
- `422 Validation Error` - Validation failed
- `500 Internal Server Error` - Server error

---

### 6. Delete Variable

Delete variable.

**Endpoint:** `DELETE {{base_url}}/frontend/workspaces/{{workspace_id}}/variables/{{variable_id}}`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `workspace_id` (string, required) - Workspace ID
- `variable_id` (string, required) - Variable ID

**Request Body:**
None

**Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "Variable deleted successfully.",
  "traceId": "{{trace_id}}",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "success": true,
    "deleted_id": "VAR-1234567890ABCDEF"
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Workspace access denied
- `404 Not Found` - Variable not found
- `500 Internal Server Error` - Server error

