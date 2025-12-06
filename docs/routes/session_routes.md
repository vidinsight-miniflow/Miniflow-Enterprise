# Session Routes API Documentation

## Base URL
```
{{base_url}}/frontend/sessions
```

## Endpoints

### 1. Get Session by ID

Get session by ID.

**Endpoint:** `GET {{base_url}}/frontend/sessions/{{session_id}}`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `session_id` (string, required) - Session ID

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
    "id": "AUS-1234567890ABCDEF",
    "user_id": "USR-1234567890ABCDEF",
    "access_token_jti": "jti-abc123...",
    "access_token_expires_at": "2024-01-01T01:00:00Z",
    "refresh_token_jti": "jti-def456...",
    "refresh_token_expires_at": "2024-01-08T00:00:00Z",
    "device_type": "web",
    "user_agent": "Mozilla/5.0...",
    "ip_address": "192.168.1.1",
    "is_revoked": false,
    "revoked_at": null,
    "revocation_reason": null,
    "last_activity_at": "2024-01-01T00:30:00Z",
    "refresh_token_last_used_at": null,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `404 Not Found` - Session not found
- `500 Internal Server Error` - Server error

---

### 2. Get Session by Access Token JTI

Get session by access token JTI.

**Endpoint:** `GET {{base_url}}/frontend/sessions/token/{{access_token_jti}}`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `access_token_jti` (string, required) - Access token JTI

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
    "id": "AUS-1234567890ABCDEF",
    "user_id": "USR-1234567890ABCDEF",
    "access_token_jti": "jti-abc123...",
    "access_token_expires_at": "2024-01-01T01:00:00Z",
    "refresh_token_jti": "jti-def456...",
    "refresh_token_expires_at": "2024-01-08T00:00:00Z",
    "device_type": "web",
    "user_agent": "Mozilla/5.0...",
    "ip_address": "192.168.1.1",
    "is_revoked": false,
    "revoked_at": null,
    "revocation_reason": null,
    "last_activity_at": "2024-01-01T00:30:00Z",
    "refresh_token_last_used_at": null,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `404 Not Found` - Session not found
- `500 Internal Server Error` - Server error

---

### 3. Get Session by Refresh Token JTI

Get session by refresh token JTI.

**Endpoint:** `GET {{base_url}}/frontend/sessions/refresh-token/{{refresh_token_jti}}`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `refresh_token_jti` (string, required) - Refresh token JTI

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
    "id": "AUS-1234567890ABCDEF",
    "user_id": "USR-1234567890ABCDEF",
    "access_token_jti": "jti-abc123...",
    "access_token_expires_at": "2024-01-01T01:00:00Z",
    "refresh_token_jti": "jti-def456...",
    "refresh_token_expires_at": "2024-01-08T00:00:00Z",
    "device_type": "web",
    "user_agent": "Mozilla/5.0...",
    "ip_address": "192.168.1.1",
    "is_revoked": false,
    "revoked_at": null,
    "revocation_reason": null,
    "last_activity_at": "2024-01-01T00:30:00Z",
    "refresh_token_last_used_at": null,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `404 Not Found` - Session not found
- `500 Internal Server Error` - Server error

---

### 4. Get User Active Sessions

Get all active sessions for a user.

**Endpoint:** `GET {{base_url}}/frontend/sessions/user/active`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Query Parameters:**
- `user_id` (string, optional) - User ID (defaults to current user)

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
        "id": "AUS-1234567890ABCDEF",
        "user_id": "USR-1234567890ABCDEF",
        "access_token_jti": "jti-abc123...",
        "access_token_expires_at": "2024-01-01T01:00:00Z",
        "refresh_token_jti": "jti-def456...",
        "refresh_token_expires_at": "2024-01-08T00:00:00Z",
        "device_type": "web",
        "user_agent": "Mozilla/5.0...",
        "ip_address": "192.168.1.1",
        "is_revoked": false,
        "revoked_at": null,
        "revocation_reason": null,
        "last_activity_at": "2024-01-01T00:30:00Z",
        "refresh_token_last_used_at": null,
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

### 5. Revoke Session

Revoke a specific session.

**Endpoint:** `POST {{base_url}}/frontend/sessions/revoke`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Request Body:**
```json
{
  "session_id": "AUS-1234567890ABCDEF",
  "reason": "User requested logout"
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "Session revoked successfully.",
  "traceId": "{{trace_id}}",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "success": true,
    "session_id": "AUS-1234567890ABCDEF"
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `404 Not Found` - Session not found
- `422 Validation Error` - Validation failed
- `500 Internal Server Error` - Server error

---

### 6. Revoke All User Sessions

Revoke all active sessions for a user.

**Endpoint:** `POST {{base_url}}/frontend/sessions/revoke-all`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Query Parameters:**
- `user_id` (string, optional) - User ID (defaults to current user)

**Request Body:**
None

**Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "All sessions revoked successfully.",
  "traceId": "{{trace_id}}",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "success": true,
    "sessions_revoked": 3
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `500 Internal Server Error` - Server error

---

### 7. Revoke Oldest Session

Revoke oldest active session for a user.

**Endpoint:** `POST {{base_url}}/frontend/sessions/revoke-oldest`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Query Parameters:**
- `user_id` (string, optional) - User ID (defaults to current user)

**Request Body:**
None

**Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "Oldest session revoked successfully.",
  "traceId": "{{trace_id}}",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "id": "AUS-1234567890ABCDEF",
    "user_id": "USR-1234567890ABCDEF",
    "access_token_jti": "jti-abc123...",
    "access_token_expires_at": "2024-01-01T01:00:00Z",
    "refresh_token_jti": "jti-def456...",
    "refresh_token_expires_at": "2024-01-08T00:00:00Z",
    "device_type": "web",
    "user_agent": "Mozilla/5.0...",
    "ip_address": "192.168.1.1",
    "is_revoked": true,
    "revoked_at": "2024-01-01T00:45:00Z",
    "revocation_reason": null,
    "last_activity_at": "2024-01-01T00:30:00Z",
    "refresh_token_last_used_at": null,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:45:00Z"
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `404 Not Found` - No active sessions found
- `500 Internal Server Error` - Server error

