# Authentication Routes API Documentation

## Base URL
```
{{base_url}}/frontend/auth
```

## Endpoints

### 1. Register User

Register a new user.

**Endpoint:** `POST {{base_url}}/frontend/auth/register`

**Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "SecurePass123!",
  "name": "John",
  "surname": "Doe",
  "marketing_consent": false,
  "terms_accepted_version_id": "AGV-1234567890ABCDEF",
  "privacy_policy_accepted_version_id": "AGV-1234567890ABCDEF"
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "User registered successfully. Please check your email for verification.",
  "traceId": "{{trace_id}}",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "id": "USR-1234567890ABCDEF",
    "username": "johndoe",
    "email": "john@example.com",
    "is_verified": false
  }
}
```

**Error Responses:**
- `400 Bad Request` - Invalid input data
- `422 Validation Error` - Validation failed
- `500 Internal Server Error` - Server error

---

### 2. Verify Email

Verify user email with verification token.

**Endpoint:** `POST {{base_url}}/frontend/auth/verify-email`

**Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "verification_token": "abc123def456..."
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "Email verified successfully.",
  "traceId": "{{trace_id}}",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "id": "USR-1234567890ABCDEF",
    "username": "johndoe",
    "email": "john@example.com",
    "is_verified": true
  }
}
```

**Error Responses:**
- `400 Bad Request` - Invalid or expired token
- `422 Validation Error` - Validation failed
- `500 Internal Server Error` - Server error

---

### 3. Resend Verification Email

Resend verification email.

**Endpoint:** `POST {{base_url}}/frontend/auth/resend-verification`

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
  "message": "If an account exists, a verification email has been sent.",
  "traceId": "{{trace_id}}",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "email": "john@example.com",
    "message": "If an account exists, a verification email has been sent."
  }
}
```

**Error Responses:**
- `422 Validation Error` - Invalid email format
- `500 Internal Server Error` - Server error

---

### 4. Login

User login.

**Endpoint:** `POST {{base_url}}/frontend/auth/login`

**Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "email_or_username": "john@example.com",
  "password": "SecurePass123!",
  "device_type": "web"
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "Login successful.",
  "traceId": "{{trace_id}}",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "id": "USR-1234567890ABCDEF",
    "username": "johndoe",
    "email": "john@example.com",
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

**Error Responses:**
- `400 Bad Request` - Invalid credentials
- `403 Forbidden` - Account locked or email not verified
- `422 Validation Error` - Validation failed
- `500 Internal Server Error` - Server error

---

### 5. Logout

Logout from current session.

**Endpoint:** `POST {{base_url}}/frontend/auth/logout`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Request Body:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "Logout successful.",
  "traceId": "{{trace_id}}",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "success": true,
    "message": "Session revoked successfully"
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Invalid token
- `422 Validation Error` - Validation failed
- `500 Internal Server Error` - Server error

---

### 6. Logout All Sessions

Logout from all sessions.

**Endpoint:** `POST {{base_url}}/frontend/auth/logout-all`

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

### 7. Validate Token

Validate access token.

**Endpoint:** `POST {{base_url}}/frontend/auth/validate-token`

**Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
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
- `422 Validation Error` - Validation failed
- `500 Internal Server Error` - Server error

---

### 8. Refresh Token

Refresh access token using refresh token.

**Endpoint:** `POST {{base_url}}/frontend/auth/refresh-token`

**Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "Token refreshed successfully.",
  "traceId": "{{trace_id}}",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

**Error Responses:**
- `400 Bad Request` - Invalid or expired refresh token
- `422 Validation Error` - Validation failed
- `500 Internal Server Error` - Server error

---

### 9. Lock Account

Lock user account (Admin only).

**Endpoint:** `POST {{base_url}}/frontend/auth/lock-account`

**Headers:**
```
Authorization: Bearer {{admin_access_token}}
Content-Type: application/json
```

**Request Body:**
```json
{
  "user_id": "USR-1234567890ABCDEF",
  "reason": "Suspicious activity detected",
  "lock_duration_minutes": 60
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "Account locked successfully.",
  "traceId": "{{trace_id}}",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "success": true,
    "user_id": "USR-1234567890ABCDEF",
    "locked_until": "2024-01-01T01:00:00Z",
    "reason": "Suspicious activity detected"
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Admin access required
- `404 Not Found` - User not found
- `422 Validation Error` - Validation failed
- `500 Internal Server Error` - Server error

---

### 10. Unlock Account

Unlock user account (Admin only).

**Endpoint:** `POST {{base_url}}/frontend/auth/unlock-account`

**Headers:**
```
Authorization: Bearer {{admin_access_token}}
Content-Type: application/json
```

**Request Body:**
```json
{
  "user_id": "USR-1234567890ABCDEF"
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "Account unlocked successfully.",
  "traceId": "{{trace_id}}",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "success": true,
    "user_id": "USR-1234567890ABCDEF"
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Admin access required
- `404 Not Found` - User not found
- `422 Validation Error` - Validation failed
- `500 Internal Server Error` - Server error

