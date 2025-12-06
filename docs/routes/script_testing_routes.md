# Script Testing Routes API Documentation

## Base URL
All endpoints are prefixed with: `{{base_url}}/frontend/workspaces`

---

## 1. Mark Test as Passed

**Endpoint:** `POST /{{workspace_id}}/scripts/{{script_id}}/test/passed`

**Description:** Mark script test as passed. Usually called by test executor/worker. Requires admin authentication.

**Headers:**
```
Authorization: Bearer {{admin_access_token}}
Content-Type: application/json
```

**Request Body:**
```json
{
  "test_results": {} (optional, JSON),
  "test_coverage": "number (optional, 0-100)"
}
```

**Expected Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "Test marked as passed.",
  "data": {
    "success": "boolean",
    "test_status": "string",
    "test_coverage": "number (optional)"
  },
  "traceId": "string"
}
```

**Error Responses:**
- `400 Bad Request`: Invalid input data (e.g., test_coverage out of range)
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Admin access required or workspace access denied
- `404 Not Found`: Script or workspace not found

---

## 2. Mark Test as Failed

**Endpoint:** `POST /{{workspace_id}}/scripts/{{script_id}}/test/failed`

**Description:** Mark script test as failed. Test results with error details are required. Requires admin authentication.

**Headers:**
```
Authorization: Bearer {{admin_access_token}}
Content-Type: application/json
```

**Request Body:**
```json
{
  "test_results": {} (required, JSON with error details),
  "test_coverage": "number (optional, 0-100)"
}
```

**Expected Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "Test marked as failed.",
  "data": {
    "success": "boolean",
    "test_status": "string"
  },
  "traceId": "string"
}
```

**Error Responses:**
- `400 Bad Request`: Invalid input data or missing test_results
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Admin access required or workspace access denied
- `404 Not Found`: Script or workspace not found

---

## 3. Mark Test as Skipped

**Endpoint:** `POST /{{workspace_id}}/scripts/{{script_id}}/test/skipped`

**Description:** Mark script test as skipped. Requires admin authentication.

**Headers:**
```
Authorization: Bearer {{admin_access_token}}
Content-Type: application/json
```

**Request Body:**
```json
{
  "reason": "string (optional)"
}
```

**Expected Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "Test marked as skipped.",
  "data": {
    "success": "boolean",
    "test_status": "string",
    "reason": "string (optional)"
  },
  "traceId": "string"
}
```

**Error Responses:**
- `400 Bad Request`: Invalid input data
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Admin access required or workspace access denied
- `404 Not Found`: Script or workspace not found

---

## 4. Reset Test Status

**Endpoint:** `POST /{{workspace_id}}/scripts/{{script_id}}/test/reset`

**Description:** Reset test status to UNTESTED. Requires admin authentication.

**Headers:**
```
Authorization: Bearer {{admin_access_token}}
```

**Request Body:** None

**Expected Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "Test status reset to UNTESTED.",
  "data": {
    "success": "boolean",
    "test_status": "string"
  },
  "traceId": "string"
}
```

**Error Responses:**
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Admin access required or workspace access denied
- `404 Not Found`: Script or workspace not found

---

## 5. Get Test Status

**Endpoint:** `GET /{{workspace_id}}/scripts/{{script_id}}/test/status`

**Description:** Get script test status.

**Headers:**
```
Authorization: Bearer {{access_token}}
```

**Request Body:** None

**Expected Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": null,
  "data": {
    "script_id": "string",
    "script_name": "string",
    "test_status": "string (optional)",
    "test_coverage": "number (optional)",
    "test_results": {} (optional),
    "is_dangerous": "boolean"
  },
  "traceId": "string"
}
```

**Error Responses:**
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Workspace access denied
- `404 Not Found`: Script or workspace not found

---

## 6. Get Untested Scripts

**Endpoint:** `GET /{{workspace_id}}/scripts/untested`

**Description:** Get untested scripts.

**Headers:**
```
Authorization: Bearer {{access_token}}
```

**Request Body:** None

**Expected Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": null,
  "data": {
    "workspace_id": "string",
    "scripts": [
      {
        "id": "string",
        "name": "string",
        "category": "string (optional)",
        "approval_status": "string (optional)",
        "is_dangerous": "boolean",
        "created_at": "string (optional)"
      }
    ],
    "count": "number"
  },
  "traceId": "string"
}
```

**Error Responses:**
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Workspace access denied
- `404 Not Found`: Workspace not found

---

## 7. Get Failed Scripts

**Endpoint:** `GET /{{workspace_id}}/scripts/failed`

**Description:** Get failed scripts.

**Headers:**
```
Authorization: Bearer {{access_token}}
```

**Request Body:** None

**Expected Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": null,
  "data": {
    "workspace_id": "string",
    "scripts": [
      {
        "id": "string",
        "name": "string",
        "category": "string (optional)",
        "test_results": {} (optional),
        "is_dangerous": "boolean",
        "created_at": "string (optional)"
      }
    ],
    "count": "number"
  },
  "traceId": "string"
}
```

**Error Responses:**
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Workspace access denied
- `404 Not Found`: Workspace not found

---

## 8. Update Test Results

**Endpoint:** `PUT /{{workspace_id}}/scripts/{{script_id}}/test/results`

**Description:** Update test results (without changing status). Requires admin authentication.

**Headers:**
```
Authorization: Bearer {{admin_access_token}}
Content-Type: application/json
```

**Request Body:**
```json
{
  "test_results": {} (required, JSON)
}
```

**Expected Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "Test results updated successfully.",
  "data": {
    "success": "boolean"
  },
  "traceId": "string"
}
```

**Error Responses:**
- `400 Bad Request`: Invalid input data or missing test_results
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Admin access required or workspace access denied
- `404 Not Found`: Script or workspace not found

---

## 9. Update Test Coverage

**Endpoint:** `PUT /{{workspace_id}}/scripts/{{script_id}}/test/coverage`

**Description:** Update test coverage. Coverage must be between 0 and 100. Requires admin authentication.

**Headers:**
```
Authorization: Bearer {{admin_access_token}}
Content-Type: application/json
```

**Request Body:**
```json
{
  "test_coverage": "number (required, 0-100)"
}
```

**Expected Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "Test coverage updated successfully.",
  "data": {
    "success": "boolean",
    "test_coverage": "number"
  },
  "traceId": "string"
}
```

**Error Responses:**
- `400 Bad Request`: Invalid input data (e.g., test_coverage out of range)
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Admin access required or workspace access denied
- `404 Not Found`: Script or workspace not found

