# Execution Management Routes API Documentation

## Base URL
All endpoints are prefixed with: `{{base_url}}/frontend/workspaces`

---

## 1. Start Execution by Workflow (Test)

**Endpoint:** `POST /{{workspace_id}}/workflows/{{workflow_id}}/executions/test`

**Description:** Start execution by workflow (UI test). This is for testing purposes. No trigger validation is performed. Execution inputs are automatically created for all workflow nodes.

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Request Body:**
```json
{
  "input_data": {} (optional, JSON)
}
```

**Expected Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "Execution started successfully for testing.",
  "data": {
    "id": "string",
    "started_at": "string (optional)",
    "execution_inputs_count": "number"
  },
  "traceId": "string"
}
```

**Error Responses:**
- `400 Bad Request`: Invalid input data
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Workspace access denied
- `404 Not Found`: Workflow or workspace not found

---

## 2. Get Execution

**Endpoint:** `GET /{{workspace_id}}/executions/{{execution_id}}`

**Description:** Get execution details.

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
    "trigger_id": "string (optional)",
    "status": "string (optional, PENDING, RUNNING, COMPLETED, FAILED, CANCELLED, TIMEOUT)",
    "started_at": "string (optional)",
    "ended_at": "string (optional)",
    "duration": "number (optional)",
    "trigger_data": {},
    "results": {},
    "retry_count": "number",
    "max_retries": "number",
    "is_retry": "boolean",
    "triggered_by": "string (optional)",
    "created_at": "string (optional)"
  },
  "traceId": "string"
}
```

**Error Responses:**
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Workspace access denied
- `404 Not Found`: Execution or workspace not found

---

## 3. Get Workspace Executions

**Endpoint:** `GET /{{workspace_id}}/executions`

**Description:** Get all workspace executions.

**Headers:**
```
Authorization: Bearer {{access_token}}
```

**Query Parameters:**
- `status` (optional): Filter by status (PENDING, RUNNING, COMPLETED, FAILED, CANCELLED, TIMEOUT)

**Request Body:** None

**Expected Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": null,
  "data": {
    "workspace_id": "string",
    "executions": [
      {
        "id": "string",
        "workflow_id": "string (optional)",
        "trigger_id": "string (optional)",
        "status": "string (optional)",
        "started_at": "string (optional)",
        "ended_at": "string (optional)",
        "duration": "number (optional)"
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

## 4. Get Workflow Executions

**Endpoint:** `GET /{{workspace_id}}/workflows/{{workflow_id}}/executions`

**Description:** Get all workflow executions.

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
    "executions": [
      {
        "id": "string",
        "workflow_id": "string (optional)",
        "trigger_id": "string (optional)",
        "status": "string (optional)",
        "started_at": "string (optional)",
        "ended_at": "string (optional)",
        "duration": "number (optional)"
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

## 5. Get Execution Statistics

**Endpoint:** `GET /{{workspace_id}}/executions/stats`

**Description:** Get execution statistics for workspace.

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
    "total": "number",
    "pending": "number",
    "running": "number",
    "completed": "number",
    "failed": "number",
    "cancelled": "number"
  },
  "traceId": "string"
}
```

**Error Responses:**
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Workspace access denied
- `404 Not Found`: Workspace not found

