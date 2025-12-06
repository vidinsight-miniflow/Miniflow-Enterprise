# Agreement Routes API Documentation

## Base URL
```
{{base_url}}/frontend/agreements
```

## Endpoints

### 1. Get All Agreements

Get all agreement versions.

**Endpoint:** `GET {{base_url}}/frontend/agreements`

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
        "id": "AGV-1234567890ABCDEF",
        "agreement_type": "terms",
        "version": "1.0",
        "content": "# Terms of Service\n\n...",
        "content_hash": "abc123...",
        "effective_date": "2024-01-01T00:00:00Z",
        "locale": "tr-TR",
        "is_active": true,
        "created_by": "USR-1234567890ABCDEF",
        "notes": "Initial version",
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

### 2. Get Active Agreements

Get all active agreements (one per type).

**Endpoint:** `GET {{base_url}}/frontend/agreements/active`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Query Parameters:**
- `locale` (string, optional, default: "tr-TR") - Locale code

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
        "id": "AGV-1234567890ABCDEF",
        "agreement_type": "terms",
        "version": "1.0",
        "content": "# Terms of Service\n\n...",
        "content_hash": "abc123...",
        "effective_date": "2024-01-01T00:00:00Z",
        "locale": "tr-TR",
        "is_active": true,
        "created_by": "USR-1234567890ABCDEF",
        "notes": null,
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

### 3. Get Agreement by ID

Get agreement by ID.

**Endpoint:** `GET {{base_url}}/frontend/agreements/{{agreement_id}}`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `agreement_id` (string, required) - Agreement ID

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
    "id": "AGV-1234567890ABCDEF",
    "agreement_type": "terms",
    "version": "1.0",
    "content": "# Terms of Service\n\n...",
    "content_hash": "abc123...",
    "effective_date": "2024-01-01T00:00:00Z",
    "locale": "tr-TR",
    "is_active": true,
    "created_by": "USR-1234567890ABCDEF",
    "notes": null,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `404 Not Found` - Agreement not found
- `500 Internal Server Error` - Server error

---

### 4. Get Active Agreement by Type

Get active agreement by type.

**Endpoint:** `GET {{base_url}}/frontend/agreements/type/{{agreement_type}}/active`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `agreement_type` (string, required) - Agreement type (e.g., "terms", "privacy_policy")

**Query Parameters:**
- `locale` (string, optional, default: "tr-TR") - Locale code

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
    "id": "AGV-1234567890ABCDEF",
    "agreement_type": "terms",
    "version": "1.0",
    "content": "# Terms of Service\n\n...",
    "content_hash": "abc123...",
    "effective_date": "2024-01-01T00:00:00Z",
    "locale": "tr-TR",
    "is_active": true,
    "created_by": "USR-1234567890ABCDEF",
    "notes": null,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `404 Not Found` - Active agreement not found for this type
- `500 Internal Server Error` - Server error

---

### 5. Get Agreement by Type and Version

Get agreement by type, version and locale.

**Endpoint:** `GET {{base_url}}/frontend/agreements/type/{{agreement_type}}/version/{{version}}`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `agreement_type` (string, required) - Agreement type
- `version` (string, required) - Version number

**Query Parameters:**
- `locale` (string, optional, default: "tr-TR") - Locale code

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
    "id": "AGV-1234567890ABCDEF",
    "agreement_type": "terms",
    "version": "1.0",
    "content": "# Terms of Service\n\n...",
    "content_hash": "abc123...",
    "effective_date": "2024-01-01T00:00:00Z",
    "locale": "tr-TR",
    "is_active": true,
    "created_by": "USR-1234567890ABCDEF",
    "notes": null,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `404 Not Found` - Agreement not found
- `500 Internal Server Error` - Server error

---

### 6. Get All Versions by Type

Get all versions for a specific agreement type.

**Endpoint:** `GET {{base_url}}/frontend/agreements/type/{{agreement_type}}/versions`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `agreement_type` (string, required) - Agreement type

**Query Parameters:**
- `locale` (string, optional) - Locale code (optional)

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
        "id": "AGV-1234567890ABCDEF",
        "agreement_type": "terms",
        "version": "1.0",
        "content": "# Terms of Service\n\n...",
        "content_hash": "abc123...",
        "effective_date": "2024-01-01T00:00:00Z",
        "locale": "tr-TR",
        "is_active": true,
        "created_by": "USR-1234567890ABCDEF",
        "notes": null,
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

### 7. Create Agreement Version

Create a new agreement version.

**Endpoint:** `POST {{base_url}}/frontend/agreements`

**Headers:**
```
Authorization: Bearer {{admin_access_token}}
Content-Type: application/json
```

**Request Body:**
```json
{
  "agreement_type": "terms",
  "version": "2.0",
  "content": "# Terms of Service v2.0\n\n...",
  "effective_date": "2024-01-01T00:00:00Z",
  "locale": "tr-TR",
  "is_active": false,
  "notes": "Updated terms"
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
    "id": "AGV-1234567890ABCDEF",
    "agreement_type": "terms",
    "version": "2.0",
    "content": "# Terms of Service v2.0\n\n...",
    "content_hash": "def456...",
    "effective_date": "2024-01-01T00:00:00Z",
    "locale": "tr-TR",
    "is_active": false,
    "created_by": "USR-1234567890ABCDEF",
    "notes": "Updated terms",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Admin access required
- `422 Validation Error` - Invalid request data
- `500 Internal Server Error` - Server error

---

### 8. Activate Agreement

Activate an agreement version.

**Endpoint:** `PUT {{base_url}}/frontend/agreements/{{agreement_id}}/activate`

**Headers:**
```
Authorization: Bearer {{admin_access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `agreement_id` (string, required) - Agreement ID

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
    "id": "AGV-1234567890ABCDEF",
    "agreement_type": "terms",
    "version": "2.0",
    "content": "# Terms of Service v2.0\n\n...",
    "content_hash": "def456...",
    "effective_date": "2024-01-01T00:00:00Z",
    "locale": "tr-TR",
    "is_active": true,
    "created_by": "USR-1234567890ABCDEF",
    "notes": null,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Admin access required
- `404 Not Found` - Agreement not found
- `500 Internal Server Error` - Server error

---

### 9. Deactivate Agreement

Deactivate an agreement version.

**Endpoint:** `PUT {{base_url}}/frontend/agreements/{{agreement_id}}/deactivate`

**Headers:**
```
Authorization: Bearer {{admin_access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `agreement_id` (string, required) - Agreement ID

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
    "id": "AGV-1234567890ABCDEF",
    "agreement_type": "terms",
    "version": "2.0",
    "content": "# Terms of Service v2.0\n\n...",
    "content_hash": "def456...",
    "effective_date": "2024-01-01T00:00:00Z",
    "locale": "tr-TR",
    "is_active": false,
    "created_by": "USR-1234567890ABCDEF",
    "notes": null,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Admin access required
- `404 Not Found` - Agreement not found
- `500 Internal Server Error` - Server error

---

### 10. Delete Agreement

Delete (soft-delete) an agreement version.

**Endpoint:** `DELETE {{base_url}}/frontend/agreements/{{agreement_id}}`

**Headers:**
```
Authorization: Bearer {{admin_access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `agreement_id` (string, required) - Agreement ID

**Request Body:**
None

**Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "Agreement deleted successfully",
  "traceId": "{{trace_id}}",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "deleted": true
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Admin access required
- `404 Not Found` - Agreement not found
- `500 Internal Server Error` - Server error

