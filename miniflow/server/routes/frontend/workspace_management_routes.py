"""Workspace management routes for frontend."""

from fastapi import APIRouter, Request, Depends, Path

from miniflow.server.dependencies import (
    get_workspace_management_service,
    authenticate_user,
    require_workspace_access,
    require_workspace_owner,
)
from miniflow.server.dependencies.auth import AuthenticatedUser
from miniflow.server.schemas.base_schemas import create_success_response
from .schemas.workspace_management_schemas import (
    CreateWorkspaceRequest,
    CreateWorkspaceResponse,
    WorkspaceResponse,
    WorkspaceDetailsResponse,
    WorkspaceLimitsResponse,
    UpdateWorkspaceRequest,
    UpdateWorkspaceResponse,
    DeleteWorkspaceResponse,
    SuspendWorkspaceRequest,
    SuspendWorkspaceResponse,
    UnsuspendWorkspaceResponse,
    TransferOwnershipRequest,
    TransferOwnershipResponse,
)

router = APIRouter(prefix="/workspaces", tags=["Workspace Management"])


# ============================================================================
# CREATE WORKSPACE ENDPOINTS
# ============================================================================

@router.post("", response_model_exclude_none=True)
async def create_workspace(
    request: Request,
    workspace_data: CreateWorkspaceRequest,
    service = Depends(get_workspace_management_service),
    current_user: AuthenticatedUser = Depends(authenticate_user),
) -> dict:
    """
    Create a new workspace.
    
    Requires: User authentication
    Note: User can only have 1 free workspace. Default plan is Freemium.
    """
    result = service.create_workspace(
        name=workspace_data.name,
        slug=workspace_data.slug,
        owner_id=current_user["user_id"],
        description=workspace_data.description
    )
    
    response_data = CreateWorkspaceResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Workspace created successfully."
    )


# ============================================================================
# GET WORKSPACE ENDPOINTS
# ============================================================================

@router.get("/{workspace_id}", response_model_exclude_none=True)
async def get_workspace(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    service = Depends(get_workspace_management_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Get workspace basic information.
    
    Requires: Workspace access
    """
    result = service.get_workspace(workspace_id=workspace_id)
    
    response_data = WorkspaceResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump()
    )


@router.get("/{workspace_id}/details", response_model_exclude_none=True)
async def get_workspace_details(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    service = Depends(get_workspace_management_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Get workspace detailed information.
    
    Requires: Workspace access
    """
    result = service.get_workspace_details(workspace_id=workspace_id)
    
    response_data = WorkspaceDetailsResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump()
    )


@router.get("/{workspace_id}/limits", response_model_exclude_none=True)
async def get_workspace_limits(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    service = Depends(get_workspace_management_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Get workspace limits and current usage.
    
    Requires: Workspace access
    """
    result = service.get_workspace_limits(workspace_id=workspace_id)
    
    response_data = WorkspaceLimitsResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump()
    )


@router.get("/slug/{slug}", response_model_exclude_none=True)
async def get_workspace_by_slug(
    request: Request,
    slug: str = Path(..., description="Workspace slug"),
    service = Depends(get_workspace_management_service),
    current_user: AuthenticatedUser = Depends(authenticate_user),
) -> dict:
    """
    Get workspace by slug.
    
    Requires: User authentication
    """
    result = service.get_workspace_by_slug(slug=slug)
    
    response_data = WorkspaceResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump()
    )


# ============================================================================
# UPDATE WORKSPACE ENDPOINTS
# ============================================================================

@router.put("/{workspace_id}", response_model_exclude_none=True)
async def update_workspace(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    workspace_data: UpdateWorkspaceRequest = ...,
    service = Depends(get_workspace_management_service),
    _: str = Depends(require_workspace_owner),
) -> dict:
    """
    Update workspace information.
    
    Requires: Workspace owner
    """
    result = service.update_workspace(
        workspace_id=workspace_id,
        name=workspace_data.name,
        slug=workspace_data.slug,
        description=workspace_data.description
    )
    
    response_data = UpdateWorkspaceResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Workspace updated successfully."
    )


# ============================================================================
# DELETE WORKSPACE ENDPOINTS
# ============================================================================

@router.delete("/{workspace_id}", response_model_exclude_none=True)
async def delete_workspace(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    service = Depends(get_workspace_management_service),
    _: str = Depends(require_workspace_owner),
) -> dict:
    """
    Delete workspace and all related data.
    
    Requires: Workspace owner
    Warning: This action cannot be undone!
    """
    result = service.delete_workspace(workspace_id=workspace_id)
    
    response_data = DeleteWorkspaceResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Workspace deleted successfully."
    )


# ============================================================================
# SUSPEND/UNSUSPEND ENDPOINTS
# ============================================================================

@router.post("/{workspace_id}/suspend", response_model_exclude_none=True)
async def suspend_workspace(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    suspend_data: SuspendWorkspaceRequest = ...,
    service = Depends(get_workspace_management_service),
    current_user: AuthenticatedUser = Depends(authenticate_user),
) -> dict:
    """
    Suspend workspace.
    
    Requires: Admin authentication (TODO: Add admin check)
    """
    result = service.suspend_workspace(
        workspace_id=workspace_id,
        reason=suspend_data.reason
    )
    
    response_data = SuspendWorkspaceResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Workspace suspended successfully."
    )


@router.post("/{workspace_id}/unsuspend", response_model_exclude_none=True)
async def unsuspend_workspace(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    service = Depends(get_workspace_management_service),
    current_user: AuthenticatedUser = Depends(authenticate_user),
) -> dict:
    """
    Unsuspend workspace.
    
    Requires: Admin authentication (TODO: Add admin check)
    """
    result = service.unsuspend_workspace(workspace_id=workspace_id)
    
    response_data = UnsuspendWorkspaceResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Workspace unsuspended successfully."
    )


# ============================================================================
# TRANSFER OWNERSHIP ENDPOINTS
# ============================================================================

@router.post("/{workspace_id}/transfer-ownership", response_model_exclude_none=True)
async def transfer_ownership(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    transfer_data: TransferOwnershipRequest = ...,
    service = Depends(get_workspace_management_service),
    current_user: AuthenticatedUser = Depends(authenticate_user),
) -> dict:
    """
    Transfer workspace ownership to another user.
    
    Requires: Workspace owner
    Note: New owner must be an existing member of the workspace.
    """
    result = service.transfer_ownership(
        workspace_id=workspace_id,
        current_owner_id=current_user["user_id"],
        new_owner_id=transfer_data.new_owner_id
    )
    
    response_data = TransferOwnershipResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Ownership transferred successfully."
    )

