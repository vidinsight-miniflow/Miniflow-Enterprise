# Workspace Plan Management Routes API Documentation

## Base URL
```
{{base_url}}/frontend/workspaces
```

## Endpoints

### 1. Get Available Plans

Get all available plans.

**Endpoint:** `GET {{base_url}}/frontend/workspaces/plans`

**Headers:**
```
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
    "plans": [
      {
        "id": "WPL-1234567890ABCDEF",
        "name": "Freemium",
        "display_name": "Free Plan",
        "description": "Free plan with basic features",
        "is_popular": false,
        "monthly_price_usd": 0.0,
        "yearly_price_usd": 0.0,
        "features": ["Basic workflows", "Limited executions"]
      }
    ],
    "count": 1
  }
}
```

**Error Responses:**
- `500 Internal Server Error` - Server error

---

### 2. Get Plan Details

Get plan details.

**Endpoint:** `GET {{base_url}}/frontend/workspaces/plans/{{plan_id}}`

**Headers:**
```
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
    "display_name": "Free Plan",
    "description": "Free plan with basic features",
    "is_popular": false,
    "limits": {
      "max_members_per_workspace": 1,
      "max_workflows_per_workspace": 5
    },
    "features": {
      "can_use_custom_scripts": true,
      "can_use_api_access": false
    },
    "api_limits": {
      "max_api_keys_per_workspace": 0,
      "api_rate_limit_per_minute": null
    },
    "pricing": {
      "monthly_price_usd": 0.0,
      "yearly_price_usd": 0.0
    },
    "feature_list": ["Basic workflows", "Limited executions"]
  }
}
```

**Error Responses:**
- `404 Not Found` - Plan not found
- `500 Internal Server Error` - Server error

---

### 3. Get Workspace Current Plan

Get workspace current plan and usage.

**Endpoint:** `GET {{base_url}}/frontend/workspaces/{{workspace_id}}/plan`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `workspace_id` (string, required) - Workspace ID

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
    "workspace_id": "WSP-1234567890ABCDEF",
    "plan": {
      "id": "WPL-1234567890ABCDEF",
      "name": "Freemium"
    },
    "usage": {
      "members": {"current": 1, "limit": 1},
      "workflows": {"current": 3, "limit": 5}
    },
    "billing": {
      "period_start": "2024-01-01T00:00:00Z",
      "period_end": "2024-02-01T00:00:00Z"
    }
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Workspace access denied
- `404 Not Found` - Workspace not found
- `500 Internal Server Error` - Server error

---

### 4. Compare Plans

Compare two plans.

**Endpoint:** `POST {{base_url}}/frontend/workspaces/plans/compare`

**Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "plan_id_1": "WPL-1234567890ABCDEF",
  "plan_id_2": "WPL-9876543210FEDCBA"
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
    "plans": {
      "plan_1": {"id": "WPL-1234567890ABCDEF", "name": "Freemium"},
      "plan_2": {"id": "WPL-9876543210FEDCBA", "name": "Pro"}
    },
    "comparison": {
      "limits": {...},
      "pricing": {...}
    },
    "features": {
      "plan_1": {"can_use_api_access": false},
      "plan_2": {"can_use_api_access": true}
    }
  }
}
```

**Error Responses:**
- `404 Not Found` - One or both plans not found
- `422 Validation Error` - Validation failed
- `500 Internal Server Error` - Server error

---

### 5. Check Upgrade Eligibility

Check if workspace can upgrade to target plan.

**Endpoint:** `POST {{base_url}}/frontend/workspaces/{{workspace_id}}/plan/check-upgrade`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `workspace_id` (string, required) - Workspace ID

**Request Body:**
```json
{
  "target_plan_id": "WPL-9876543210FEDCBA"
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
    "eligible": true,
    "is_upgrade": true,
    "current_plan": {"id": "WPL-1234567890ABCDEF", "name": "Freemium"},
    "target_plan": {"id": "WPL-9876543210FEDCBA", "name": "Pro"},
    "price_difference_monthly": 29.0,
    "issues": null
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Workspace owner access required
- `404 Not Found` - Workspace or plan not found
- `422 Validation Error` - Validation failed
- `500 Internal Server Error` - Server error

---

### 6. Check Downgrade Eligibility

Check if workspace can downgrade to target plan.

**Endpoint:** `POST {{base_url}}/frontend/workspaces/{{workspace_id}}/plan/check-downgrade`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `workspace_id` (string, required) - Workspace ID

**Request Body:**
```json
{
  "target_plan_id": "WPL-1234567890ABCDEF"
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
    "eligible": false,
    "blocking_issues": ["Current usage exceeds target plan limits"],
    "current_plan": {"id": "WPL-9876543210FEDCBA", "name": "Pro"},
    "target_plan": {"id": "WPL-1234567890ABCDEF", "name": "Freemium"},
    "monthly_savings": 29.0
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Workspace owner access required
- `404 Not Found` - Workspace or plan not found
- `422 Validation Error` - Validation failed
- `500 Internal Server Error` - Server error

---

### 7. Upgrade Plan

Upgrade workspace plan.

**Endpoint:** `POST {{base_url}}/frontend/workspaces/{{workspace_id}}/plan/upgrade`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `workspace_id` (string, required) - Workspace ID

**Request Body:**
```json
{
  "target_plan_id": "WPL-9876543210FEDCBA",
  "stripe_subscription_id": "sub_1234567890"
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "Plan upgraded successfully.",
  "traceId": "{{trace_id}}",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "success": true,
    "workspace_id": "WSP-1234567890ABCDEF",
    "new_plan_id": "WPL-9876543210FEDCBA",
    "new_plan_name": "Pro",
    "upgraded_at": "2024-01-01T00:00:00Z"
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Workspace owner access required
- `400 Bad Request` - Upgrade not eligible
- `404 Not Found` - Workspace or plan not found
- `422 Validation Error` - Validation failed
- `500 Internal Server Error` - Server error

---

### 8. Downgrade Plan

Downgrade workspace plan.

**Endpoint:** `POST {{base_url}}/frontend/workspaces/{{workspace_id}}/plan/downgrade`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `workspace_id` (string, required) - Workspace ID

**Request Body:**
```json
{
  "target_plan_id": "WPL-1234567890ABCDEF"
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "Plan downgrade scheduled.",
  "traceId": "{{trace_id}}",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "success": true,
    "workspace_id": "WSP-1234567890ABCDEF",
    "new_plan_id": "WPL-1234567890ABCDEF",
    "new_plan_name": "Freemium",
    "downgraded_at": "2024-01-01T00:00:00Z"
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Workspace owner access required
- `400 Bad Request` - Downgrade not eligible
- `404 Not Found` - Workspace or plan not found
- `422 Validation Error` - Validation failed
- `500 Internal Server Error` - Server error

---

### 9. Update Billing Info

Update workspace billing information.

**Endpoint:** `PUT {{base_url}}/frontend/workspaces/{{workspace_id}}/billing`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `workspace_id` (string, required) - Workspace ID

**Request Body:**
```json
{
  "stripe_customer_id": "cus_1234567890",
  "stripe_subscription_id": "sub_1234567890",
  "billing_email": "billing@example.com",
  "billing_currency": "USD"
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "Billing information updated successfully.",
  "traceId": "{{trace_id}}",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "workspace_id": "WSP-1234567890ABCDEF",
    "stripe_customer_id": "cus_1234567890",
    "stripe_subscription_id": "sub_1234567890",
    "billing_email": "billing@example.com",
    "billing_currency": "USD"
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Workspace owner access required
- `404 Not Found` - Workspace not found
- `422 Validation Error` - Validation failed
- `500 Internal Server Error` - Server error

---

### 10. Update Billing Period

Update billing period and reset monthly counters.

**Endpoint:** `POST {{base_url}}/frontend/workspaces/{{workspace_id}}/billing/period`

**Headers:**
```
Authorization: Bearer {{admin_access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `workspace_id` (string, required) - Workspace ID

**Request Body:**
```json
{
  "period_start": "2024-01-01T00:00:00Z",
  "period_end": "2024-02-01T00:00:00Z"
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "Billing period updated successfully.",
  "traceId": "{{trace_id}}",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "success": true,
    "workspace_id": "WSP-1234567890ABCDEF",
    "period_start": "2024-01-01T00:00:00Z",
    "period_end": "2024-02-01T00:00:00Z"
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Admin access required
- `404 Not Found` - Workspace not found
- `422 Validation Error` - Validation failed
- `500 Internal Server Error` - Server error

---

### 11. Check Limit

Check if a limit would be exceeded.

**Endpoint:** `POST {{base_url}}/frontend/workspaces/{{workspace_id}}/limits/check`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `workspace_id` (string, required) - Workspace ID

**Request Body:**
```json
{
  "limit_type": "workflows",
  "increment": 1
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
    "allowed": true,
    "current": 3,
    "limit": 5,
    "after_increment": 4,
    "would_exceed_by": null
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Workspace access denied
- `404 Not Found` - Workspace not found
- `422 Validation Error` - Validation failed
- `500 Internal Server Error` - Server error

