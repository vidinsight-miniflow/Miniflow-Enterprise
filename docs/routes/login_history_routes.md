# Login History Routes API Documentation

## Base URL
```
{{base_url}}/frontend/login-history
```

## Endpoints

### 1. Get User Login History

Get login history for a user.

**Endpoint:** `GET {{base_url}}/frontend/login-history/user`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Query Parameters:**
- `user_id` (string, optional) - User ID (defaults to current user)
- `limit` (integer, optional, default: 10, min: 1, max: 100) - Maximum number of records

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
        "id": "LGH-1234567890ABCDEF",
        "user_id": "USR-1234567890ABCDEF",
        "status": "SUCCESS",
        "login_method": "password",
        "failure_reason": null,
        "ip_address": "192.168.1.1",
        "user_agent": "Mozilla/5.0...",
        "created_at": "2024-01-01T00:00:00Z"
      }
    ]
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `500 Internal Server Error` - Server error

---

### 2. Get Login History by ID

Get login history record by ID.

**Endpoint:** `GET {{base_url}}/frontend/login-history/{{history_id}}`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `history_id` (string, required) - Login history record ID

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
    "id": "LGH-1234567890ABCDEF",
    "user_id": "USR-1234567890ABCDEF",
    "status": "SUCCESS",
    "login_method": "password",
    "failure_reason": null,
    "ip_address": "192.168.1.1",
    "user_agent": "Mozilla/5.0...",
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `404 Not Found` - History record not found
- `500 Internal Server Error` - Server error

---

### 3. Check Rate Limit

Check if user has exceeded rate limit.

**Endpoint:** `GET {{base_url}}/frontend/login-history/user/rate-limit-check`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Query Parameters:**
- `user_id` (string, optional) - User ID (defaults to current user)
- `max_attempts` (integer, optional, default: 5, min: 1) - Maximum attempts
- `window_minutes` (integer, optional, default: 5, min: 1) - Time window in minutes

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
    "rate_limit_exceeded": false
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `500 Internal Server Error` - Server error

