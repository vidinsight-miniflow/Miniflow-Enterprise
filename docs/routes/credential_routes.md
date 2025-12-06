# Credential Routes API Documentation

## Base URL
```
{{base_url}}/frontend/workspaces
```

## Endpoints

### 1. Create API Key Credential

Create API key credential.

**Endpoint:** `POST {{base_url}}/frontend/workspaces/{{workspace_id}}/credentials/api-key`

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
  "name": "OpenAI API Key",
  "api_key": "sk-1234567890abcdef",
  "provider": "OPENAI",
  "description": "OpenAI API key for GPT models",
  "tags": ["ai", "gpt"],
  "expires_at": "2025-01-01T00:00:00Z"
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "API key credential created successfully.",
  "traceId": "{{trace_id}}",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "id": "CRD-1234567890ABCDEF"
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Workspace access denied
- `400 Bad Request` - Credential name already exists
- `422 Validation Error` - Validation failed
- `500 Internal Server Error` - Server error

---

### 2. Create Slack Credential

Create Slack credential.

**Endpoint:** `POST {{base_url}}/frontend/workspaces/{{workspace_id}}/credentials/slack`

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
  "name": "Slack Workspace",
  "bot_token": "xoxb-1234567890-abcdef",
  "signing_secret": "abc123def456",
  "app_token": "xapp-1234567890-abcdef",
  "description": "Slack workspace credentials",
  "tags": ["slack", "notifications"],
  "expires_at": null
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "Slack credential created successfully.",
  "traceId": "{{trace_id}}",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "id": "CRD-1234567890ABCDEF"
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Workspace access denied
- `400 Bad Request` - Credential name already exists
- `422 Validation Error` - Validation failed
- `500 Internal Server Error` - Server error

---

### 3. Get Credential

Get credential details.

**Endpoint:** `GET {{base_url}}/frontend/workspaces/{{workspace_id}}/credentials/{{credential_id}}`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `workspace_id` (string, required) - Workspace ID
- `credential_id` (string, required) - Credential ID

**Query Parameters:**
- `include_secret` (boolean, optional, default: false) - Include secret data (for workflow execution)

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
    "id": "CRD-1234567890ABCDEF",
    "workspace_id": "WSP-1234567890ABCDEF",
    "owner_id": "USR-1234567890ABCDEF",
    "name": "OpenAI API Key",
    "credential_type": "API_KEY",
    "credential_provider": "OPENAI",
    "description": "OpenAI API key for GPT models",
    "is_active": true,
    "expires_at": "2025-01-01T00:00:00Z",
    "last_used_at": null,
    "tags": ["ai", "gpt"],
    "created_at": "2024-01-01T00:00:00Z",
    "credential_data": {
      "api_key": "sk-1234567890abcdef"
    }
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Workspace access denied
- `404 Not Found` - Credential not found
- `500 Internal Server Error` - Server error

---

### 4. Get Workspace Credentials

Get all workspace credentials.

**Endpoint:** `GET {{base_url}}/frontend/workspaces/{{workspace_id}}/credentials`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `workspace_id` (string, required) - Workspace ID

**Query Parameters:**
- `credential_type` (string, optional) - Filter by credential type (API_KEY, SLACK, etc.)

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
    "credentials": [
      {
        "id": "CRD-1234567890ABCDEF",
        "name": "OpenAI API Key",
        "credential_type": "API_KEY",
        "credential_provider": "OPENAI",
        "description": "OpenAI API key for GPT models",
        "is_active": true,
        "expires_at": "2025-01-01T00:00:00Z",
        "last_used_at": null,
        "tags": ["ai", "gpt"]
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

### 5. Update Credential

Update credential metadata.

**Endpoint:** `PUT {{base_url}}/frontend/workspaces/{{workspace_id}}/credentials/{{credential_id}}`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `workspace_id` (string, required) - Workspace ID
- `credential_id` (string, required) - Credential ID

**Request Body:**
```json
{
  "name": "Updated OpenAI API Key",
  "description": "Updated description",
  "tags": ["ai", "gpt", "updated"]
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "Credential updated successfully.",
  "traceId": "{{trace_id}}",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "id": "CRD-1234567890ABCDEF",
    "workspace_id": "WSP-1234567890ABCDEF",
    "owner_id": "USR-1234567890ABCDEF",
    "name": "Updated OpenAI API Key",
    "credential_type": "API_KEY",
    "credential_provider": "OPENAI",
    "description": "Updated description",
    "is_active": true,
    "expires_at": "2025-01-01T00:00:00Z",
    "last_used_at": null,
    "tags": ["ai", "gpt", "updated"],
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Workspace access denied
- `404 Not Found` - Credential not found
- `422 Validation Error` - Validation failed
- `500 Internal Server Error` - Server error

---

### 6. Activate Credential

Activate credential.

**Endpoint:** `POST {{base_url}}/frontend/workspaces/{{workspace_id}}/credentials/{{credential_id}}/activate`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `workspace_id` (string, required) - Workspace ID
- `credential_id` (string, required) - Credential ID

**Request Body:**
None

**Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "Credential activated successfully.",
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
- `404 Not Found` - Credential not found
- `500 Internal Server Error` - Server error

---

### 7. Deactivate Credential

Deactivate credential.

**Endpoint:** `POST {{base_url}}/frontend/workspaces/{{workspace_id}}/credentials/{{credential_id}}/deactivate`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `workspace_id` (string, required) - Workspace ID
- `credential_id` (string, required) - Credential ID

**Request Body:**
None

**Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "Credential deactivated successfully.",
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
- `404 Not Found` - Credential not found
- `500 Internal Server Error` - Server error

---

### 8. Delete Credential

Delete credential.

**Endpoint:** `DELETE {{base_url}}/frontend/workspaces/{{workspace_id}}/credentials/{{credential_id}}`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `workspace_id` (string, required) - Workspace ID
- `credential_id` (string, required) - Credential ID

**Request Body:**
None

**Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "Credential deleted successfully.",
  "traceId": "{{trace_id}}",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "success": true,
    "deleted_id": "CRD-1234567890ABCDEF"
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Workspace access denied
- `404 Not Found` - Credential not found
- `500 Internal Server Error` - Server error

