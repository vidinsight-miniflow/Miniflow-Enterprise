# Workspace Invitation Routes API Documentation

## Base URL
```
{{base_url}}/frontend/workspaces
```

## Endpoints

### 1. Get User Pending Invitations

Get user's pending invitations.

**Endpoint:** `GET {{base_url}}/frontend/workspaces/user/{{user_id}}/invitations/pending`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `user_id` (string, required) - User ID

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
    "user_id": "USR-1234567890ABCDEF",
    "pending_invitations": [
      {
        "id": "WIN-1234567890ABCDEF",
        "workspace_id": "WSP-1234567890ABCDEF",
        "workspace_name": "My Workspace",
        "workspace_slug": "my-workspace",
        "invited_by": "USR-9876543210FEDCBA",
        "inviter_name": "Jane Doe",
        "inviter_email": "jane@example.com",
        "role_id": "ROL-1234567890ABCDEF",
        "role_name": "Member",
        "message": "Join our workspace!",
        "created_at": "2024-01-01T00:00:00Z"
      }
    ],
    "count": 1
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Can only view own invitations
- `500 Internal Server Error` - Server error

---

### 2. Get Workspace Invitations

Get workspace invitations.

**Endpoint:** `GET {{base_url}}/frontend/workspaces/{{workspace_id}}/invitations`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `workspace_id` (string, required) - Workspace ID

**Query Parameters:**
- `status_filter` (string, optional) - Status filter (PENDING, ACCEPTED, DECLINED, CANCELLED)

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
    "invitations": [
      {
        "id": "WIN-1234567890ABCDEF",
        "invitee_id": "USR-1234567890ABCDEF",
        "invitee_name": "John Doe",
        "invitee_email": "john@example.com",
        "invited_by": "USR-9876543210FEDCBA",
        "inviter_name": "Jane Doe",
        "role_id": "ROL-1234567890ABCDEF",
        "role_name": "Member",
        "status": "PENDING",
        "message": "Join our workspace!",
        "created_at": "2024-01-01T00:00:00Z",
        "accepted_at": null,
        "declined_at": null
      }
    ],
    "count": 1
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Workspace access denied
- `404 Not Found` - Workspace not found
- `500 Internal Server Error` - Server error

---

### 3. Invite User

Invite user to workspace.

**Endpoint:** `POST {{base_url}}/frontend/workspaces/{{workspace_id}}/invitations`

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
  "invitee_id": "USR-1234567890ABCDEF",
  "role_id": "ROL-1234567890ABCDEF",
  "message": "Join our workspace!"
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "Invitation sent successfully.",
  "traceId": "{{trace_id}}",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "id": "WIN-1234567890ABCDEF",
    "workspace_id": "WSP-1234567890ABCDEF",
    "invitee_id": "USR-1234567890ABCDEF",
    "invitee_email": "john@example.com",
    "role_id": "ROL-1234567890ABCDEF",
    "status": "PENDING",
    "message": "Join our workspace!"
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Workspace access denied
- `400 Bad Request` - Member limit exceeded or user already member
- `404 Not Found` - Workspace or user not found
- `422 Validation Error` - Validation failed
- `500 Internal Server Error` - Server error

---

### 4. Accept Invitation

Accept workspace invitation.

**Endpoint:** `POST {{base_url}}/frontend/workspaces/invitations/{{invitation_id}}/accept`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `invitation_id` (string, required) - Invitation ID

**Request Body:**
None

**Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "Invitation accepted successfully.",
  "traceId": "{{trace_id}}",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "invitation_id": "WIN-1234567890ABCDEF",
    "member_id": "WMB-1234567890ABCDEF",
    "workspace_id": "WSP-1234567890ABCDEF",
    "status": "ACCEPTED",
    "accepted_at": "2024-01-01T00:00:00Z"
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Can only accept own invitations
- `400 Bad Request` - Invitation already accepted/declined or member limit exceeded
- `404 Not Found` - Invitation not found
- `500 Internal Server Error` - Server error

---

### 5. Decline Invitation

Decline workspace invitation.

**Endpoint:** `POST {{base_url}}/frontend/workspaces/invitations/{{invitation_id}}/decline`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `invitation_id` (string, required) - Invitation ID

**Request Body:**
None

**Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "Invitation declined.",
  "traceId": "{{trace_id}}",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "id": "WIN-1234567890ABCDEF",
    "status": "DECLINED",
    "declined_at": "2024-01-01T00:00:00Z"
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Can only decline own invitations
- `400 Bad Request` - Invitation already accepted/declined
- `404 Not Found` - Invitation not found
- `500 Internal Server Error` - Server error

---

### 6. Cancel Invitation

Cancel workspace invitation.

**Endpoint:** `POST {{base_url}}/frontend/workspaces/{{workspace_id}}/invitations/{{invitation_id}}/cancel`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `workspace_id` (string, required) - Workspace ID
- `invitation_id` (string, required) - Invitation ID

**Request Body:**
None

**Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "Invitation cancelled successfully.",
  "traceId": "{{trace_id}}",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "id": "WIN-1234567890ABCDEF",
    "status": "CANCELLED"
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Workspace access denied
- `400 Bad Request` - Invitation already accepted/declined
- `404 Not Found` - Invitation not found
- `500 Internal Server Error` - Server error

---

### 7. Resend Invitation

Resend workspace invitation.

**Endpoint:** `POST {{base_url}}/frontend/workspaces/{{workspace_id}}/invitations/{{invitation_id}}/resend`

**Headers:**
```
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

**Path Parameters:**
- `workspace_id` (string, required) - Workspace ID
- `invitation_id` (string, required) - Invitation ID

**Request Body:**
None

**Response (200 OK):**
```json
{
  "status": "success",
  "code": 200,
  "message": "Invitation resent successfully.",
  "traceId": "{{trace_id}}",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    "success": true,
    "invitation_id": "WIN-1234567890ABCDEF",
    "invitee_email": "john@example.com"
  }
}
```

**Error Responses:**
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Workspace access denied
- `400 Bad Request` - Invitation already accepted/declined
- `404 Not Found` - Invitation not found
- `500 Internal Server Error` - Server error

