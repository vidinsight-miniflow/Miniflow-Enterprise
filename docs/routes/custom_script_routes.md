# Custom Script Routes API Documentation

## Base URL
All endpoints are prefixed with: `{{base_url}}/frontend/workspaces`

---

## 1. Create Custom Script

**Endpoint:** `POST /{{workspace_id}}/scripts`

**Description:** Create a new custom script. Script content cannot be changed after creation. Script is created with PENDING approval status.

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "string (required, unique within workspace)",
  "content": "string (required, Python code)",
  "description": "string (optional)",
  "category": "string (optional)",
  "subcategory": "string (optional)",
  "required_packages": ["string"] (optional),
  "input_schema": {} (optional, JSON),
  "output_schema": {} (optional, JSON),
  "tags": ["string"] (optional),
  "documentation_url": "string (optional)"
}
```

**Expected Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "Custom script created successfully. Waiting for approval.",
  "data": {
    "id": "string"
  },
  "traceId": "string"
}
```

**Error Responses:**
- `400 Bad Request`: Invalid input data
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Workspace access denied
- `404 Not Found`: Workspace not found
- `409 Conflict`: Script name already exists

---

## 2. Get Custom Script

**Endpoint:** `GET /{{workspace_id}}/scripts/{{script_id}}`

**Description:** Get custom script details (without content).

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
    "id": "string",
    "workspace_id": "string",
    "uploaded_by": "string",
    "name": "string",
    "description": "string (optional)",
    "file_extension": "string (optional)",
    "file_size": "number (optional)",
    "category": "string (optional)",
    "subcategory": "string (optional)",
    "required_packages": ["string"] (optional),
    "input_schema": {} (optional),
    "output_schema": {} (optional),
    "tags": ["string"] (optional),
    "documentation_url": "string (optional)",
    "approval_status": "string (optional)",
    "reviewed_by": "string (optional)",
    "reviewed_at": "string (optional)",
    "review_notes": "string (optional)",
    "test_status": "string (optional)",
    "test_coverage": "number (optional)",
    "is_dangerous": "boolean",
    "created_at": "string (optional)"
  },
  "traceId": "string"
}
```

**Error Responses:**
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Workspace access denied
- `404 Not Found`: Script or workspace not found

---

## 3. Get Script Content

**Endpoint:** `GET /{{workspace_id}}/scripts/{{script_id}}/content`

**Description:** Get script content and schemas.

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
    "content": "string",
    "input_schema": {},
    "output_schema": {}
  },
  "traceId": "string"
}
```

**Error Responses:**
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Workspace access denied
- `404 Not Found`: Script or workspace not found

---

## 4. Get Workspace Scripts

**Endpoint:** `GET /{{workspace_id}}/scripts`

**Description:** Get all workspace scripts.

**Headers:**
```
Authorization: Bearer {{access_token}}
```

**Query Parameters:**
- `category` (optional): Filter by category
- `approval_status` (optional): Filter by approval status (PENDING, APPROVED, REJECTED)

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
        "description": "string (optional)",
        "category": "string (optional)",
        "subcategory": "string (optional)",
        "file_size": "number (optional)",
        "approval_status": "string (optional)",
        "test_status": "string (optional)",
        "is_dangerous": "boolean",
        "tags": ["string"] (optional),
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

## 5. Update Custom Script

**Endpoint:** `PUT /{{workspace_id}}/scripts/{{script_id}}`

**Description:** Update script metadata. Script content cannot be changed. Create a new script instead.

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Request Body:**
```json
{
  "description": "string (optional)",
  "tags": ["string"] (optional),
  "documentation_url": "string (optional)"
}
```

