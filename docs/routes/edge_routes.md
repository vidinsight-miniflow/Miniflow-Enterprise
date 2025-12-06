# Edge Routes API Documentation

## Base URL
All endpoints are prefixed with: `{{base_url}}/frontend/workspaces`

---

## 1. Create Edge

**Endpoint:** `POST /{{workspace_id}}/workflows/{{workflow_id}}/edges`

**Description:** Create a new edge (connection between nodes). Self-loops are not allowed. Both nodes must belong to the same workflow.

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Request Body:**
```json
{
  "from_node_id": "string (required)",
  "to_node_id": "string (required)"
}
```

**Expected Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "Edge created successfully.",
  "data": {
    "id": "string"
  },
  "traceId": "string"
}
```

**Error Responses:**
- `400 Bad Request`: Invalid input data (e.g., self-loop, nodes from different workflows)
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Workspace access denied
- `404 Not Found`: Workflow, nodes, or workspace not found

---

## 2. Get Edge

**Endpoint:** `GET /{{workspace_id}}/workflows/{{workflow_id}}/edges/{{edge_id}}`

**Description:** Get edge details.

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
    "from_node_id": "string",
    "to_node_id": "string",
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
- `404 Not Found`: Edge, workflow, or workspace not found

---

## 3. Get Workflow Edges

**Endpoint:** `GET /{{workspace_id}}/workflows/{{workflow_id}}/edges`

**Description:** Get all workflow edges.

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
    "edges": [
      {
        "id": "string",
        "from_node_id": "string",
        "to_node_id": "string"
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

## 4. Get Outgoing Edges

**Endpoint:** `GET /{{workspace_id}}/workflows/{{workflow_id}}/nodes/{{node_id}}/outgoing-edges`

**Description:** Get outgoing edges from a node.

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
    "edges": [
      {
        "id": "string",
        "to_node_id": "string"
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
- `404 Not Found`: Node, workflow, or workspace not found

---

## 5. Get Incoming Edges

**Endpoint:** `GET /{{workspace_id}}/workflows/{{workflow_id}}/nodes/{{node_id}}/incoming-edges`

**Description:** Get incoming edges to a node.

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
    "edges": [
      {
        "id": "string",
        "from_node_id": "string"
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
- `404 Not Found`: Node, workflow, or workspace not found

---

## 6. Update Edge

**Endpoint:** `PUT /{{workspace_id}}/workflows/{{workflow_id}}/edges/{{edge_id}}`

**Description:** Update edge (change node connections). Self-loops are not allowed.

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Request Body:**
```json
{
  "from_node_id": "string (optional)",
  "to_node_id": "string (optional)"
}
```

**Expected Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "Edge updated successfully.",
  "data": {
    "id": "string",
    "workflow_id": "string",
    "from_node_id": "string",
    "to_node_id": "string",
    "created_at": "string (optional)",
    "updated_at": "string (optional)",
    "created_by": "string (optional)"
  },
  "traceId": "string"
}
```

**Error Responses:**
- `400 Bad Request`: Invalid input data (e.g., self-loop)
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Workspace access denied
- `404 Not Found`: Edge, workflow, nodes, or workspace not found

---

## 7. Delete Edge

**Endpoint:** `DELETE /{{workspace_id}}/workflows/{{workflow_id}}/edges/{{edge_id}}`

**Description:** Delete edge.

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
  "message": "Edge deleted successfully.",
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
- `404 Not Found`: Edge, workflow, or workspace not found

