# Global Script Routes API Documentation

## Base URL
All endpoints are prefixed with: `{{base_url}}/frontend/admin`

**Note:** Global scripts are available to all workspaces. Read endpoints are public, write endpoints require admin authentication.

---

## 1. Create Global Script

**Endpoint:** `POST /scripts`

**Description:** Create a new global script. Script content cannot be changed after creation. Scripts are available to all workspaces.

**Headers:**
```
Authorization: Bearer {{admin_access_token}}
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "string (required, globally unique)",
  "category": "string (required)",
  "content": "string (required, Python code)",
  "description": "string (optional)",
  "subcategory": "string (optional)",
  "script_metadata": {} (optional, JSON),
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
  "message": "Global script created successfully.",
  "data": {
    "id": "string"
  },
  "traceId": "string"
}
```

**Error Responses:**
- `400 Bad Request`: Invalid input data
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Admin access required
- `409 Conflict`: Script name already exists

---

## 2. Get Global Script

**Endpoint:** `GET /scripts/{{script_id}}`

**Description:** Get global script details (without content). Public endpoint - no authentication required.

**Headers:** None (public endpoint)

**Request Body:** None

**Expected Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": null,
  "data": {
    "id": "string",
    "name": "string",
    "description": "string (optional)",
    "category": "string (optional)",
    "subcategory": "string (optional)",
    "file_extension": "string (optional)",
    "file_size": "number (optional)",
    "script_metadata": {} (optional),
    "required_packages": ["string"] (optional),
    "input_schema": {} (optional),
    "output_schema": {} (optional),
    "tags": ["string"] (optional),
    "documentation_url": "string (optional)",
    "created_at": "string (optional)"
  },
  "traceId": "string"
}
```

**Error Responses:**
- `404 Not Found`: Script not found

---

## 3. Get Script by Name

**Endpoint:** `GET /scripts/name/{{name}}`

**Description:** Get global script by name. Public endpoint - no authentication required.

**Headers:** None (public endpoint)

**Request Body:** None

**Expected Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": null,
  "data": {
    "id": "string",
    "name": "string",
    "description": "string (optional)",
    "category": "string (optional)",
    "subcategory": "string (optional)",
    "file_extension": "string (optional)",
    "file_size": "number (optional)",
    "required_packages": ["string"] (optional),
    "tags": ["string"] (optional)
  },
  "traceId": "string"
}
```

**Error Responses:**
- `404 Not Found`: Script not found

---

## 4. Get Script Content

**Endpoint:** `GET /scripts/{{script_id}}/content`

**Description:** Get script content and schemas. Public endpoint - no authentication required.

**Headers:** None (public endpoint)

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
- `404 Not Found`: Script not found

---

## 5. Get All Scripts

**Endpoint:** `GET /scripts`

**Description:** Get all global scripts. Public endpoint - no authentication required.

**Headers:** None (public endpoint)

**Query Parameters:**
- `category` (optional): Filter by category
- `subcategory` (optional): Filter by subcategory

**Request Body:** None

**Expected Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": null,
  "data": {
    "scripts": [
      {
        "id": "string",
        "name": "string",
        "description": "string (optional)",
        "category": "string (optional)",
        "subcategory": "string (optional)",
        "file_size": "number (optional)",
        "required_packages": ["string"] (optional),
        "tags": ["string"] (optional),
        "created_at": "string (optional)"
      }
    ],
    "count": "number"
  },
  "traceId": "string"
}
```

**Error Responses:** None (returns empty list if no scripts found)

---

## 6. Get Categories

**Endpoint:** `GET /scripts/categories`

**Description:** Get all script categories. Public endpoint - no authentication required.

**Headers:** None (public endpoint)

**Request Body:** None

**Expected Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": null,
  "data": {
    "categories": ["string"]
  },
  "traceId": "string"
}
```

**Error Responses:** None (returns empty list if no categories found)

---

## 7. Update Global Script

**Endpoint:** `PUT /scripts/{{script_id}}`

**Description:** Update script metadata. Script content cannot be changed. Create a new script instead. Requires admin authentication.

**Headers:**
```
Authorization: Bearer {{admin_access_token}}
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
    "name": "string",
    "description": "string (optional)",
    "category": "string (optional)",
    "subcategory": "string (optional)",
    "file_extension": "string (optional)",
    "file_size": "number (optional)",
    "script_metadata": {} (optional),
    "required_packages": ["string"] (optional),
    "input_schema": {} (optional),
    "output_schema": {} (optional),
    "tags": ["string"] (optional),
    "documentation_url": "string (optional)",
    "created_at": "string (optional)"
  },
  "traceId": "string"
}
```

**Error Responses:**
- `400 Bad Request`: Invalid input data
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Admin access required
- `404 Not Found`: Script not found

---

## 8. Delete Global Script

**Endpoint:** `DELETE /scripts/{{script_id}}`

**Description:** Delete global script. Both file and database record will be deleted. Requires admin authentication.

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
- `403 Forbidden`: Admin access required
- `404 Not Found`: Script not found

---

## 9. Seed Scripts

**Endpoint:** `POST /scripts/seed`

**Description:** Seed global scripts (initial data). Existing scripts with same name will be skipped. Requires admin authentication.

**Headers:**
```
Authorization: Bearer {{admin_access_token}}
Content-Type: application/json
```

**Request Body:**
```json
{
  "scripts_data": [
    {
      "name": "string",
      "category": "string",
      "content": "string",
      "description": "string (optional)",
      "subcategory": "string (optional)",
      "script_metadata": {} (optional),
      "required_packages": ["string"] (optional),
      "input_schema": {} (optional),
      "output_schema": {} (optional),
      "tags": ["string"] (optional),
      "documentation_url": "string (optional)"
    }
  ]
}
```

**Expected Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "Script seeding completed. Created: {created}, Skipped: {skipped}.",
  "data": {
    "created": "number",
    "skipped": "number"
  },
  "traceId": "string"
}
```

**Error Responses:**
- `400 Bad Request`: Invalid input data
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Admin access required

