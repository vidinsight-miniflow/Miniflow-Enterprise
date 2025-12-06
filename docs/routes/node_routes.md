# Node Routes API Documentation

## Base URL
All endpoints are prefixed with: `{{base_url}}/frontend/workspaces`

---

## 1. Create Node

**Endpoint:** `POST /{{workspace_id}}/workflows/{{workflow_id}}/nodes`

**Description:** Create a new node. Either script_id or custom_script_id must be provided (XOR). Input params are validated against script's input_schema.

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "string (required, unique within workflow)",
  "script_id": "string (optional, XOR with custom_script_id)",
  "custom_script_id": "string (optional, XOR with script_id)",
  "description": "string (optional)",
  "input_params": {} (optional, JSON),
  "output_params": {} (optional, JSON),
  "meta_data": {} (optional, JSON),
  "max_retries": "number (optional, default: 3, must be >= 0)",
  "timeout_seconds": "number (optional, default: 300, must be > 0)"
}
```

**Expected Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "Node created successfully.",
  "data": {
    "id": "string"
  },
  "traceId": "string"
}
```

**Error Responses:**
- `400 Bad Request`: Invalid input data (e.g., both script_id and custom_script_id provided, or neither provided)
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Workspace access denied
- `404 Not Found`: Workflow, script, or workspace not found
- `409 Conflict`: Node name already exists

---

## 2. Get Node

**Endpoint:** `GET /{{workspace_id}}/workflows/{{workflow_id}}/nodes/{{node_id}}`

**Description:** Get node details.

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
    "workflow_id": "string",
    "name": "string",
    "description": "string (optional)",
    "script_id": "string (optional)",
    "custom_script_id": "string (optional)",
    "script_type": "string (optional)",
    "input_params": {} (optional),
    "output_params": {} (optional),
    "meta_data": {} (optional),
    "max_retries": "number",
    "timeout_seconds": "number",
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
- `404 Not Found`: Node, workflow, or workspace not found

---

## 3. Get Node Form Schema

**Endpoint:** `GET /{{workspace_id}}/workflows/{{workflow_id}}/nodes/{{node_id}}/form-schema`

**Description:** Get node form schema for frontend. Returns script's input_schema converted to frontend format.

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
    "node_id": "string",
    "node_name": "string (optional)",
    "script_id": "string (optional)",
    "custom_script_id": "string (optional)",
    "script_name": "string (optional)",
    "script_type": "string (optional)",
    "form_schema": {},
    "output_schema": {}
  },
  "traceId": "string"
}
```

**Error Responses:**
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Workspace access denied
- `404 Not Found`: Node, workflow, or workspace not found

---

## 4. Get Workflow Nodes

**Endpoint:** `GET /{{workspace_id}}/workflows/{{workflow_id}}/nodes`

**Description:** Get all workflow nodes.

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
    "nodes": [
      {
        "id": "string",
        "name": "string",
        "description": "string (optional)",
        "script_id": "string (optional)",
        "custom_script_id": "string (optional)",
        "script_type": "string (optional)",
        "max_retries": "number (optional)",
        "timeout_seconds": "number (optional)",
        "meta_data": {} (optional)
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
- `404 Not Found`: Workflow or workspace not found

---

## 5. Update Node

**Endpoint:** `PUT /{{workspace_id}}/workflows/{{workflow_id}}/nodes/{{node_id}}`

**Description:** Update node information. If script is changed, input_params may be reset.

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
  "script_id": "string (optional)",
  "custom_script_id": "string (optional)",
  "meta_data": {} (optional, JSON),
  "max_retries": "number (optional, must be >= 0)",
  "timeout_seconds": "number (optional, must be > 0)"
}
```

**Expected Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "Node updated successfully.",
  "data": {
    "id": "string",
    "workflow_id": "string",
    "name": "string",
    "description": "string (optional)",
    "script_id": "string (optional)",
    "custom_script_id": "string (optional)",
    "script_type": "string (optional)",
    "input_params": {} (optional),
    "output_params": {} (optional),
    "meta_data": {} (optional),
    "max_retries": "number",
    "timeout_seconds": "number",
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
- `404 Not Found`: Node, workflow, or workspace not found
- `409 Conflict`: Node name already exists

---

## 6. Update Node Input Parameters

**Endpoint:** `PUT /{{workspace_id}}/workflows/{{workflow_id}}/nodes/{{node_id}}/input-params`

**Description:** Update node input parameters. Input params are validated against script's input_schema.

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Request Body:**
```json
{
  "input_params": {} (required, JSON)
}
```

**Expected Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "Node input parameters updated successfully.",
  "data": {
    "id": "string",
    "workflow_id": "string",
    "name": "string",
    "description": "string (optional)",
    "script_id": "string (optional)",
    "custom_script_id": "string (optional)",
    "script_type": "string (optional)",
    "input_params": {},
    "output_params": {} (optional),
    "meta_data": {} (optional),
    "max_retries": "number",
    "timeout_seconds": "number",
    "created_at": "string (optional)",
    "updated_at": "string (optional)",
    "created_by": "string (optional)"
  },
  "traceId": "string"
}
```

**Error Responses:**
- `400 Bad Request`: Invalid input data or validation failed
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Workspace access denied
- `404 Not Found`: Node, workflow, or workspace not found

---

## 7. Sync Input Schema Values

**Endpoint:** `PUT /{{workspace_id}}/workflows/{{workflow_id}}/nodes/{{node_id}}/sync-input-values`

**Description:** Sync input schema values from frontend. Syncs all parameter values, using defaults for missing values.

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Request Body:**
```json
{
  "values": {} (required, JSON dictionary {param_name: value})
}
```

**Expected Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "Input schema values synced successfully.",
  "data": {
    "id": "string",
    "workflow_id": "string",
    "name": "string",
    "description": "string (optional)",
    "script_id": "string (optional)",
    "custom_script_id": "string (optional)",
    "script_type": "string (optional)",
    "input_params": {},
    "output_params": {} (optional),
    "meta_data": {} (optional),
    "max_retries": "number",
    "timeout_seconds": "number",
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
- `404 Not Found`: Node, workflow, or workspace not found

---

## 8. Reset Input Parameters to Defaults

**Endpoint:** `POST /{{workspace_id}}/workflows/{{workflow_id}}/nodes/{{node_id}}/reset-input-params`

**Description:** Reset input parameters to script defaults.

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
  "message": "Input parameters reset to defaults successfully.",
  "data": {
    "id": "string",
    "workflow_id": "string",
    "name": "string",
    "description": "string (optional)",
    "script_id": "string (optional)",
    "custom_script_id": "string (optional)",
    "script_type": "string (optional)",
    "input_params": {},
    "output_params": {} (optional),
    "meta_data": {} (optional),
    "max_retries": "number",
    "timeout_seconds": "number",
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
- `404 Not Found`: Node, workflow, or workspace not found

---

## 9. Delete Node

**Endpoint:** `DELETE /{{workspace_id}}/workflows/{{workflow_id}}/nodes/{{node_id}}`

**Description:** Delete node. Connected edges will be deleted (cascade).

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
  "message": "Node deleted successfully.",
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
- `404 Not Found`: Node, workflow, or workspace not found

