# Workflow Management Routes API Documentation

## Base URL
All endpoints are prefixed with: `{{base_url}}/frontend/workspaces`

---

## 1. Create Workflow

**Endpoint:** `POST /{{workspace_id}}/workflows`

**Description:** Create a new workflow. Workflow is created with DRAFT status. A default API trigger is automatically created.

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "string (required, unique within workspace)",
  "description": "string (optional)",
  "priority": "number (optional, default: 1, must be >= 1)",
  "tags": ["string"] (optional)
}
```

**Expected Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "Workflow created successfully. Default API trigger has been created.",
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
- `409 Conflict`: Workflow name already exists

---

## 2. Get Workflow

**Endpoint:** `GET /{{workspace_id}}/workflows/{{workflow_id}}`

**Description:** Get workflow details.

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
    "name": "string",
    "description": "string (optional)",
    "priority": "number",
    "status": "string (optional)",
    "status_message": "string (optional)",
    "tags": ["string"] (optional),
    "node_count": "number",
    "edge_count": "number",
    "created_at": "string (optional)",
    "updated_at": "string (optional)",
    "created_by": "string (optional)"
  },
  "traceId": "string"
}
```

**Error Responses:**
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Workspace access denied
- `404 Not Found`: Workflow or workspace not found

---

## 3. Get Workspace Workflows

**Endpoint:** `GET /{{workspace_id}}/workflows`

**Description:** Get all workspace workflows.

**Headers:**
```
Authorization: Bearer {{access_token}}
```

**Query Parameters:**
- `status` (optional): Filter by status (DRAFT, ACTIVE, DEACTIVATED, ARCHIVED)

**Request Body:** None

**Expected Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": null,
  "data": {
    "workspace_id": "string",
    "workflows": [
      {
        "id": "string",
        "name": "string",
        "description": "string (optional)",
        "priority": "number",
        "status": "string (optional)",
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

## 4. Get Workflow Graph

**Endpoint:** `GET /{{workspace_id}}/workflows/{{workflow_id}}/graph`

**Description:** Get workflow graph (nodes and edges).

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
    "workflow_id": "string",
    "workflow_name": "string (optional)",
    "status": "string (optional)",
    "nodes": [
      {
        "id": "string",
        "name": "string (optional)",
        "description": "string (optional)",
        "script_id": "string (optional)",
        "custom_script_id": "string (optional)",
        "script_type": "string (optional)",
        "max_retries": "number (optional)",
        "timeout_seconds": "number (optional)",
        "meta_data": {} (optional)
      }
    ],
    "edges": [
      {
        "id": "string",
        "from_node_id": "string",
        "to_node_id": "string"
      }
    ]
  },
  "traceId": "string"
}
```

**Error Responses:**
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Workspace access denied
- `404 Not Found`: Workflow or workspace not found

---

## 5. Update Workflow

**Endpoint:** `PUT /{{workspace_id}}/workflows/{{workflow_id}}`

**Description:** Update workflow information.

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "string (optional)",
  "description": "string (optional)",
  "priority": "number (optional, must be >= 1)",
  "tags": ["string"] (optional)
}
```

**Expected Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "Workflow updated successfully.",
  "data": {
    "id": "string",
    "workspace_id": "string",
    "name": "string",
    "description": "string (optional)",
    "priority": "number",
    "status": "string (optional)",
    "status_message": "string (optional)",
    "tags": ["string"] (optional),
    "node_count": "number",
    "edge_count": "number",
    "created_at": "string (optional)",
    "updated_at": "string (optional)",
    "created_by": "string (optional)"
  },
  "traceId": "string"
}
```

**Error Responses:**
- `400 Bad Request`: Invalid input data
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Workspace access denied
- `404 Not Found`: Workflow or workspace not found
- `409 Conflict`: Workflow name already exists

---

## 6. Activate Workflow

**Endpoint:** `POST /{{workspace_id}}/workflows/{{workflow_id}}/activate`

**Description:** Activate workflow. Workflow must have at least one node to be activated. Associated triggers are also enabled.

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
  "message": "Workflow activated successfully.",
  "data": {
    "success": "boolean",
    "status": "string"
  },
  "traceId": "string"
}
```

**Error Responses:**
- `400 Bad Request`: Workflow has no nodes
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Workspace access denied
- `404 Not Found`: Workflow or workspace not found

---

## 7. Deactivate Workflow

**Endpoint:** `POST /{{workspace_id}}/workflows/{{workflow_id}}/deactivate`

**Description:** Deactivate workflow. Associated triggers are also disabled.

**Headers:**
```
Authorization: Bearer {{access_token}}
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
  "message": "Workflow deactivated successfully.",
  "data": {
    "success": "boolean",
    "status": "string"
  },
  "traceId": "string"
}
```

**Error Responses:**
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Workspace access denied
- `404 Not Found`: Workflow or workspace not found

---

## 8. Archive Workflow

**Endpoint:** `POST /{{workspace_id}}/workflows/{{workflow_id}}/archive`

**Description:** Archive workflow. Archived workflows cannot be modified or activated.

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
  "message": "Workflow archived successfully.",
  "data": {
    "success": "boolean",
    "status": "string"
  },
  "traceId": "string"
}
```

**Error Responses:**
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Workspace access denied
- `404 Not Found`: Workflow or workspace not found

---

## 9. Set Workflow to Draft

**Endpoint:** `POST /{{workspace_id}}/workflows/{{workflow_id}}/set-draft`

**Description:** Set workflow to draft status. Archived workflows cannot be set to draft.

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
  "message": "Workflow set to draft status.",
  "data": {
    "success": "boolean",
    "status": "string"
  },
  "traceId": "string"
}
```

**Error Responses:**
- `400 Bad Request`: Workflow is archived
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Workspace access denied
- `404 Not Found`: Workflow or workspace not found

---

## 10. Delete Workflow

**Endpoint:** `DELETE /{{workspace_id}}/workflows/{{workflow_id}}`

**Description:** Delete workflow. All nodes, edges, and triggers will be deleted (cascade).

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
  "message": "Workflow deleted successfully.",
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
- `404 Not Found`: Workflow or workspace not found

