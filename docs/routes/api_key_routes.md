# API Key Routes API Documentation

## Base URL
```
{{base_url}}/frontend/workspaces
```

## Endpoints

### 1. Validate API Key

Validate API key.

**Endpoint:** `POST {{base_url}}/frontend/workspaces/api-keys/validate`

**Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "full_api_key": "sk_live_1234567890abcdef",
  "client_ip": "192.168.1.1"
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": null,
  "traceId": "{{trace_id}}",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "valid": true,
    "workspace_id": "WSP-1234567890ABCDEF",
    "api_key_id": "AKY-1234567890ABCDEF",
    "permissions": {
      "workflow.read": true,
      "workflow.execute": true
    },
    "workspace_plan_id": "WPL-1234567890ABCDEF"
  }
}
```

**Error Responses:**
- `400 Bad Request` - Invalid API key
- `422 Validation Error` - Validation failed
- `500 Internal Server Error` - Server error

---

### 2. Create API Key

Create a new API key.

**Endpoint:** `POST {{base_url}}/frontend/workspaces/{{workspace_id}}/api-keys`

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
  "name": "Production API Key",
  "description": "API key for production environment",
  "permissions": {
    "workflow.read": true,
    "workflow.execute": true
  },
  "expires_at": "2025-01-01T00:00:00Z",
  "tags": ["production", "api"],
  "allowed_ips": ["192.168.1.1"],
  "key_prefix": "sk_live_"
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "API key created successfully. Save it now - it won't be shown again!",
  "traceId": "{{trace_id}}",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "id": "AKY-1234567890ABCDEF",
    "api_key": "sk_live_1234567890abcdef"
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Workspace access denied
- `400 Bad Request` - API key limit exceeded or name already exists
- `422 Validation Error` - Validation failed
- `500 Internal Server Error` - Server error

---

### 3. Get API Key

Get API key details.

**Endpoint:** `GET {{base_url}}/frontend/workspaces/{{workspace_id}}/api-keys/{{api_key_id}}`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `workspace_id` (string, required) - Workspace ID
- `api_key_id` (string, required) - API key ID

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
    "id": "AKY-1234567890ABCDEF",
    "workspace_id": "WSP-1234567890ABCDEF",
    "owner_id": "USR-1234567890ABCDEF",
    "name": "Production API Key",
    "api_key_masked": "sk_live_****",
    "description": "API key for production environment",
    "permissions": {
      "workflow.read": true,
      "workflow.execute": true
    },
    "is_active": true,
    "expires_at": "2025-01-01T00:00:00Z",
    "last_used_at": "2024-01-01T00:30:00Z",
    "usage_count": 150,
    "allowed_ips": ["192.168.1.1"],
    "tags": ["production", "api"],
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Workspace access denied
- `404 Not Found` - API key not found
- `500 Internal Server Error` - Server error

---

### 4. Get Workspace API Keys

Get all workspace API keys.

**Endpoint:** `GET {{base_url}}/frontend/workspaces/{{workspace_id}}/api-keys`

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
    "api_keys": [
      {
        "id": "AKY-1234567890ABCDEF",
        "name": "Production API Key",
        "api_key_masked": "sk_live_****",
        "description": "API key for production environment",
        "is_active": true,
        "expires_at": "2025-01-01T00:00:00Z",
        "last_used_at": "2024-01-01T00:30:00Z",
        "usage_count": 150
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

### 5. Update API Key

Update API key metadata.

**Endpoint:** `PUT {{base_url}}/frontend/workspaces/{{workspace_id}}/api-keys/{{api_key_id}}`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `workspace_id` (string, required) - Workspace ID
- `api_key_id` (string, required) - API key ID

**Request Body:**
```json
{
  "name": "Updated Production API Key",
  "description": "Updated description",
  "permissions": {
    "workflow.read": true,
    "workflow.execute": true,
    "workflow.create": false
  },
  "tags": ["production", "api", "updated"],
  "allowed_ips": ["192.168.1.1", "192.168.1.2"],
  "expires_at": "2026-01-01T00:00:00Z"
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "API key updated successfully.",
  "traceId": "{{trace_id}}",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "id": "AKY-1234567890ABCDEF",
    "workspace_id": "WSP-1234567890ABCDEF",
    "owner_id": "USR-1234567890ABCDEF",
    "name": "Updated Production API Key",
    "api_key_masked": "sk_live_****",
    "description": "Updated description",
    "permissions": {
      "workflow.read": true,
      "workflow.execute": true,
      "workflow.create": false
    },
    "is_active": true,
    "expires_at": "2026-01-01T00:00:00Z",
    "last_used_at": "2024-01-01T00:30:00Z",
    "usage_count": 150,
    "allowed_ips": ["192.168.1.1", "192.168.1.2"],
    "tags": ["production", "api", "updated"],
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Workspace access denied
- `404 Not Found` - API key not found
- `422 Validation Error` - Validation failed
- `500 Internal Server Error` - Server error

---

### 6. Activate API Key

Activate API key.

**Endpoint:** `POST {{base_url}}/frontend/workspaces/{{workspace_id}}/api-keys/{{api_key_id}}/activate`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `workspace_id` (string, required) - Workspace ID
- `api_key_id` (string, required) - API key ID

**Request Body:**
None

**Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "API key activated successfully.",
  "traceId": "{{trace_id}}",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "success": true,
    "is_active": true
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Workspace access denied
- `404 Not Found` - API key not found
- `500 Internal Server Error` - Server error

---

### 7. Deactivate API Key

Deactivate API key.

**Endpoint:** `POST {{base_url}}/frontend/workspaces/{{workspace_id}}/api-keys/{{api_key_id}}/deactivate`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `workspace_id` (string, required) - Workspace ID
- `api_key_id` (string, required) - API key ID

**Request Body:**
None

**Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "API key deactivated successfully.",
  "traceId": "{{trace_id}}",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "success": true,
    "is_active": false
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Workspace access denied
- `404 Not Found` - API key not found
- `500 Internal Server Error` - Server error

---

### 8. Delete API Key

Delete API key.

**Endpoint:** `DELETE {{base_url}}/frontend/workspaces/{{workspace_id}}/api-keys/{{api_key_id}}`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `workspace_id` (string, required) - Workspace ID
- `api_key_id` (string, required) - API key ID

**Request Body:**
None

**Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "API key deleted successfully.",
  "traceId": "{{trace_id}}",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "success": true,
    "deleted_id": "AKY-1234567890ABCDEF"
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Workspace access denied
- `404 Not Found` - API key not found
- `500 Internal Server Error` - Server error

