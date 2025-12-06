# Trigger Routes API Documentation

## Base URL
All endpoints are prefixed with: `{{base_url}}/frontend/workspaces`

**Note:** The trigger limits endpoint is public and does not require authentication.

---

## 1. Create Trigger

**Endpoint:** `POST /{{workspace_id}}/workflows/{{workflow_id}}/triggers`

**Description:** Create a new trigger. Trigger limit per workflow is enforced. SCHEDULED triggers require 'cron_expression' in config.

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "string (required, unique within workspace)",
  "trigger_type": "string (required, API, SCHEDULED, WEBHOOK, EVENT)",
  "config": {} (required, JSON),
  "description": "string (optional)",
  "input_mapping": {} (optional, JSON),
  "is_enabled": "boolean (optional, default: true)"
}
```

**Expected Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "Trigger created successfully.",
  "data": {
    "id": "string"
  },
  "traceId": "string"
}
```

**Error Responses:**
- `400 Bad Request`: Invalid input data (e.g., invalid trigger_type, missing cron_expression for SCHEDULED)
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Workspace access denied
- `404 Not Found`: Workflow or workspace not found
- `409 Conflict`: Trigger name already exists or trigger limit exceeded

---

## 2. Get Trigger

**Endpoint:** `GET /{{workspace_id}}/workflows/{{workflow_id}}/triggers/{{trigger_id}}`

**Description:** Get trigger details.

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
    "workflow_id": "string",
    "name": "string",
    "description": "string (optional)",
    "trigger_type": "string (optional)",
    "config": {},
    "input_mapping": {},
    "is_enabled": "boolean",
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
- `404 Not Found`: Trigger, workflow, or workspace not found

---

## 3. Get Workspace Triggers

**Endpoint:** `GET /{{workspace_id}}/triggers`

**Description:** Get all workspace triggers.

**Headers:**
```
Authorization: Bearer {{access_token}}
```

**Query Parameters:**
- `trigger_type` (optional): Filter by trigger type (API, SCHEDULED, WEBHOOK, EVENT)
- `is_enabled` (optional): Filter by enabled status (true/false)

**Request Body:** None

**Expected Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": null,
  "data": {
    "workspace_id": "string",
    "triggers": [
      {
        "id": "string",
        "name": "string",
        "description": "string (optional)",
        "workflow_id": "string (optional)",
        "trigger_type": "string (optional)",
        "is_enabled": "boolean"
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

## 4. Get Workflow Triggers

**Endpoint:** `GET /{{workspace_id}}/workflows/{{workflow_id}}/triggers`

**Description:** Get all workflow triggers.

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
    "triggers": [
      {
        "id": "string",
        "name": "string",
        "description": "string (optional)",
        "trigger_type": "string (optional)",
        "config": {},
        "is_enabled": "boolean"
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

## 5. Get Trigger Limits

**Endpoint:** `GET /triggers/limits`

**Description:** Get trigger limits information. Public endpoint - no authentication required.

**Headers:** None (public endpoint)

**Request Body:** None

**Expected Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": null,
  "data": {
    "min_triggers_per_workflow": "number",
    "max_triggers_per_workflow": "number"
  },
  "traceId": "string"
}
```

**Error Responses:** None (always returns limits)

---

## 6. Update Trigger

**Endpoint:** `PUT /{{workspace_id}}/workflows/{{workflow_id}}/triggers/{{trigger_id}}`

**Description:** Update trigger information. Config validation is performed based on trigger type.

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
  "trigger_type": "string (optional, API, SCHEDULED, WEBHOOK, EVENT)",
  "config": {} (optional, JSON),
  "input_mapping": {} (optional, JSON)
}
```

**Expected Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "Trigger updated successfully.",
  "data": {
    "id": "string",
    "workspace_id": "string",
    "workflow_id": "string",
    "name": "string",
    "description": "string (optional)",
    "trigger_type": "string (optional)",
    "config": {},
    "input_mapping": {},
    "is_enabled": "boolean",
    "created_at": "string (optional)",
    "updated_at": "string (optional)",
    "created_by": "string (optional)"
  },
  "traceId": "string"
}
```

**Error Responses:**
- `400 Bad Request`: Invalid input data (e.g., invalid trigger_type, invalid config)
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Workspace access denied
- `404 Not Found`: Trigger, workflow, or workspace not found
- `409 Conflict`: Trigger name already exists

---

## 7. Enable Trigger

**Endpoint:** `POST /{{workspace_id}}/workflows/{{workflow_id}}/triggers/{{trigger_id}}/enable`

**Description:** Enable trigger.

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
  "message": "Trigger enabled successfully.",
  "data": {
    "success": "boolean",
    "is_enabled": "boolean"
  },
  "traceId": "string"
}
```

**Error Responses:**
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Workspace access denied
- `404 Not Found`: Trigger, workflow, or workspace not found

---

## 8. Disable Trigger

**Endpoint:** `POST /{{workspace_id}}/workflows/{{workflow_id}}/triggers/{{trigger_id}}/disable`

**Description:** Disable trigger.

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
  "message": "Trigger disabled successfully.",
  "data": {
    "success": "boolean",
    "is_enabled": "boolean"
  },
  "traceId": "string"
}
```

**Error Responses:**
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Workspace access denied
- `404 Not Found`: Trigger, workflow, or workspace not found

---

## 9. Delete Trigger

**Endpoint:** `DELETE /{{workspace_id}}/workflows/{{workflow_id}}/triggers/{{trigger_id}}`

**Description:** Delete trigger. DEFAULT trigger cannot be deleted. Minimum trigger count per workflow must be maintained.

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
  "message": "Trigger deleted successfully.",
  "data": {
    "success": "boolean",
    "deleted_id": "string"
  },
  "traceId": "string"
}
```

**Error Responses:**
- `400 Bad Request`: Cannot delete DEFAULT trigger or minimum trigger count would be violated
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Workspace access denied
- `404 Not Found`: Trigger, workflow, or workspace not found

