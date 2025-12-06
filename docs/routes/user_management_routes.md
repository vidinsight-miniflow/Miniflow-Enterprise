# User Management Routes API Documentation

## Base URL
```
{{base_url}}/frontend/users
```

## Endpoints

### 1. Get User Details by ID

Get user details by ID.

**Endpoint:** `GET {{base_url}}/frontend/users/{{user_id}}`

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
    "id": "USR-1234567890ABCDEF",
    "username": "johndoe",
    "email": "john@example.com",
    "name": "John",
    "surname": "Doe",
    "avatar_url": null,
    "country_code": "TR",
    "phone_number": "+905551234567",
    "phone_verified": false,
    "is_verified": true,
    "is_active": true,
    "is_locked": false,
    "locked_until": null,
    "marketing_consent": false,
    "marketing_consent_at": null,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z",
    "last_login_at": "2024-01-01T00:30:00Z",
    "deletion_requested_at": null,
    "deletion_scheduled_for": null
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Can only view own details (unless admin)
- `404 Not Found` - User not found
- `500 Internal Server Error` - Server error

---

### 2. Get User by Email

Get user details by email (Admin only).

**Endpoint:** `GET {{base_url}}/frontend/users/by-email/{{email}}`

**Headers:**
```
Authorization: Bearer {{admin_access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `email` (string, required) - User email address

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
    "id": "USR-1234567890ABCDEF",
    "username": "johndoe",
    "email": "john@example.com",
    "name": "John",
    "surname": "Doe",
    "avatar_url": null,
    "country_code": "TR",
    "phone_number": "+905551234567",
    "phone_verified": false,
    "is_verified": true,
    "is_active": true,
    "is_locked": false,
    "locked_until": null,
    "marketing_consent": false,
    "marketing_consent_at": null,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z",
    "last_login_at": "2024-01-01T00:30:00Z",
    "deletion_requested_at": null,
    "deletion_scheduled_for": null
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Admin access required
- `404 Not Found` - User not found
- `500 Internal Server Error` - Server error

---

### 3. Get User by Username

Get user details by username (Admin only).

**Endpoint:** `GET {{base_url}}/frontend/users/by-username/{{username}}`

**Headers:**
```
Authorization: Bearer {{admin_access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `username` (string, required) - Username

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
    "id": "USR-1234567890ABCDEF",
    "username": "johndoe",
    "email": "john@example.com",
    "name": "John",
    "surname": "Doe",
    "avatar_url": null,
    "country_code": "TR",
    "phone_number": "+905551234567",
    "phone_verified": false,
    "is_verified": true,
    "is_active": true,
    "is_locked": false,
    "locked_until": null,
    "marketing_consent": false,
    "marketing_consent_at": null,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z",
    "last_login_at": "2024-01-01T00:30:00Z",
    "deletion_requested_at": null,
    "deletion_scheduled_for": null
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Admin access required
- `404 Not Found` - User not found
- `500 Internal Server Error` - Server error

---

### 4. Get All User Preferences

Get all user preferences.

**Endpoint:** `GET {{base_url}}/frontend/users/{{user_id}}/preferences`

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
    "user_id": "USR-1234567890ABCDEF",
    "preferences": [
      {
        "id": "UPR-1234567890ABCDEF",
        "key": "theme",
        "value": "dark",
        "category": "ui",
        "description": "UI theme preference"
      }
    ]
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Can only view own preferences
- `500 Internal Server Error` - Server error

---

### 5. Get User Preference

Get a specific user preference.

**Endpoint:** `GET {{base_url}}/frontend/users/{{user_id}}/preferences/{{preference_key}}`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `user_id` (string, required) - User ID
- `preference_key` (string, required) - Preference key

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
    "id": "UPR-1234567890ABCDEF",
    "user_id": "USR-1234567890ABCDEF",
    "key": "theme",
    "value": "dark",
    "category": "ui",
    "description": "UI theme preference"
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Can only view own preferences
- `404 Not Found` - Preference not found
- `500 Internal Server Error` - Server error

---

### 6. Get User Preferences by Category

Get user preferences by category.

**Endpoint:** `GET {{base_url}}/frontend/users/{{user_id}}/preferences/category/{{category}}`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `user_id` (string, required) - User ID
- `category` (string, required) - Preference category

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
    "category": "ui",
    "preferences": [
      {
        "id": "UPR-1234567890ABCDEF",
        "key": "theme",
        "value": "dark",
        "category": "ui",
        "description": "UI theme preference"
      }
    ]
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Can only view own preferences
- `500 Internal Server Error` - Server error

---

### 7. Set User Preference

Set or update user preference.

**Endpoint:** `PUT {{base_url}}/frontend/users/{{user_id}}/preferences`

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
  "key": "theme",
  "value": "dark",
  "category": "ui",
  "description": "UI theme preference"
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "Preference updated successfully.",
  "traceId": "{{trace_id}}",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "id": "UPR-1234567890ABCDEF",
    "user_id": "USR-1234567890ABCDEF",
    "key": "theme",
    "value": "dark",
    "category": "ui",
    "description": "UI theme preference"
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Can only update own preferences
- `422 Validation Error` - Validation failed
- `500 Internal Server Error` - Server error

---

### 8. Delete User Preference

Delete user preference.

**Endpoint:** `DELETE {{base_url}}/frontend/users/{{user_id}}/preferences/{{preference_key}}`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `user_id` (string, required) - User ID
- `preference_key` (string, required) - Preference key

**Request Body:**
None

**Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "Preference deleted successfully.",
  "traceId": "{{trace_id}}",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "success": true,
    "deleted_key": "theme"
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Can only delete own preferences
- `404 Not Found` - Preference not found
- `500 Internal Server Error` - Server error

---

### 9. Request Account Deletion

Request account deletion.

**Endpoint:** `POST {{base_url}}/frontend/users/{{user_id}}/deletion/request`

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
  "reason": "No longer using the service"
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "Account deletion requested. You have 30 days to cancel.",
  "traceId": "{{trace_id}}",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "user_id": "USR-1234567890ABCDEF",
    "deletion_requested_at": "2024-01-01T00:00:00Z",
    "deletion_scheduled_for": "2024-01-31T00:00:00Z",
    "deletion_reason": "No longer using the service",
    "grace_period_days": 30
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Can only request deletion for own account
- `422 Validation Error` - Validation failed
- `500 Internal Server Error` - Server error

---

### 10. Cancel Account Deletion

Cancel account deletion request.

**Endpoint:** `POST {{base_url}}/frontend/users/{{user_id}}/deletion/cancel`

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
    "success": true,
    "message": "Account deletion cancelled successfully"
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Can only cancel deletion for own account
- `404 Not Found` - No pending deletion request
- `500 Internal Server Error` - Server error

---

### 11. Get Deletion Status

Get account deletion status.

**Endpoint:** `GET {{base_url}}/frontend/users/{{user_id}}/deletion/status`

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
    "has_pending_deletion": true,
    "deletion_requested_at": "2024-01-01T00:00:00Z",
    "deletion_scheduled_for": "2024-01-31T00:00:00Z",
    "days_remaining": 30
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Can only view deletion status for own account
- `500 Internal Server Error` - Server error

---

### 12. Update Marketing Consent

Update marketing consent.

**Endpoint:** `PUT {{base_url}}/frontend/users/{{user_id}}/marketing-consent`

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
  "consent": true
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "Marketing consent updated successfully.",
  "traceId": "{{trace_id}}",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "success": true,
    "marketing_consent": true,
    "marketing_consent_at": "2024-01-01T00:00:00Z"
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Can only update own marketing consent
- `422 Validation Error` - Validation failed
- `500 Internal Server Error` - Server error

