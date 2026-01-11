"""API key routes for frontend."""

from fastapi import APIRouter, Request, Depends, Path, Query
from datetime import datetime

from miniflow.server.dependencies import (
    get_api_key_service,
    authenticate_user,
    require_workspace_access,
)
from miniflow.server.dependencies.auth import AuthenticatedUser
from miniflow.server.schemas.base_schemas import create_success_response
from .schemas.api_key_schemas import (
    ValidateApiKeyRequest,
    ValidateApiKeyResponse,
    CreateApiKeyRequest,
    CreateApiKeyResponse,
    ApiKeyResponse,
    WorkspaceApiKeysResponse,
    UpdateApiKeyRequest,
    ActivateApiKeyResponse,
    DeactivateApiKeyResponse,
    DeleteApiKeyResponse,
)

router = APIRouter(prefix="/workspaces", tags=["API Keys"])


# ============================================================================
# VALIDATE API KEY ENDPOINTS
# ============================================================================

@router.post("/api-keys/validate", response_model_exclude_none=True)
async def validate_api_key(
    request: Request,
    validate_data: ValidateApiKeyRequest,
    service = Depends(get_api_key_service),
) -> dict:
    """
    Validate API key.
    
    Public endpoint - no authentication required.
    Used for API key validation.
    """
    ip_address = request.client.host if request.client else None
    
    result = service.validate_api_key(
        full_api_key=validate_data.full_api_key,
        client_ip=validate_data.client_ip or ip_address
    )
    
    response_data = ValidateApiKeyResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump()
    )


# ============================================================================
# CREATE API KEY ENDPOINTS
# ============================================================================

@router.post("/{workspace_id}/api-keys", response_model_exclude_none=True)
async def create_api_key(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    api_key_data: CreateApiKeyRequest = ...,
    service = Depends(get_api_key_service),
    current_user: AuthenticatedUser = Depends(authenticate_user),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Create a new API key.
    
    Requires: Workspace access
    Warning: The full API key is only shown once! Save it securely.
    """
    expires_at = None
    if api_key_data.expires_at:
        expires_at = datetime.fromisoformat(api_key_data.expires_at.replace('Z', '+00:00'))
    
    result = service.create_api_key(
        workspace_id=workspace_id,
        owner_id=current_user["user_id"],
        name=api_key_data.name,
        description=api_key_data.description,
        permissions=api_key_data.permissions,
        expires_at=expires_at,
        tags=api_key_data.tags,
        allowed_ips=api_key_data.allowed_ips,
        key_prefix=api_key_data.key_prefix
    )
    
    response_data = CreateApiKeyResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="API key created successfully. Save it now - it won't be shown again!"
    )


# ============================================================================
# GET API KEY ENDPOINTS
# ============================================================================

@router.get("/{workspace_id}/api-keys/{api_key_id}", response_model_exclude_none=True)
async def get_api_key(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    api_key_id: str = Path(..., description="API key ID"),
    service = Depends(get_api_key_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Get API key details.
    
    Requires: Workspace access
    Note: The actual API key is never returned. Only masked version is shown.
    """
    result = service.get_api_key(
        api_key_id=api_key_id
    )
    
    response_data = ApiKeyResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump()
    )


@router.get("/{workspace_id}/api-keys", response_model_exclude_none=True)
async def get_workspace_api_keys(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    service = Depends(get_api_key_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Get all workspace API keys.
    
    Requires: Workspace access
    """
    result = service.get_workspace_api_keys(
        workspace_id=workspace_id
    )
    
    response_data = WorkspaceApiKeysResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump()
    )


# ============================================================================
# UPDATE API KEY ENDPOINTS
# ============================================================================

@router.put("/{workspace_id}/api-keys/{api_key_id}", response_model_exclude_none=True)
async def update_api_key(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    api_key_id: str = Path(..., description="API key ID"),
    api_key_data: UpdateApiKeyRequest = ...,
    service = Depends(get_api_key_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Update API key metadata.
    
    Requires: Workspace access
    Note: The actual API key cannot be changed. Create a new one instead.
    """
    expires_at = None
    if api_key_data.expires_at:
        expires_at = datetime.fromisoformat(api_key_data.expires_at.replace('Z', '+00:00'))
    
    result = service.update_api_key(
        api_key_id=api_key_id,
        name=api_key_data.name,
        description=api_key_data.description,
        permissions=api_key_data.permissions,
        tags=api_key_data.tags,
        allowed_ips=api_key_data.allowed_ips,
        expires_at=expires_at
    )
    
    response_data = ApiKeyResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="API key updated successfully."
    )


# ============================================================================
# ACTIVATE/DEACTIVATE API KEY ENDPOINTS
# ============================================================================

@router.post("/{workspace_id}/api-keys/{api_key_id}/activate", response_model_exclude_none=True)
async def activate_api_key(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    api_key_id: str = Path(..., description="API key ID"),
    service = Depends(get_api_key_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Activate API key.
    
    Requires: Workspace access
    """
    result = service.activate_api_key(
        api_key_id=api_key_id
    )
    
    response_data = ActivateApiKeyResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="API key activated successfully."
    )


@router.post("/{workspace_id}/api-keys/{api_key_id}/deactivate", response_model_exclude_none=True)
async def deactivate_api_key(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    api_key_id: str = Path(..., description="API key ID"),
    service = Depends(get_api_key_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Deactivate API key.
    
    Requires: Workspace access
    """
    result = service.deactivate_api_key(
        api_key_id=api_key_id
    )
    
    response_data = DeactivateApiKeyResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="API key deactivated successfully."
    )


# ============================================================================
# DELETE API KEY ENDPOINTS
# ============================================================================

@router.delete("/{workspace_id}/api-keys/{api_key_id}", response_model_exclude_none=True)
async def delete_api_key(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    api_key_id: str = Path(..., description="API key ID"),
    service = Depends(get_api_key_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Delete API key.
    
    Requires: Workspace access
    """
    result = service.delete_api_key(
        api_key_id=api_key_id
    )
    
    response_data = DeleteApiKeyResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="API key deleted successfully."
    )

