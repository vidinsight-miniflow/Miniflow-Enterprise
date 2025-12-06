# Workspace Member Routes API Documentation

## Base URL
```
{{base_url}}/frontend/workspaces
```

## Endpoints

### 1. Get Workspace Members

Get all workspace members.

**Endpoint:** `GET {{base_url}}/frontend/workspaces/{{workspace_id}}/members`

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
    "members": [
      {
        "id": "WMB-1234567890ABCDEF",
        "user_id": "USR-1234567890ABCDEF",
        "user_name": "John Doe",
        "user_email": "john@example.com",
        "role_id": "ROL-1234567890ABCDEF",
        "role_name": "Owner",
        "joined_at": "2024-01-01T00:00:00Z",
        "last_accessed_at": "2024-01-01T00:30:00Z"
      }
    ],
    "total_count": 1
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Workspace access denied
- `404 Not Found` - Workspace not found
- `500 Internal Server Error` - Server error

---

### 2. Get Member Details

Get member details.

**Endpoint:** `GET {{base_url}}/frontend/workspaces/{{workspace_id}}/members/{{member_id}}`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `workspace_id` (string, required) - Workspace ID
- `member_id` (string, required) - Member ID

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
    "id": "WMB-1234567890ABCDEF",
    "workspace_id": "WSP-1234567890ABCDEF",
    "user_id": "USR-1234567890ABCDEF",
    "user_name": "John Doe",
    "user_email": "john@example.com",
    "role_id": "ROL-1234567890ABCDEF",
    "role_name": "Owner",
    "invited_by": null,
    "joined_at": "2024-01-01T00:00:00Z",
    "last_accessed_at": "2024-01-01T00:30:00Z",
    "custom_permissions": null
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Workspace access denied
- `404 Not Found` - Member not found
- `500 Internal Server Error` - Server error

---

### 3. Get User Workspaces

Get all workspaces for a user.

**Endpoint:** `GET {{base_url}}/frontend/workspaces/user/{{user_id}}/workspaces`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `user_id` (string, required) - User ID

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
    "owned_workspaces": [
      {
        "workspace_id": "WSP-1234567890ABCDEF",
        "workspace_name": "My Workspace",
        "workspace_slug": "my-workspace",
        "role": "Owner"
      }
    ],
    "memberships": []
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Can only view own workspaces
- `500 Internal Server Error` - Server error

---

### 4. Change Member Role

Change member role.

**Endpoint:** `PUT {{base_url}}/frontend/workspaces/{{workspace_id}}/members/{{member_id}}/role`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `workspace_id` (string, required) - Workspace ID
- `member_id` (string, required) - Member ID

**Request Body:**
```json
{
  "new_role_id": "ROL-9876543210FEDCBA"
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "Member role updated successfully.",
  "traceId": "{{trace_id}}",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "id": "WMB-1234567890ABCDEF",
    "user_id": "USR-1234567890ABCDEF",
    "role_id": "ROL-9876543210FEDCBA",
    "role_name": "Admin"
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Workspace owner access required
- `400 Bad Request` - Cannot change owner role
- `404 Not Found` - Member not found
- `422 Validation Error` - Validation failed
- `500 Internal Server Error` - Server error

---

### 5. Remove Member

Remove member from workspace.

**Endpoint:** `DELETE {{base_url}}/frontend/workspaces/{{workspace_id}}/members/{{user_id}}`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `workspace_id` (string, required) - Workspace ID
- `user_id` (string, required) - User ID to remove

**Request Body:**
None

**Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "Member removed successfully.",
  "traceId": "{{trace_id}}",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "success": true,
    "workspace_id": "WSP-1234567890ABCDEF",
    "removed_user_id": "USR-9876543210FEDCBA"
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Workspace owner access required
- `400 Bad Request` - Cannot remove owner
- `404 Not Found` - Member not found
- `500 Internal Server Error` - Server error

---

### 6. Leave Workspace

Leave workspace.

**Endpoint:** `POST {{base_url}}/frontend/workspaces/{{workspace_id}}/leave`

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
  "message": "You have left the workspace.",
  "traceId": "{{trace_id}}",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "success": true
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `400 Bad Request` - Owner cannot leave workspace
- `404 Not Found` - Workspace or membership not found
- `500 Internal Server Error` - Server error

---

### 7. Set Custom Permissions

Set custom permissions for member.

**Endpoint:** `PUT {{base_url}}/frontend/workspaces/{{workspace_id}}/members/{{member_id}}/permissions`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `workspace_id` (string, required) - Workspace ID
- `member_id` (string, required) - Member ID

**Request Body:**
```json
{
  "custom_permissions": {
    "workflow.create": true,
    "workflow.delete": false,
    "script.approve": true
  }
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "Custom permissions updated successfully.",
  "traceId": "{{trace_id}}",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "id": "WMB-1234567890ABCDEF",
    "custom_permissions": {
      "workflow.create": true,
      "workflow.delete": false,
      "script.approve": true
    }
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Workspace owner access required
- `404 Not Found` - Member not found
- `422 Validation Error` - Validation failed
- `500 Internal Server Error` - Server error

---

### 8. Clear Custom Permissions

Clear custom permissions for member (revert to role-based permissions).

**Endpoint:** `DELETE {{base_url}}/frontend/workspaces/{{workspace_id}}/members/{{member_id}}/permissions`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `workspace_id` (string, required) - Workspace ID
- `member_id` (string, required) - Member ID

**Request Body:**
None

**Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "Custom permissions cleared successfully.",
  "traceId": "{{trace_id}}",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "success": true
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Workspace owner access required
- `404 Not Found` - Member not found
- `500 Internal Server Error` - Server error

