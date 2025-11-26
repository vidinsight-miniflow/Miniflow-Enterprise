"""
Workspace management routes.

Handles workspace creation, retrieval, updates, and deletion.
"""
from fastapi import APIRouter, Depends, Request, status, Path
from typing import Dict, Any

from src.miniflow.server.dependencies import get_workspace_service
from src.miniflow.services import WorkspaceService
from src.miniflow.server.helpers import (
    validate_workspace_member,
    authenticate_user,
    AuthUser,
)
from src.miniflow.server.schemas.base_schema import create_success_response
from src.miniflow.server.schemas.routes.workspace_schemas.workspace_schemas import (
    CreateWorkspaceRequest,
    UpdateWorkspaceRequest,
)

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


# ============================================================================
# CREATE WORKSPACE
# ============================================================================

@router.post(
    "",
    summary="Create workspace",
    description="Create a new workspace (user becomes owner)",
    status_code=status.HTTP_201_CREATED,
)
async def create_workspace(
    request: Request,
    body: CreateWorkspaceRequest,
    current_user: AuthUser = Depends(authenticate_user),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
) -> Dict[str, Any]:
    """
    Create a new workspace.
    
    - **name**: Workspace name (1-100 characters)
    - **slug**: Workspace slug (URL-friendly identifier, 1-100 characters)
    - **description**: Workspace description (optional, max 500 characters)
    
    Requires authentication. User becomes the workspace owner.
    Workspace is created with Freemium plan by default.
    """
    result = workspace_service.create_workspace(
        name=body.name,
        slug=body.slug,
        description=body.description,
        owner_id=current_user["user_id"],
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="Workspace created successfully",
        code=status.HTTP_201_CREATED,
    ).model_dump()


# ============================================================================
# GET WORKSPACE DETAILS
# ============================================================================

@router.get(
    "/{workspace_id}",
    summary="Get workspace details",
    description="Get detailed information about a workspace",
    status_code=status.HTTP_200_OK,
)
async def get_workspace_details(
    request: Request,
    workspace_id: str = Depends(validate_workspace_member),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
) -> Dict[str, Any]:
    """
    Get workspace details.
    
    - **workspace_id**: Workspace ID (path parameter)
    
    Requires authentication and workspace membership.
    Returns workspace information including owner details.
    """
    result = workspace_service.get_workspace_details(workspace_id=workspace_id)
    
    return create_success_response(
        request=request,
        data=result,
        message="Workspace details retrieved successfully",
        code=status.HTTP_200_OK,
    ).model_dump()


# ============================================================================
# GET WORKSPACE LIMITS
# ============================================================================

@router.get(
    "/{workspace_id}/limits",
    summary="Get workspace limits",
    description="Get workspace resource limits and current usage",
    status_code=status.HTTP_200_OK,
)
async def get_workspace_limits(
    request: Request,
    workspace_id: str = Depends(validate_workspace_member),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
) -> Dict[str, Any]:
    """
    Get workspace resource limits and current usage.
    
    - **workspace_id**: Workspace ID (path parameter)
    
    Requires authentication and workspace membership.
    Returns limits for members, workflows, scripts, storage, API keys, and executions.
    """
    result = workspace_service.get_workspace_limits(workspace_id=workspace_id)
    
    return create_success_response(
        request=request,
        data=result,
        message="Workspace limits retrieved successfully",
        code=status.HTTP_200_OK,
    ).model_dump()


# ============================================================================
# UPDATE WORKSPACE
# ============================================================================

@router.put(
    "/{workspace_id}",
    summary="Update workspace",
    description="Update workspace information (name, slug, description)",
    status_code=status.HTTP_200_OK,
)
async def update_workspace(
    request: Request,
    workspace_id: str = Depends(validate_workspace_member),
    body: UpdateWorkspaceRequest = ...,
    workspace_service: WorkspaceService = Depends(get_workspace_service),
) -> Dict[str, Any]:
    """
    Update workspace information.
    
    - **workspace_id**: Workspace ID (path parameter)
    - **name**: Workspace name (optional)
    - **slug**: Workspace slug (optional)
    - **description**: Workspace description (optional)
    
    Requires authentication and workspace membership.
    Only provided fields will be updated.
    """
    result = workspace_service.update_workspace(
        workspace_id=workspace_id,
        name=body.name,
        slug=body.slug,
        description=body.description,
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="Workspace updated successfully",
        code=status.HTTP_200_OK,
    ).model_dump()


# ============================================================================
# DELETE WORKSPACE
# ============================================================================

@router.delete(
    "/{workspace_id}",
    summary="Delete workspace",
    description="Delete workspace and all associated resources",
    status_code=status.HTTP_200_OK,
)
async def delete_workspace(
    request: Request,
    workspace_id: str = Depends(validate_workspace_member),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
) -> Dict[str, Any]:
    """
    Delete workspace and all associated resources.
    
    - **workspace_id**: Workspace ID (path parameter)
    
    Requires authentication and workspace membership.
    Permanently deletes workspace and all related data:
    - Members, invitations, workflows, scripts, executions
    - Variables, files, databases, credentials, API keys
    - Workspace folders and files
    
    ⚠️ WARNING: This action cannot be undone!
    """
    result = workspace_service.delete_workspace(workspace_id=workspace_id)
    
    return create_success_response(
        request=request,
        data=result,
        message="Workspace deleted successfully",
        code=status.HTTP_200_OK,
    ).model_dump()