**Expected Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "Script metadata updated successfully.",
  "data": {
    "id": "string",
    "workspace_id": "string",
    "uploaded_by": "string",
    "name": "string",
    "description": "string (optional)",
    "file_extension": "string (optional)",
    "file_size": "number (optional)",
    "category": "string (optional)",
    "subcategory": "string (optional)",
    "required_packages": ["string"] (optional),
    "input_schema": {} (optional),
    "output_schema": {} (optional),
    "tags": ["string"] (optional),
    "documentation_url": "string (optional)",
    "approval_status": "string (optional)",
    "reviewed_by": "string (optional)",
    "reviewed_at": "string (optional)",
    "review_notes": "string (optional)",
    "test_status": "string (optional)",
    "test_coverage": "number (optional)",
    "is_dangerous": "boolean",
    "created_at": "string (optional)"
  },
  "traceId": "string"
}
```

**Error Responses:**
- `400 Bad Request`: Invalid input data
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Workspace access denied
- `404 Not Found`: Script or workspace not found

---

## 6. Approve Script

**Endpoint:** `POST /{{workspace_id}}/scripts/{{script_id}}/approve`

**Description:** Approve script. Requires admin authentication.

**Headers:**
```
Authorization: Bearer {{admin_access_token}}
Content-Type: application/json
```

**Request Body:**
```json
{
  "review_notes": "string (optional)"
}
```

**Expected Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "Script approved successfully.",
  "data": {
    "success": "boolean",
    "approval_status": "string"
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

## 7. Reject Script

**Endpoint:** `POST /{{workspace_id}}/scripts/{{script_id}}/reject`

**Description:** Reject script. Requires admin authentication. Review notes are required for rejection.

**Headers:**
```
Authorization: Bearer {{admin_access_token}}
Content-Type: application/json
```

**Request Body:**
```json
{
  "review_notes": "string (required)"
}
```

**Expected Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "Script rejected.",
  "data": {
    "success": "boolean",
    "approval_status": "string"
  },
  "traceId": "string"
}
```

**Error Responses:**
- `400 Bad Request`: Invalid input data or missing review_notes
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Admin access required or workspace access denied
- `404 Not Found`: Script or workspace not found

---

## 8. Reset Approval Status

**Endpoint:** `POST /{{workspace_id}}/scripts/{{script_id}}/reset-approval`

**Description:** Reset approval status to PENDING. Requires admin authentication.

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
  "message": "Approval status reset to PENDING.",
  "data": {
    "success": "boolean",
    "approval_status": "string"
  },
  "traceId": "string"
}
```

**Error Responses:**
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Admin access required or workspace access denied
- `404 Not Found`: Script or workspace not found

---

## 9. Mark Script as Dangerous

**Endpoint:** `POST /{{workspace_id}}/scripts/{{script_id}}/mark-dangerous`

**Description:** Mark script as dangerous. Requires admin authentication.

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
  "message": "Script marked as dangerous.",
  "data": {
    "success": "boolean",
    "is_dangerous": "boolean"
  },
  "traceId": "string"
}
```

**Error Responses:**
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Admin access required or workspace access denied
- `404 Not Found`: Script or workspace not found

---

## 10. Unmark Script as Dangerous

**Endpoint:** `POST /{{workspace_id}}/scripts/{{script_id}}/unmark-dangerous`

**Description:** Unmark script as dangerous. Requires admin authentication.

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
  "message": "Script unmarked as dangerous.",
  "data": {
    "success": "boolean",
    "is_dangerous": "boolean"
  },
  "traceId": "string"
}
```

**Error Responses:**
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Admin access required or workspace access denied
- `404 Not Found`: Script or workspace not found

---

## 11. Delete Custom Script

**Endpoint:** `DELETE /{{workspace_id}}/scripts/{{script_id}}`

**Description:** Delete custom script. Both file and database record will be deleted.

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
  "message": "Script deleted successfully.",
  "data": {
    "success": "boolean",
    "deleted_id": "string"
  },
  "traceId": "string"
}
```

**Error Responses:**
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Workspace access denied
- `404 Not Found`: Script or workspace not found

