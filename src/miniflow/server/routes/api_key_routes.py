"""
API Key management routes.

Handles API key creation, retrieval, update, and deletion for workspaces.
"""
from fastapi import APIRouter, Depends, Request, status, Path, Query
from typing import Dict, Any, Optional

from src.miniflow.server.dependencies import get_api_key_service
from src.miniflow.services import ApiKeyService
from src.miniflow.server.helpers import (
    validate_workspace_member,
    authenticate_user,
    AuthUser,
)
from src.miniflow.server.schemas.base_schema import create_success_response
from src.miniflow.server.schemas.routes.resource_schemas.api_key_schemas import (
    CreateApiKeyRequest,
    UpdateApiKeyRequest,
)

router = APIRouter(prefix="/workspaces", tags=["api-keys"])


# ============================================================================
# GET ALL API KEYS
# ============================================================================

@router.get(
    "/{workspace_id}/api-keys",
    summary="Get all API keys",
    description="Get all API keys for a workspace with pagination",
    status_code=status.HTTP_200_OK,
)
async def get_all_api_keys(
    request: Request,
    workspace_id: str = Depends(validate_workspace_member),
    page: int = Query(1, ge=1, description="Page number (starts from 1)"),
    page_size: int = Query(100, ge=1, le=1000, description="Number of items per page (1-1000)"),
    order_by: Optional[str] = Query(None, description="Field to order by (default: created_at)"),
    order_desc: bool = Query(False, description="Order descending (default: False)"),
    include_deleted: bool = Query(False, description="Include deleted API keys"),
    api_key_service: ApiKeyService = Depends(get_api_key_service),
) -> Dict[str, Any]:
    """
    Get all API keys for a workspace with pagination.
    
    - **workspace_id**: Workspace ID (path parameter)
    - **page**: Page number (query parameter, default: 1, min: 1)
    - **page_size**: Number of items per page (query parameter, default: 100, min: 1, max: 1000)
    - **order_by**: Field to order by (query parameter, optional, default: created_at)
    - **order_desc**: Order descending (query parameter, default: False)
    - **include_deleted**: Include deleted API keys (query parameter, default: False)
    
    Requires workspace membership.
    Returns paginated list of API keys (masked).
    """
    result = api_key_service.get_all_api_keys(
        workspace_id=workspace_id,
        page=page,
        page_size=page_size,
        order_by=order_by,
        order_desc=order_desc,
        include_deleted=include_deleted,
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="API keys retrieved successfully",
        code=status.HTTP_200_OK,
    ).model_dump()


# ============================================================================
# GET API KEY
# ============================================================================

@router.get(
    "/{workspace_id}/api-keys/{api_key_id}",
    summary="Get API key",
    description="Get detailed information about a specific API key",
    status_code=status.HTTP_200_OK,
)
async def get_api_key(
    request: Request,
    workspace_id: str = Depends(validate_workspace_member),
    api_key_id: str = Path(..., description="API Key ID"),
    api_key_service: ApiKeyService = Depends(get_api_key_service),
) -> Dict[str, Any]:
    """
    Get detailed information about a specific API key.
    
    - **workspace_id**: Workspace ID (path parameter)
    - **api_key_id**: API Key ID (path parameter)
    
    Requires workspace membership.
    Returns API key information (masked - only prefix shown).
    """
    result = api_key_service.get_api_key(
        api_key_id=api_key_id,
        workspace_id=workspace_id,
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="API key retrieved successfully",
        code=status.HTTP_200_OK,
    ).model_dump()


# ============================================================================
# CREATE API KEY
# ============================================================================

