# User Profile Routes API Documentation

## Base URL
```
{{base_url}}/frontend/users
```

## Endpoints

### 1. Update Profile

Update user profile information.

**Endpoint:** `PUT {{base_url}}/frontend/users/{{user_id}}/profile`

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
  "name": "John",
  "surname": "Doe",
  "avatar_url": "https://example.com/avatar.jpg",
  "country_code": "TR",
  "phone_number": "+905551234567"
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "Profile updated successfully.",
  "traceId": "{{trace_id}}",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "user_id": "USR-1234567890ABCDEF",
    "name": "John",
    "surname": "Doe",
    "avatar_url": "https://example.com/avatar.jpg",
    "country_code": "TR",
    "phone_number": "+905551234567",
    "phone_verified": false
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Can only update own profile
- `422 Validation Error` - Validation failed
- `500 Internal Server Error` - Server error

---

### 2. Change Username

Change username.

**Endpoint:** `PUT {{base_url}}/frontend/users/{{user_id}}/username`

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
  "new_username": "newjohndoe"
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "Username changed successfully.",
  "traceId": "{{trace_id}}",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "success": true,
    "old_username": "johndoe",
    "username": "newjohndoe"
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Can only change own username
- `400 Bad Request` - Username already exists
- `422 Validation Error` - Validation failed
- `500 Internal Server Error` - Server error

---

### 3. Change Email

Change email address.

**Endpoint:** `PUT {{base_url}}/frontend/users/{{user_id}}/email`

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
  "new_email": "newemail@example.com"
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
    "old_email": "john@example.com",
    "email": "newemail@example.com",
    "is_verified": false,
    "sessions_revoked": 3,
    "message": "Email changed. Please verify your new email. All active sessions have been revoked for security."
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Can only change own email
- `400 Bad Request` - Email already exists
- `422 Validation Error` - Validation failed
- `500 Internal Server Error` - Server error

---

### 4. Change Phone

Change phone number.

**Endpoint:** `PUT {{base_url}}/frontend/users/{{user_id}}/phone`

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
  "country_code": "TR",
  "phone_number": "+905551234567"
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "Phone number updated. Please verify with the code sent to your phone.",
  "traceId": "{{trace_id}}",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "success": true,
    "country_code": "TR",
    "phone_number": "+905551234567",
    "phone_verified": false
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Can only change own phone number
- `422 Validation Error` - Validation failed
- `500 Internal Server Error` - Server error

---

### 5. Verify Phone

Verify phone number with SMS code.

**Endpoint:** `POST {{base_url}}/frontend/users/{{user_id}}/phone/verify`

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
  "verification_code": "123456"
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "Phone number verified successfully.",
  "traceId": "{{trace_id}}",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "success": true,
    "phone_verified": true,
    "phone_verified_at": "2024-01-01T00:00:00Z"
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Can only verify own phone number
- `400 Bad Request` - Invalid verification code
- `422 Validation Error` - Validation failed
- `500 Internal Server Error` - Server error

