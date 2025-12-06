# Workspace Management Routes API Documentation

## Base URL
```
{{base_url}}/frontend/workspaces
```

## Endpoints

### 1. Create Workspace

Create a new workspace.

**Endpoint:** `POST {{base_url}}/frontend/workspaces`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "My Workspace",
  "slug": "my-workspace",
  "description": "Workspace description"
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "Workspace created successfully.",
  "traceId": "{{trace_id}}",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "id": "WSP-1234567890ABCDEF",
    "name": "My Workspace",
    "slug": "my-workspace",
    "description": "Workspace description",
    "owner_id": "USR-1234567890ABCDEF",
    "plan_id": "WPL-1234567890ABCDEF"
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `400 Bad Request` - User already has free workspace (if creating free workspace)
- `422 Validation Error` - Validation failed
- `500 Internal Server Error` - Server error

---

### 2. Get Workspace

Get workspace basic information.

**Endpoint:** `GET {{base_url}}/frontend/workspaces/{{workspace_id}}`

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
    "id": "WSP-1234567890ABCDEF",
    "name": "My Workspace",
    "slug": "my-workspace",
    "owner_id": "USR-1234567890ABCDEF",
    "plan_id": "WPL-1234567890ABCDEF",
    "is_suspended": false
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Workspace access denied
- `404 Not Found` - Workspace not found
- `500 Internal Server Error` - Server error

---

### 3. Get Workspace Details

Get workspace detailed information.

**Endpoint:** `GET {{base_url}}/frontend/workspaces/{{workspace_id}}/details`

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
    "id": "WSP-1234567890ABCDEF",
    "name": "My Workspace",
    "slug": "my-workspace",
    "description": "Workspace description",
    "owner_id": "USR-1234567890ABCDEF",
    "owner_name": "John Doe",
    "owner_email": "john@example.com",
    "plan_id": "WPL-1234567890ABCDEF",
    "is_suspended": false,
    "suspension_reason": null,
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Workspace access denied
- `404 Not Found` - Workspace not found
- `500 Internal Server Error` - Server error

---

### 4. Get Workspace Limits

Get workspace limits and current usage.

**Endpoint:** `GET {{base_url}}/frontend/workspaces/{{workspace_id}}/limits`

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
    "members": {
      "limit": 5,
      "current": 3
    },
    "workflows": {
      "limit": 10,
      "current": 5
    },
    "custom_scripts": {
      "limit": 20,
      "current": 8
    },
    "storage_mb": {
      "limit": 1000,
      "current": 250
    },
    "api_keys": {
      "limit": 5,
      "current": 2
    },
    "monthly_executions": {
      "limit": 10000,
      "current": 3500
    },
    "concurrent_executions": {
      "limit": 5
    },
    "billing_period": {
      "start": "2024-01-01T00:00:00Z",
      "end": "2024-02-01T00:00:00Z"
    },
    "max_file_size_mb": 10
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Workspace access denied
- `404 Not Found` - Workspace not found
- `500 Internal Server Error` - Server error

---

### 5. Get Workspace by Slug

Get workspace by slug.

**Endpoint:** `GET {{base_url}}/frontend/workspaces/slug/{{slug}}`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `slug` (string, required) - Workspace slug

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
    "id": "WSP-1234567890ABCDEF",
    "name": "My Workspace",
    "slug": "my-workspace",
    "owner_id": "USR-1234567890ABCDEF",
    "plan_id": "WPL-1234567890ABCDEF",
    "is_suspended": false
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `404 Not Found` - Workspace not found
- `500 Internal Server Error` - Server error

---

### 6. Update Workspace

Update workspace information.

**Endpoint:** `PUT {{base_url}}/frontend/workspaces/{{workspace_id}}`

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
  "name": "Updated Workspace Name",
  "slug": "updated-workspace-slug",
  "description": "Updated description"
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "Workspace updated successfully.",
  "traceId": "{{trace_id}}",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "id": "WSP-1234567890ABCDEF",
    "name": "Updated Workspace Name",
    "slug": "updated-workspace-slug",
    "description": "Updated description"
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Workspace owner access required
- `404 Not Found` - Workspace not found
- `422 Validation Error` - Validation failed
- `500 Internal Server Error` - Server error

---

### 7. Delete Workspace

Delete workspace (soft-delete).

**Endpoint:** `DELETE {{base_url}}/frontend/workspaces/{{workspace_id}}`

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
  "message": "Workspace deleted successfully.",
  "traceId": "{{trace_id}}",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "success": true,
    "workspace_id": "WSP-1234567890ABCDEF",
    "deleted_members": 5,
    "deleted_invitations": 2
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Workspace owner access required
- `404 Not Found` - Workspace not found
- `500 Internal Server Error` - Server error

---

### 8. Suspend Workspace

Suspend workspace (Admin only).

**Endpoint:** `POST {{base_url}}/frontend/workspaces/{{workspace_id}}/suspend`

**Headers:**
```
Authorization: Bearer {{admin_access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `workspace_id` (string, required) - Workspace ID

**Request Body:**
```json
{
  "reason": "Violation of terms of service"
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "Workspace suspended successfully.",
  "traceId": "{{trace_id}}",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "success": true,
    "suspended_at": "2024-01-01T00:00:00Z"
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Admin access required
- `404 Not Found` - Workspace not found
- `422 Validation Error` - Validation failed
- `500 Internal Server Error` - Server error

---

### 9. Unsuspend Workspace

Unsuspend workspace (Admin only).

**Endpoint:** `POST {{base_url}}/frontend/workspaces/{{workspace_id}}/unsuspend`

**Headers:**
```
Authorization: Bearer {{admin_access_token}}
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
  "message": "Workspace unsuspended successfully.",
  "traceId": "{{trace_id}}",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "success": true
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Admin access required
- `404 Not Found` - Workspace not found
- `500 Internal Server Error` - Server error

---

### 10. Transfer Ownership

Transfer workspace ownership.

**Endpoint:** `POST {{base_url}}/frontend/workspaces/{{workspace_id}}/transfer-ownership`

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
  "new_owner_id": "USR-9876543210FEDCBA"
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "Ownership transferred successfully.",
  "traceId": "{{trace_id}}",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "success": true,
    "workspace_id": "WSP-1234567890ABCDEF",
    "previous_owner_id": "USR-1234567890ABCDEF",
    "new_owner_id": "USR-9876543210FEDCBA"
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Workspace owner access required
- `404 Not Found` - Workspace or new owner not found
- `422 Validation Error` - Validation failed
- `500 Internal Server Error` - Server error

