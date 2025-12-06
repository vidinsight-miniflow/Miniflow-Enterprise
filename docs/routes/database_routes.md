# Database Routes API Documentation

## Base URL
```
{{base_url}}/frontend/workspaces
```

## Endpoints

### 1. Create Database

Create a new database connection.

**Endpoint:** `POST {{base_url}}/frontend/workspaces/{{workspace_id}}/databases`

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
  "name": "Production PostgreSQL",
  "database_type": "POSTGRESQL",
  "host": "db.example.com",
  "port": 5432,
  "database_name": "mydb",
  "username": "dbuser",
  "password": "dbpassword",
  "connection_string": null,
  "ssl_enabled": true,
  "additional_params": {
    "pool_size": 10
  },
  "description": "Production database connection",
  "tags": ["production", "postgresql"]
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "Database connection created successfully.",
  "traceId": "{{trace_id}}",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "id": "DB-1234567890ABCDEF"
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Workspace access denied
- `400 Bad Request` - Invalid database type or name already exists
- `422 Validation Error` - Validation failed
- `500 Internal Server Error` - Server error

---

### 2. Get Database

Get database connection details.

**Endpoint:** `GET {{base_url}}/frontend/workspaces/{{workspace_id}}/databases/{{database_id}}`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `workspace_id` (string, required) - Workspace ID
- `database_id` (string, required) - Database ID

**Query Parameters:**
- `include_password` (boolean, optional, default: false) - Include password (decrypted)

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
    "id": "DB-1234567890ABCDEF",
    "workspace_id": "WSP-1234567890ABCDEF",
    "owner_id": "USR-1234567890ABCDEF",
    "name": "Production PostgreSQL",
    "database_type": "POSTGRESQL",
    "host": "db.example.com",
    "port": 5432,
    "database_name": "mydb",
    "username": "dbuser",
    "password": "****",
    "connection_string": null,
    "ssl_enabled": true,
    "additional_params": {
      "pool_size": 10
    },
    "description": "Production database connection",
    "tags": ["production", "postgresql"],
    "is_active": true,
    "last_tested_at": "2024-01-01T00:00:00Z",
    "last_test_status": "SUCCESS",
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Workspace access denied
- `404 Not Found` - Database not found
- `500 Internal Server Error` - Server error

---

### 3. Get Workspace Databases

Get all workspace database connections.

**Endpoint:** `GET {{base_url}}/frontend/workspaces/{{workspace_id}}/databases`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `workspace_id` (string, required) - Workspace ID

**Query Parameters:**
- `database_type` (string, optional) - Filter by database type

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
    "databases": [
      {
        "id": "DB-1234567890ABCDEF",
        "name": "Production PostgreSQL",
        "database_type": "POSTGRESQL",
        "host": "db.example.com",
        "port": 5432,
        "database_name": "mydb",
        "description": "Production database connection",
        "tags": ["production", "postgresql"],
        "is_active": true,
        "last_tested_at": "2024-01-01T00:00:00Z",
        "last_test_status": "SUCCESS"
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

### 4. Update Database

Update database connection.

**Endpoint:** `PUT {{base_url}}/frontend/workspaces/{{workspace_id}}/databases/{{database_id}}`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `workspace_id` (string, required) - Workspace ID
- `database_id` (string, required) - Database ID

**Request Body:**
```json
{
  "name": "Updated Production PostgreSQL",
  "host": "new-db.example.com",
  "port": 5432,
  "database_name": "newdb",
  "username": "newuser",
  "password": "newpassword",
  "connection_string": null,
  "ssl_enabled": true,
  "additional_params": {
    "pool_size": 20
  },
  "description": "Updated description",
  "tags": ["production", "postgresql", "updated"]
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "Database connection updated successfully.",
  "traceId": "{{trace_id}}",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "id": "DB-1234567890ABCDEF",
    "workspace_id": "WSP-1234567890ABCDEF",
    "owner_id": "USR-1234567890ABCDEF",
    "name": "Updated Production PostgreSQL",
    "database_type": "POSTGRESQL",
    "host": "new-db.example.com",
    "port": 5432,
    "database_name": "newdb",
    "username": "newuser",
    "password": "****",
    "connection_string": null,
    "ssl_enabled": true,
    "additional_params": {
      "pool_size": 20
    },
    "description": "Updated description",
    "tags": ["production", "postgresql", "updated"],
    "is_active": true,
    "last_tested_at": "2024-01-01T00:00:00Z",
    "last_test_status": "SUCCESS",
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Workspace access denied
- `404 Not Found` - Database not found
- `422 Validation Error` - Validation failed
- `500 Internal Server Error` - Server error

---

### 5. Update Test Status

Update database connection test status.

**Endpoint:** `POST {{base_url}}/frontend/workspaces/{{workspace_id}}/databases/{{database_id}}/test-status`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `workspace_id` (string, required) - Workspace ID
- `database_id` (string, required) - Database ID

**Request Body:**
```json
{
  "status": "SUCCESS"
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "Test status updated successfully.",
  "traceId": "{{trace_id}}",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "success": true,
    "status": "SUCCESS"
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Workspace access denied
- `404 Not Found` - Database not found
- `422 Validation Error` - Validation failed
- `500 Internal Server Error` - Server error

---

### 6. Activate Database

Activate database connection.

**Endpoint:** `POST {{base_url}}/frontend/workspaces/{{workspace_id}}/databases/{{database_id}}/activate`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `workspace_id` (string, required) - Workspace ID
- `database_id` (string, required) - Database ID

**Request Body:**
None

**Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "Database connection activated successfully.",
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
- `404 Not Found` - Database not found
- `500 Internal Server Error` - Server error

---

### 7. Deactivate Database

Deactivate database connection.

**Endpoint:** `POST {{base_url}}/frontend/workspaces/{{workspace_id}}/databases/{{database_id}}/deactivate`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `workspace_id` (string, required) - Workspace ID
- `database_id` (string, required) - Database ID

**Request Body:**
None

**Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "Database connection deactivated successfully.",
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
- `404 Not Found` - Database not found
- `500 Internal Server Error` - Server error

---

### 8. Delete Database

Delete database connection.

**Endpoint:** `DELETE {{base_url}}/frontend/workspaces/{{workspace_id}}/databases/{{database_id}}`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `workspace_id` (string, required) - Workspace ID
- `database_id` (string, required) - Database ID

**Request Body:**
None

**Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "Database connection deleted successfully.",
  "traceId": "{{trace_id}}",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "success": true,
    "deleted_id": "DB-1234567890ABCDEF"
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Workspace access denied
- `404 Not Found` - Database not found
- `500 Internal Server Error` - Server error