@router.post(
    "/{workspace_id}/api-keys",
    summary="Create API key",
    description="Create a new API key for a workspace",
    status_code=status.HTTP_201_CREATED,
)
async def create_api_key(
    request: Request,
    workspace_id: str = Depends(validate_workspace_member),
    body: CreateApiKeyRequest = ...,
    current_user: AuthUser = Depends(authenticate_user),
    api_key_service: ApiKeyService = Depends(get_api_key_service),
) -> Dict[str, Any]:
    """
    Create a new API key for a workspace.
    
    - **workspace_id**: Workspace ID (path parameter)
    - **name**: API key name (request body, required)
    - **key_prefix**: API key prefix (request body, optional, default: "sk_live_")
    - **description**: Optional description (request body, optional)
    - **permissions**: Optional custom permissions (request body, optional)
    - **expires_at**: Optional expiration date (request body, optional)
    - **tags**: Optional tags (request body, optional)
    - **allowed_ips**: Optional allowed IP addresses (request body, optional)
    
    Requires workspace membership.
    The authenticated user will be recorded as the owner.
    Returns the full API key (only shown once - store securely!).
    """
    result = api_key_service.create_api_key(
        workspace_id=workspace_id,
        owner_id=current_user["user_id"],
        name=body.name,
        key_prefix=body.key_prefix,
        description=body.description,
        permissions=body.permissions,
        expires_at=body.expires_at,
        tags=body.tags,
        allowed_ips=body.allowed_ips,
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="API key created successfully. Store it securely - it won't be shown again!",
        code=status.HTTP_201_CREATED,
    ).model_dump()


# ============================================================================
# UPDATE API KEY
# ============================================================================

@router.put(
    "/{workspace_id}/api-keys/{api_key_id}",
    summary="Update API key",
    description="Update an existing API key",
    status_code=status.HTTP_200_OK,
)
async def update_api_key(
    request: Request,
    workspace_id: str = Depends(validate_workspace_member),
    api_key_id: str = Path(..., description="API Key ID"),
    body: UpdateApiKeyRequest = ...,
    current_user: AuthUser = Depends(authenticate_user),
    api_key_service: ApiKeyService = Depends(get_api_key_service),
) -> Dict[str, Any]:
    """
    Update an existing API key.
    
    - **workspace_id**: Workspace ID (path parameter)
    - **api_key_id**: API Key ID (path parameter)
    - **name**: API key name (request body, optional)
    - **description**: API key description (request body, optional)
    - **permissions**: Custom permissions (request body, optional)
    - **tags**: Tags (request body, optional)
    - **allowed_ips**: Allowed IP addresses (request body, optional)
    - **is_active**: Whether the API key is active (request body, optional)
    - **expires_at**: Expiration date (request body, optional)
    
    Requires workspace membership.
    The authenticated user will be recorded as the updater.
    """
    result = api_key_service.update_api_key(
        api_key_id=api_key_id,
        name=body.name,
        description=body.description,
        permissions=body.permissions,
        tags=body.tags,
        allowed_ips=body.allowed_ips,
        is_active=body.is_active,
        expires_at=body.expires_at,
        updated_by=current_user["user_id"],
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="API key updated successfully",
        code=status.HTTP_200_OK,
    ).model_dump()


# ============================================================================
# DELETE API KEY
# ============================================================================

@router.delete(
    "/{workspace_id}/api-keys/{api_key_id}",
    summary="Delete API key",
    description="Delete an API key",
    status_code=status.HTTP_200_OK,
)
async def delete_api_key(
    request: Request,
    workspace_id: str = Depends(validate_workspace_member),
    api_key_id: str = Path(..., description="API Key ID"),
    api_key_service: ApiKeyService = Depends(get_api_key_service),
) -> Dict[str, Any]:
    """
    Delete an API key.
    
    - **workspace_id**: Workspace ID (path parameter)
    - **api_key_id**: API Key ID (path parameter)
    
    Requires workspace membership.
    Deletes the API key and updates workspace API key count.
    """
    result = api_key_service.delete_api_key(
        api_key_id=api_key_id,
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="API key deleted successfully",
        code=status.HTTP_200_OK,
    ).model_dump()

