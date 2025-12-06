# User Role Routes API Documentation

## Base URL
```
{{base_url}}/frontend/user-roles
```

## Endpoints

### 1. Get All User Roles

Get all user roles.

**Endpoint:** `GET {{base_url}}/frontend/user-roles`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

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
    "items": [
      {
        "id": "ROL-1234567890ABCDEF",
        "name": "Owner",
        "description": "Workspace owner with full access",
        "can_edit_workspace": true,
        "can_delete_workspace": true,
        "can_invite_members": true,
        "can_remove_members": true,
        "can_manage_api_keys": true,
        "can_manage_credentials": true,
        "can_manage_files": true,
        "can_manage_variables": true,
        "can_manage_databases": true,
        "can_manage_custom_scripts": true,
        "can_manage_workflows": true,
        "can_execute_workflows": true,
        "can_view_executions": true,
        "can_manage_executions": true,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
      }
    ]
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `500 Internal Server Error` - Server error

---

### 2. Get User Role by ID

Get user role by ID.

**Endpoint:** `GET {{base_url}}/frontend/user-roles/{{role_id}}`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `role_id` (string, required) - Role ID

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
    "id": "ROL-1234567890ABCDEF",
    "name": "Owner",
    "description": "Workspace owner with full access",
    "can_edit_workspace": true,
    "can_delete_workspace": true,
    "can_invite_members": true,
    "can_remove_members": true,
    "can_manage_api_keys": true,
    "can_manage_credentials": true,
    "can_manage_files": true,
    "can_manage_variables": true,
    "can_manage_databases": true,
    "can_manage_custom_scripts": true,
    "can_manage_workflows": true,
    "can_execute_workflows": true,
    "can_view_executions": true,
    "can_manage_executions": true,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `404 Not Found` - Role not found
- `500 Internal Server Error` - Server error

---

### 3. Get User Role by Name

Get user role by name.

**Endpoint:** `GET {{base_url}}/frontend/user-roles/name/{{role_name}}`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `role_name` (string, required) - Role name

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
    "id": "ROL-1234567890ABCDEF",
    "name": "Owner",
    "description": "Workspace owner with full access",
    "can_edit_workspace": true,
    "can_delete_workspace": true,
    "can_invite_members": true,
    "can_remove_members": true,
    "can_manage_api_keys": true,
    "can_manage_credentials": true,
    "can_manage_files": true,
    "can_manage_variables": true,
    "can_manage_databases": true,
    "can_manage_custom_scripts": true,
    "can_manage_workflows": true,
    "can_execute_workflows": true,
    "can_view_executions": true,
    "can_manage_executions": true,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `404 Not Found` - Role not found
- `500 Internal Server Error` - Server error

---

### 4. Get Role Permissions

Get all permissions for a role.

**Endpoint:** `GET {{base_url}}/frontend/user-roles/{{role_id}}/permissions`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `role_id` (string, required) - Role ID

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
    "role_id": "ROL-1234567890ABCDEF",
    "permissions": {
      "can_edit_workspace": true,
      "can_delete_workspace": true,
      "can_invite_members": true,
      "can_remove_members": true,
      "can_manage_api_keys": true,
      "can_manage_credentials": true,
      "can_manage_files": true,
      "can_manage_variables": true,
      "can_manage_databases": true,
      "can_manage_custom_scripts": true,
      "can_manage_workflows": true,
      "can_execute_workflows": true,
      "can_view_executions": true,
      "can_manage_executions": true
    }
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `404 Not Found` - Role not found
- `500 Internal Server Error` - Server error

---

### 5. Check Permission

Check if a role has a specific permission.

**Endpoint:** `GET {{base_url}}/frontend/user-roles/{{role_id}}/check-permission`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `role_id` (string, required) - Role ID

**Query Parameters:**
- `permission` (string, required) - Permission name (e.g., 'can_edit_workspace')

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
    "role_id": "ROL-1234567890ABCDEF",
    "permission": "can_edit_workspace",
    "has_permission": true
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `404 Not Found` - Role not found
- `422 Validation Error` - Invalid permission name
- `500 Internal Server Error` - Server error

