# API Endpoints Documentation

Bu klasör, MiniFlow Enterprise API'nin tüm endpoint'leri için detaylı dokümantasyon içerir.

## Base URL

Tüm endpoint'ler şu base URL altında çalışır:

```
{{base_url}}/frontend
```

Örnek:
- Development: `http://localhost:8000/frontend`
- Production: `https://api.miniflow.com/frontend`

## Authentication

Çoğu endpoint authentication gerektirir. Authentication için Bearer token kullanılır:

```
Authorization: Bearer {{access_token}}
```

Token'ı almak için `/frontend/auth/login` endpoint'ini kullanın.

### Admin vs Normal User Tokens

**Önemli:** Token formatı aynıdır - her ikisi de JWT Bearer token'dır. Fark, token'ın içindeki kullanıcının yetkilerinde:

- **Normal Token (`{{access_token}}`)**: Herhangi bir kullanıcı login olduğunda alınan token. `authenticate_user` dependency'si ile kontrol edilir.
- **Admin Token (`{{admin_access_token}}`)**: Aynı token formatı, ancak kullanıcının `is_superadmin=True` olması gerekir. `authenticate_admin` dependency'si önce `authenticate_user`'ı çağırır, sonra veritabanından kullanıcıyı çekip `is_superadmin` kontrolü yapar.

**Not:** Dokümantasyonda `{{admin_access_token}}` kullanımı sadece görsel bir ayrım içindir. Gerçekte aynı token formatı kullanılır - sadece admin endpoint'leri için kullanıcının super admin olması gerekir. Normal kullanıcı token'ı ile admin endpoint'lerine erişmeye çalışırsanız `403 Forbidden` hatası alırsınız.

## Response Format

Tüm başarılı response'lar şu formatta döner:

```json
{
  "status": "success",
  "code": 200,
  "message": "Operation successful",
  "traceId": "request-id",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": {
    // Response data
  }
}
```

Hata response'ları:

```json
{
  "status": "error",
  "code": 400,
  "message": "Error message",
  "traceId": "request-id",
  "timestamp": "2024-01-01T00:00:00Z",
  "error_message": "Detailed error message",
  "error_code": "ERROR_CODE"
}
```

## Endpoint Kategorileri

### 1. Authentication & User Management
- [Authentication Routes](auth_routes.md) - Login, Register, Email Verification
- [Session Routes](session_routes.md) - Session Management
- [Login History Routes](login_history_routes.md) - Login History
- [User Management Routes](user_management_routes.md) - User Details, Preferences
- [User Profile Routes](user_profile_routes.md) - Profile Management
- [User Password Routes](user_password_routes.md) - Password Management

### 2. Workspace Management
- [Workspace Management Routes](workspace_management_routes.md) - Workspace CRUD
- [Workspace Member Routes](workspace_member_routes.md) - Member Management
- [Workspace Invitation Routes](workspace_invitation_routes.md) - Invitations
- [Workspace Plan Management Routes](workspace_plan_management_routes.md) - Plan Management

### 3. Resources
- [Variable Routes](variable_routes.md) - Variables
- [Credential Routes](credential_routes.md) - Credentials
- [API Key Routes](api_key_routes.md) - API Keys
- [Database Routes](database_routes.md) - Database Connections
- [File Routes](file_routes.md) - File Management

### 4. Scripts
- [Custom Script Routes](custom_script_routes.md) - Custom Scripts
- [Global Script Routes](global_script_routes.md) - Global Scripts
- [Script Testing Routes](script_testing_routes.md) - Script Testing

### 5. Workflows
- [Workflow Management Routes](workflow_management_routes.md) - Workflow CRUD
- [Node Routes](node_routes.md) - Workflow Nodes
- [Edge Routes](edge_routes.md) - Workflow Edges
- [Trigger Routes](trigger_routes.md) - Workflow Triggers
- [Execution Management Routes](execution_management_routes.md) - Executions

### 6. Information
- [Agreement Routes](agreement_routes.md) - Agreements
- [User Role Routes](user_role_routes.md) - User Roles
- [Workspace Plan Routes](workspace_plan_routes.md) - Workspace Plans

## Common Error Codes

- `HTTP_400` - Bad Request
- `HTTP_401` - Unauthorized
- `HTTP_403` - Forbidden
- `HTTP_404` - Not Found
- `HTTP_422` - Validation Error
- `HTTP_429` - Rate Limit Exceeded
- `HTTP_500` - Internal Server Error

## Rate Limiting

API rate limiting uygulanır. Rate limit aşıldığında `429 Too Many Requests` döner.

Response header'ında:
```
Retry-After: 60
```

## Pagination

Liste endpoint'leri pagination destekler (gelecekte eklenecek).

## Filtering & Sorting

Liste endpoint'leri filtering ve sorting destekler (gelecekte eklenecek).

