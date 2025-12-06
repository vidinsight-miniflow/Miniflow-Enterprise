# User Password Routes API Documentation

## Base URL
```
{{base_url}}/frontend/users
```

## Endpoints

### 1. Change Password

Change password (requires old password).

**Endpoint:** `PUT {{base_url}}/frontend/users/{{user_id}}/password/change`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `user_id` (string, required) - User ID

**Request Body:**
```json
{
  "old_password": "OldPassword123!",
  "new_password": "NewPassword123!"
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
    "success": true,
    "message": "Password changed successfully"
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Can only change own password
- `400 Bad Request` - Invalid old password
- `422 Validation Error` - Validation failed
- `500 Internal Server Error` - Server error

---

### 2. Send Password Reset Email

Send password reset email.

**Endpoint:** `POST {{base_url}}/frontend/users/password/reset/request`

**Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "email": "john@example.com"
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
    "success": true,
    "message": "If an account exists, a password reset email has been sent."
  }
}
```

**Error Responses:**
- `422 Validation Error` - Invalid email format
- `500 Internal Server Error` - Server error

---

### 3. Validate Password Reset Token

Validate password reset token.

**Endpoint:** `POST {{base_url}}/frontend/users/password/reset/validate`

**Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "token": "abc123def456..."
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
    "valid": true
  }
}
```

**Error Responses:**
- `400 Bad Request` - Invalid or expired token
- `422 Validation Error` - Validation failed
- `500 Internal Server Error` - Server error

---

### 4. Reset Password

Reset password using reset token.

**Endpoint:** `POST {{base_url}}/frontend/users/password/reset`

**Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "token": "abc123def456...",
  "new_password": "NewPassword123!"
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
    "success": true,
    "message": "Password reset successfully. All active sessions have been revoked for security."
  }
}
```

**Error Responses:**
- `400 Bad Request` - Invalid or expired token
- `422 Validation Error` - Validation failed
- `500 Internal Server Error` - Server error

---

### 5. Get Password History

Get password change history.

**Endpoint:** `GET {{base_url}}/frontend/users/{{user_id}}/password/history`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `user_id` (string, required) - User ID

**Query Parameters:**
- `limit` (integer, optional, default: 10, min: 1, max: 50) - Maximum number of records

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
    "user_id": "USR-1234567890ABCDEF",
    "total_records": 5,
    "history": [
      {
        "id": "PWH-1234567890ABCDEF",
        "change_reason": "VOLUNTARY",
        "changed_from_ip": "192.168.1.1",
        "changed_from_device": "Mozilla/5.0...",
        "created_at": "2024-01-01T00:00:00Z"
      }
    ]
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Can only view own password history
- `500 Internal Server Error` - Server error

