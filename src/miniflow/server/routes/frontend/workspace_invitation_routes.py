"""Workspace invitation routes for frontend."""

from fastapi import APIRouter, Request, Depends, Path, Query

from miniflow.server.dependencies import (
    get_workspace_invitation_service,
    authenticate_user,
    require_workspace_access,
    require_workspace_owner,
)
from miniflow.server.dependencies.auth import AuthenticatedUser
from miniflow.server.schemas.base_schemas import create_success_response
from .schemas.workspace_invitation_schemas import (
    UserPendingInvitationsResponse,
    WorkspaceInvitationsResponse,
    InviteUserRequest,
    InviteUserResponse,
    AcceptInvitationResponse,
    DeclineInvitationResponse,
    CancelInvitationResponse,
    ResendInvitationResponse,
)

router = APIRouter(prefix="/workspaces", tags=["Workspace Invitations"])


# ============================================================================
# GET INVITATIONS ENDPOINTS
# ============================================================================

@router.get("/user/{user_id}/invitations/pending", response_model_exclude_none=True)
async def get_user_pending_invitations(
    request: Request,
    user_id: str = Path(..., description="User ID"),
    service = Depends(get_workspace_invitation_service),
    current_user: AuthenticatedUser = Depends(authenticate_user),
) -> dict:
    """
    Get user's pending invitations.
    
    Requires: User authentication
    Security: Users can only view their own invitations
    """
    # Security: Users can only view their own invitations
    if current_user["user_id"] != user_id:
        from miniflow.core.exceptions import PermissionDeniedError
        raise PermissionDeniedError(
            message="You can only view your own invitations"
        )
    
    result = service.get_user_pending_invitations(user_id=user_id)
    
    response_data = UserPendingInvitationsResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump()
    )


@router.get("/{workspace_id}/invitations", response_model_exclude_none=True)
async def get_workspace_invitations(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    status_filter: str = Query(None, description="Status filter (PENDING, ACCEPTED, DECLINED, CANCELLED)"),
    service = Depends(get_workspace_invitation_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Get workspace invitations.
    
    Requires: Workspace access
    """
    result = service.get_workspace_invitations(
        workspace_id=workspace_id,
        status_filter=status_filter
    )
    
    response_data = WorkspaceInvitationsResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump()
    )


# ============================================================================
# INVITE USER ENDPOINTS
# ============================================================================

@router.post("/{workspace_id}/invitations", response_model_exclude_none=True)
async def invite_user(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    invitation_data: InviteUserRequest = ...,
    service = Depends(get_workspace_invitation_service),
    current_user: AuthenticatedUser = Depends(authenticate_user),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Invite user to workspace.
    
    Requires: Workspace access (Owner/Admin can invite)
    Note: Member limit is checked automatically.
    """
    result = service.invite_user(
        workspace_id=workspace_id,
        invited_by=current_user["user_id"],
        invitee_id=invitation_data.invitee_id,
        role_id=invitation_data.role_id,
        message=invitation_data.message
    )
    
    response_data = InviteUserResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Invitation sent successfully."
    )


# ============================================================================
# ACCEPT/DECLINE INVITATION ENDPOINTS
# ============================================================================

@router.post("/invitations/{invitation_id}/accept", response_model_exclude_none=True)
async def accept_invitation(
    request: Request,
    invitation_id: str = Path(..., description="Invitation ID"),
    service = Depends(get_workspace_invitation_service),
    current_user: AuthenticatedUser = Depends(authenticate_user),
) -> dict:
    """
    Accept workspace invitation.
    
    Requires: User authentication
    Security: Users can only accept their own invitations
    """
    result = service.accept_invitation(
        invitation_id=invitation_id,
        user_id=current_user["user_id"]
    )
    
    response_data = AcceptInvitationResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Invitation accepted successfully."
    )


@router.post("/invitations/{invitation_id}/decline", response_model_exclude_none=True)
async def decline_invitation(
    request: Request,
    invitation_id: str = Path(..., description="Invitation ID"),
    service = Depends(get_workspace_invitation_service),
    current_user: AuthenticatedUser = Depends(authenticate_user),
) -> dict:
    """
    Decline workspace invitation.
    
    Requires: User authentication
    Security: Users can only decline their own invitations
    """
    result = service.decline_invitation(
        invitation_id=invitation_id,
        user_id=current_user["user_id"]
    )
    
    response_data = DeclineInvitationResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Invitation declined."
    )


# ============================================================================
# CANCEL/RESEND INVITATION ENDPOINTS
# ============================================================================

@router.post("/{workspace_id}/invitations/{invitation_id}/cancel", response_model_exclude_none=True)
async def cancel_invitation(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    invitation_id: str = Path(..., description="Invitation ID"),
    service = Depends(get_workspace_invitation_service),
    current_user: AuthenticatedUser = Depends(authenticate_user),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Cancel workspace invitation.
    
    Requires: Workspace access (Inviter or Owner can cancel)
    """
    result = service.cancel_invitation(
        invitation_id=invitation_id,
        cancelled_by=current_user["user_id"]
    )
    
    response_data = CancelInvitationResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Invitation cancelled successfully."
    )


@router.post("/{workspace_id}/invitations/{invitation_id}/resend", response_model_exclude_none=True)
async def resend_invitation(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    invitation_id: str = Path(..., description="Invitation ID"),
    service = Depends(get_workspace_invitation_service),
    current_user: AuthenticatedUser = Depends(authenticate_user),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Resend workspace invitation.
    
    Requires: Workspace access (Inviter or Owner can resend)
    """
    result = service.resend_invitation(
        invitation_id=invitation_id,
        resent_by=current_user["user_id"]
    )
    
    response_data = ResendInvitationResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Invitation resent successfully."
    )

