"""
Workspace Invitation management routes.

Handles workspace invitations, including creating, accepting, declining, and canceling invitations.
"""
from fastapi import APIRouter, Depends, Request, status, Path
from typing import Dict, Any

from src.miniflow.server.dependencies import get_workspace_invatation_service
from src.miniflow.services import WorkspaceInvatationService
from src.miniflow.server.helpers import (
    validate_workspace_member,
    authenticate_user,
    AuthUser,
)
from src.miniflow.server.schemas.base_schema import create_success_response
from src.miniflow.server.schemas.routes.workspace_schemas.workspace_invitation_schemas import (
    InviteUserToWorkspaceRequest,
)

router = APIRouter(tags=["workspace-invitations"])


# ============================================================================
# GET USER PENDING INVITATIONS
# ============================================================================

@router.get(
    "/users/{user_id}/invitations/pending",
    summary="Get user pending invitations",
    description="Get all pending workspace invitations for a user",
    status_code=status.HTTP_200_OK,
)
async def get_user_pending_invitations(
    request: Request,
    user_id: str = Path(..., description="User ID"),
    current_user: AuthUser = Depends(authenticate_user),
    invitation_service: WorkspaceInvatationService = Depends(get_workspace_invatation_service),
) -> Dict[str, Any]:
    """
    Get all pending workspace invitations for a user.
    
    - **user_id**: User ID (path parameter)
    
    Requires authentication. Users can only view their own pending invitations.
    """
    # Security: Users can only view their own invitations
    if current_user["user_id"] != user_id:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own invitations"
        )
    
    result = invitation_service.get_user_pending_invitations(user_id=user_id)
    
    return create_success_response(
        request=request,
        data=result,
        message="Pending invitations retrieved successfully",
        code=status.HTTP_200_OK,
    ).model_dump()


# ============================================================================
# GET WORKSPACE INVITATIONS
# ============================================================================

@router.get(
    "/workspaces/{workspace_id}/invitations",
    summary="Get workspace invitations",
    description="Get all invitations for a workspace",
    status_code=status.HTTP_200_OK,
)
async def get_workspace_invitations(
    request: Request,
    workspace_id: str = Depends(validate_workspace_member),
    invitation_service: WorkspaceInvatationService = Depends(get_workspace_invatation_service),
) -> Dict[str, Any]:
    """
    Get all invitations for a workspace.
    
    - **workspace_id**: Workspace ID (path parameter)
    
    Requires workspace membership.
    Returns all invitations (pending, accepted, declined, cancelled).
    """
    result = invitation_service.get_workspace_invitations(workspace_id=workspace_id)
    
    return create_success_response(
        request=request,
        data={"invitations": result, "count": len(result)},
        message="Workspace invitations retrieved successfully",
        code=status.HTTP_200_OK,
    ).model_dump()


# ============================================================================
# INVITE USER TO WORKSPACE
# ============================================================================

@router.post(
    "/workspaces/{workspace_id}/invitations",
    summary="Invite user to workspace",
    description="Invite a user to join a workspace with a specific role",
    status_code=status.HTTP_201_CREATED,
)
async def invite_user_to_workspace(
    request: Request,
    workspace_id: str = Depends(validate_workspace_member),
    body: InviteUserToWorkspaceRequest = ...,
    current_user: AuthUser = Depends(authenticate_user),
    invitation_service: WorkspaceInvatationService = Depends(get_workspace_invatation_service),
) -> Dict[str, Any]:
    """
    Invite a user to join a workspace.
    
    - **workspace_id**: Workspace ID (path parameter)
    - **user_id**: User ID to invite (request body)
    - **role_id**: Role ID for the invitation (request body)
    - **message**: Optional invitation message (request body)
    
    Requires workspace membership.
    The authenticated user will be recorded as the inviter.
    """
    result = invitation_service.invite_user_to_workspace(
        workspace_id=workspace_id,
        invited_by=current_user["user_id"],
        user_id=body.user_id,
        role_id=body.role_id,
        message=body.message,
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="User invited successfully",
        code=status.HTTP_201_CREATED,
    ).model_dump()


# ============================================================================
# ACCEPT INVITATION
# ============================================================================

@router.post(
    "/invitations/{invitation_id}/accept",
    summary="Accept invitation",
    description="Accept a workspace invitation",
    status_code=status.HTTP_200_OK,
)
async def accept_invitation(
    request: Request,
    invitation_id: str = Path(..., description="Invitation ID"),
    current_user: AuthUser = Depends(authenticate_user),
    invitation_service: WorkspaceInvatationService = Depends(get_workspace_invatation_service),
) -> Dict[str, Any]:
    """
    Accept a workspace invitation.
    
    - **invitation_id**: Invitation ID (path parameter)
    
    Requires authentication. Users can only accept their own invitations.
    Upon acceptance, the user becomes a member of the workspace.
    """
    result = invitation_service.accept_invitation(
        invitation_id=invitation_id,
        accepted_by=current_user["user_id"],
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="Invitation accepted successfully",
        code=status.HTTP_200_OK,
    ).model_dump()


# ============================================================================
# DECLINE INVITATION
# ============================================================================

@router.post(
    "/invitations/{invitation_id}/decline",
    summary="Decline invitation",
    description="Decline a workspace invitation",
    status_code=status.HTTP_200_OK,
)
async def decline_invitation(
    request: Request,
    invitation_id: str = Path(..., description="Invitation ID"),
    current_user: AuthUser = Depends(authenticate_user),
    invitation_service: WorkspaceInvatationService = Depends(get_workspace_invatation_service),
) -> Dict[str, Any]:
    """
    Decline a workspace invitation.
    
    - **invitation_id**: Invitation ID (path parameter)
    
    Requires authentication. Users can only decline their own invitations.
    """
    result = invitation_service.decline_invitation(
        invitation_id=invitation_id,
        user_id=current_user["user_id"],
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="Invitation declined successfully",
        code=status.HTTP_200_OK,
    ).model_dump()


# ============================================================================
# CANCEL INVITATION
# ============================================================================

@router.delete(
    "/invitations/{invitation_id}",
    summary="Cancel invitation",
    description="Cancel a workspace invitation (only by the inviter)",
    status_code=status.HTTP_200_OK,
)
async def cancel_invitation(
    request: Request,
    invitation_id: str = Path(..., description="Invitation ID"),
    current_user: AuthUser = Depends(authenticate_user),
    invitation_service: WorkspaceInvatationService = Depends(get_workspace_invatation_service),
) -> Dict[str, Any]:
    """
    Cancel a workspace invitation.
    
    - **invitation_id**: Invitation ID (path parameter)
    
    Requires authentication. Only the user who created the invitation can cancel it.
    """
    result = invitation_service.cancel_invitation(
        invitation_id=invitation_id,
        cancelled_by=current_user["user_id"],
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="Invitation cancelled successfully",
        code=status.HTTP_200_OK,
    ).model_dump()

