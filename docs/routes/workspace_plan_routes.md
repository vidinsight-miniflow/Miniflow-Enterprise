# Workspace Plan Routes API Documentation

## Base URL
```
{{base_url}}/frontend/workspace-plans
```

## Endpoints

### 1. Get All Workspace Plans

Get all workspace plans.

**Endpoint:** `GET {{base_url}}/frontend/workspace-plans`

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
        "id": "WPL-1234567890ABCDEF",
        "name": "Freemium",
        "description": "Free plan with basic features",
        "display_order": 1,
        "max_members_per_workspace": 1,
        "max_workflows_per_workspace": 5,
        "max_custom_scripts_per_workspace": 10,
        "storage_limit_mb_per_workspace": 100,
        "max_file_size_mb_per_workspace": 5,
        "monthly_execution_limit": 1000,
        "max_concurrent_executions": 1,
        "can_use_custom_scripts": true,
        "can_use_api_access": false,
        "can_use_webhooks": false,
        "can_use_scheduling": false,
        "can_export_data": false,
        "max_api_keys_per_workspace": 0,
        "api_rate_limit_per_minute": null,
        "api_rate_limit_per_hour": null,
        "api_rate_limit_per_day": null,
        "monthly_price_usd": 0.0,
        "yearly_price_usd": 0.0,
        "price_per_extra_member_usd": null,
        "price_per_extra_workflow_usd": null,
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

### 2. Get Workspace Plan by ID

Get workspace plan by ID.

**Endpoint:** `GET {{base_url}}/frontend/workspace-plans/{{plan_id}}`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `plan_id` (string, required) - Plan ID

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
    "id": "WPL-1234567890ABCDEF",
    "name": "Freemium",
    "description": "Free plan with basic features",
    "display_order": 1,
    "max_members_per_workspace": 1,
    "max_workflows_per_workspace": 5,
    "max_custom_scripts_per_workspace": 10,
    "storage_limit_mb_per_workspace": 100,
    "max_file_size_mb_per_workspace": 5,
    "monthly_execution_limit": 1000,
    "max_concurrent_executions": 1,
    "can_use_custom_scripts": true,
    "can_use_api_access": false,
    "can_use_webhooks": false,
    "can_use_scheduling": false,
    "can_export_data": false,
    "max_api_keys_per_workspace": 0,
    "api_rate_limit_per_minute": null,
    "api_rate_limit_per_hour": null,
    "api_rate_limit_per_day": null,
    "monthly_price_usd": 0.0,
    "yearly_price_usd": 0.0,
    "price_per_extra_member_usd": null,
    "price_per_extra_workflow_usd": null,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `404 Not Found` - Plan not found
- `500 Internal Server Error` - Server error

---

### 3. Get Workspace Plan by Name

Get workspace plan by name.

**Endpoint:** `GET {{base_url}}/frontend/workspace-plans/name/{{plan_name}}`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `plan_name` (string, required) - Plan name

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
    "id": "WPL-1234567890ABCDEF",
    "name": "Freemium",
    "description": "Free plan with basic features",
    "display_order": 1,
    "max_members_per_workspace": 1,
    "max_workflows_per_workspace": 5,
    "max_custom_scripts_per_workspace": 10,
    "storage_limit_mb_per_workspace": 100,
    "max_file_size_mb_per_workspace": 5,
    "monthly_execution_limit": 1000,
    "max_concurrent_executions": 1,
    "can_use_custom_scripts": true,
    "can_use_api_access": false,
    "can_use_webhooks": false,
    "can_use_scheduling": false,
    "can_export_data": false,
    "max_api_keys_per_workspace": 0,
    "api_rate_limit_per_minute": null,
    "api_rate_limit_per_hour": null,
    "api_rate_limit_per_day": null,
    "monthly_price_usd": 0.0,
    "yearly_price_usd": 0.0,
    "price_per_extra_member_usd": null,
    "price_per_extra_workflow_usd": null,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `404 Not Found` - Plan not found
- `500 Internal Server Error` - Server error

---

### 4. Get Workspace Limits

Get workspace limits for a plan.

**Endpoint:** `GET {{base_url}}/frontend/workspace-plans/{{plan_id}}/limits`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `plan_id` (string, required) - Plan ID

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
    "plan_id": "WPL-1234567890ABCDEF",
    "max_members_per_workspace": 1,
    "max_workflows_per_workspace": 5,
    "max_custom_scripts_per_workspace": 10,
    "storage_limit_mb_per_workspace": 100,
    "max_file_size_mb_per_workspace": 5
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `404 Not Found` - Plan not found
- `500 Internal Server Error` - Server error

---

### 5. Get Monthly Limits

Get monthly execution limits for a plan.

**Endpoint:** `GET {{base_url}}/frontend/workspace-plans/{{plan_id}}/monthly-limits`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `plan_id` (string, required) - Plan ID

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
    "plan_id": "WPL-1234567890ABCDEF",
    "monthly_execution_limit": 1000,
    "max_concurrent_executions": 1
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `404 Not Found` - Plan not found
- `500 Internal Server Error` - Server error

---

### 6. Get Feature Flags

Get feature flags for a plan.

**Endpoint:** `GET {{base_url}}/frontend/workspace-plans/{{plan_id}}/features`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `plan_id` (string, required) - Plan ID

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
    "plan_id": "WPL-1234567890ABCDEF",
    "can_use_custom_scripts": true,
    "can_use_api_access": false,
    "can_use_webhooks": false,
    "can_use_scheduling": false,
    "can_export_data": false
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `404 Not Found` - Plan not found
- `500 Internal Server Error` - Server error

---

### 7. Get API Limits

Get API rate limits for a plan.

**Endpoint:** `GET {{base_url}}/frontend/workspace-plans/{{plan_id}}/api-limits`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `plan_id` (string, required) - Plan ID

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
    "plan_id": "WPL-1234567890ABCDEF",
    "max_api_keys_per_workspace": 0,
    "api_rate_limit_per_minute": null,
    "api_rate_limit_per_hour": null,
    "api_rate_limit_per_day": null
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `404 Not Found` - Plan not found
- `500 Internal Server Error` - Server error

---

### 8. Get Pricing

Get pricing information for a plan.

**Endpoint:** `GET {{base_url}}/frontend/workspace-plans/{{plan_id}}/pricing`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `plan_id` (string, required) - Plan ID

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
    "plan_id": "WPL-1234567890ABCDEF",
    "monthly_price_usd": 0.0,
    "yearly_price_usd": 0.0,
    "price_per_extra_member_usd": null,
    "price_per_extra_workflow_usd": null
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `404 Not Found` - Plan not found
- `500 Internal Server Error` - Server error

---

### 9. Get All API Rate Limits

Get all API rate limits for all plans.

**Endpoint:** `GET {{base_url}}/frontend/workspace-plans/api-rate-limits/all`

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
    "limits": {
      "WPL-1234567890ABCDEF": {
        "per_minute": 60,
        "per_hour": 1000,
        "per_day": 10000
      }
    }
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `500 Internal Server Error` - Server error

