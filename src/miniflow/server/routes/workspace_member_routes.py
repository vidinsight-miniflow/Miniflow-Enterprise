"""
Workspace Member management routes.

Handles workspace membership, member roles, and member operations.
"""
from fastapi import APIRouter, Depends, Request, status, Path
from typing import Dict, Any

from src.miniflow.server.dependencies import get_workspace_member_service
from src.miniflow.services import WorkspaceMemberService
from src.miniflow.server.helpers import (
    validate_workspace_member,
    authenticate_user,
    AuthUser,
)
from src.miniflow.server.schemas.base_schema import create_success_response
from src.miniflow.server.schemas.routes.workspace_schemas.workspace_member_schemas import (
    ChangeUserRoleRequest,
)

router = APIRouter(prefix="/workspaces", tags=["workspace-members"])


# ============================================================================
# GET WORKSPACE MEMBERS
# ============================================================================

@router.get(
    "/{workspace_id}/members",
    summary="Get workspace members",
    description="Get all members of a workspace",
    status_code=status.HTTP_200_OK,
)
async def get_workspace_members(
    request: Request,
    workspace_id: str = Depends(validate_workspace_member),
    workspace_member_service: WorkspaceMemberService = Depends(get_workspace_member_service),
) -> Dict[str, Any]:
    """
    Get all members of a workspace.
    
    - **workspace_id**: Workspace ID (path parameter)
    
    Requires authentication and workspace membership.
    Returns list of all workspace members with their details.
    """
    result = workspace_member_service.get_workspace_members(workspace_id=workspace_id)
    
    return create_success_response(
        request=request,
        data={"members": result, "total": len(result)},
        message="Workspace members retrieved successfully",
        code=status.HTTP_200_OK,
    ).model_dump()


# ============================================================================
# GET WORKSPACE MEMBER
# ============================================================================

@router.get(
    "/{workspace_id}/members/{member_id}",
    summary="Get workspace member",
    description="Get detailed information about a specific workspace member",
    status_code=status.HTTP_200_OK,
)
async def get_workspace_member(
    request: Request,
    workspace_id: str = Depends(validate_workspace_member),
    member_id: str = Path(..., description="Member ID"),
    workspace_member_service: WorkspaceMemberService = Depends(get_workspace_member_service),
) -> Dict[str, Any]:
    """
    Get detailed information about a workspace member.
    
    - **workspace_id**: Workspace ID (path parameter)
    - **member_id**: Member ID (path parameter)
    
    Requires authentication and workspace membership.
    Returns detailed member information including role and permissions.
    """
    result = workspace_member_service.get_workspace_member(member_id=member_id)
    
    return create_success_response(
        request=request,
        data=result,
        message="Workspace member retrieved successfully",
        code=status.HTTP_200_OK,
    ).model_dump()


# ============================================================================
# CHANGE USER ROLE
# ============================================================================

@router.put(
    "/{workspace_id}/members/{member_id}/role",
    summary="Change member role",
    description="Change the role of a workspace member",
    status_code=status.HTTP_200_OK,
)
async def change_user_role(
    request: Request,
    workspace_id: str = Depends(validate_workspace_member),
    member_id: str = Path(..., description="Member ID"),
    body: ChangeUserRoleRequest = ...,
    workspace_member_service: WorkspaceMemberService = Depends(get_workspace_member_service),
) -> Dict[str, Any]:
    """
    Change the role of a workspace member.
    
    - **workspace_id**: Workspace ID (path parameter)
    - **member_id**: Member ID (path parameter)
    - **role_id**: New role ID (request body)
    
    Requires authentication and workspace membership.
    Only workspace owners/admins can change member roles.
    """
    result = workspace_member_service.change_user_role(
        member_id=member_id,
        role_id=body.role_id,
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="Member role updated successfully",
        code=status.HTTP_200_OK,
    ).model_dump()


# ============================================================================
# DELETE USER FROM WORKSPACE
# ============================================================================

@router.delete(
    "/{workspace_id}/members/{user_id}",
    summary="Remove member from workspace",
    description="Remove a user from workspace (cannot remove owner)",
    status_code=status.HTTP_200_OK,
)
async def delete_user_from_workspace(
    request: Request,
    workspace_id: str = Depends(validate_workspace_member),
    user_id: str = Path(..., description="User ID to remove"),
    workspace_member_service: WorkspaceMemberService = Depends(get_workspace_member_service),
) -> Dict[str, Any]:
    """
    Remove a user from workspace.
    
    - **workspace_id**: Workspace ID (path parameter)
    - **user_id**: User ID to remove (path parameter)
    
    Requires authentication and workspace membership.
    Cannot remove workspace owner. Transfer ownership first or delete workspace.
    """
    result = workspace_member_service.delete_user_from_workspace(
        workspace_id=workspace_id,
        user_id=user_id,
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="Member removed from workspace successfully",
        code=status.HTTP_200_OK,
    ).model_dump()

