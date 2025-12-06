"""Workspace member routes for frontend."""

from fastapi import APIRouter, Request, Depends, Path

from miniflow.server.dependencies import (
    get_workspace_member_service,
    authenticate_user,
    require_workspace_access,
    require_workspace_owner,
)
from miniflow.server.dependencies.auth import AuthenticatedUser
from miniflow.server.schemas.base_schemas import create_success_response
from .schemas.workspace_member_schemas import (
    WorkspaceMembersResponse,
    MemberDetailsResponse,
    UserWorkspacesResponse,
    ChangeMemberRoleRequest,
    ChangeMemberRoleResponse,
    RemoveMemberResponse,
    SetCustomPermissionsRequest,
    SetCustomPermissionsResponse,
    ClearCustomPermissionsResponse,
)

router = APIRouter(prefix="/workspaces", tags=["Workspace Members"])


# ============================================================================
# GET MEMBERS ENDPOINTS
# ============================================================================

@router.get("/{workspace_id}/members", response_model_exclude_none=True)
async def get_workspace_members(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    service = Depends(get_workspace_member_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Get all workspace members.
    
    Requires: Workspace access
    """
    result = service.get_workspace_members(workspace_id=workspace_id)
    
    response_data = WorkspaceMembersResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump()
    )


@router.get("/{workspace_id}/members/{member_id}", response_model_exclude_none=True)
async def get_member_details(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    member_id: str = Path(..., description="Member ID"),
    service = Depends(get_workspace_member_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Get member details.
    
    Requires: Workspace access
    """
    result = service.get_member_details(member_id=member_id)
    
    response_data = MemberDetailsResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump()
    )


@router.get("/user/{user_id}/workspaces", response_model_exclude_none=True)
async def get_user_workspaces(
    request: Request,
    user_id: str = Path(..., description="User ID"),
    service = Depends(get_workspace_member_service),
    current_user: AuthenticatedUser = Depends(authenticate_user),
) -> dict:
    """
    Get all workspaces for a user.
    
    Requires: User authentication
    Security: Users can only view their own workspaces
    """
    # Security: Users can only view their own workspaces
    if current_user["user_id"] != user_id:
        from miniflow.core.exceptions import PermissionDeniedError
        raise PermissionDeniedError(
            message="You can only view your own workspaces"
        )
    
    result = service.get_user_workspaces(user_id=user_id)
    
    response_data = UserWorkspacesResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump()
    )


# ============================================================================
# CHANGE ROLE ENDPOINTS
# ============================================================================

@router.put("/{workspace_id}/members/{member_id}/role", response_model_exclude_none=True)
async def change_member_role(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    member_id: str = Path(..., description="Member ID"),
    role_data: ChangeMemberRoleRequest = ...,
    service = Depends(get_workspace_member_service),
    _: str = Depends(require_workspace_owner),
) -> dict:
    """
    Change member role.
    
    Requires: Workspace owner
    Note: Owner role cannot be changed. Use transfer ownership instead.
    """
    result = service.change_member_role(
        member_id=member_id,
        new_role_id=role_data.new_role_id
    )
    
    response_data = ChangeMemberRoleResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Member role updated successfully."
    )


# ============================================================================
# REMOVE MEMBER ENDPOINTS
# ============================================================================

@router.delete("/{workspace_id}/members/{user_id}", response_model_exclude_none=True)
async def remove_member(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    user_id: str = Path(..., description="User ID to remove"),
    service = Depends(get_workspace_member_service),
    _: str = Depends(require_workspace_owner),
) -> dict:
    """
    Remove member from workspace.
    
    Requires: Workspace owner
    Note: Owner cannot be removed. Transfer ownership first.
    """
    result = service.remove_member(
        workspace_id=workspace_id,
        user_id=user_id
    )
    
    response_data = RemoveMemberResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Member removed successfully."
    )


@router.post("/{workspace_id}/leave", response_model_exclude_none=True)
async def leave_workspace(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    service = Depends(get_workspace_member_service),
    current_user: AuthenticatedUser = Depends(authenticate_user),
) -> dict:
    """
    Leave workspace.
    
    Requires: User authentication
    Note: Owner cannot leave. Transfer ownership first.
    """
    result = service.leave_workspace(
        workspace_id=workspace_id,
        user_id=current_user["user_id"]
    )
    
    return create_success_response(
        request,
        data={"success": True},
        message="You have left the workspace."
    )


# ============================================================================
# CUSTOM PERMISSIONS ENDPOINTS
# ============================================================================

@router.put("/{workspace_id}/members/{member_id}/permissions", response_model_exclude_none=True)
async def set_custom_permissions(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    member_id: str = Path(..., description="Member ID"),
    permissions_data: SetCustomPermissionsRequest = ...,
    service = Depends(get_workspace_member_service),
    _: str = Depends(require_workspace_owner),
) -> dict:
    """
    Set custom permissions for member.
    
    Requires: Workspace owner
    """
    result = service.set_custom_permissions(
        member_id=member_id,
        custom_permissions=permissions_data.custom_permissions
    )
    
    response_data = SetCustomPermissionsResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Custom permissions updated successfully."
    )


@router.delete("/{workspace_id}/members/{member_id}/permissions", response_model_exclude_none=True)
async def clear_custom_permissions(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    member_id: str = Path(..., description="Member ID"),
    service = Depends(get_workspace_member_service),
    _: str = Depends(require_workspace_owner),
) -> dict:
    """
    Clear custom permissions for member (revert to role-based permissions).
    
    Requires: Workspace owner
    """
    result = service.clear_custom_permissions(member_id=member_id)
    
    response_data = ClearCustomPermissionsResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Custom permissions cleared successfully."
    )

