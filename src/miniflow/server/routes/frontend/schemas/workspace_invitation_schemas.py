"""Workspace invitation service schemas for frontend routes."""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


# ============================================================================
# INVITATION LIST SCHEMAS
# ============================================================================

class PendingInvitationItem(BaseModel):
    """Schema for a single pending invitation."""
    id: str = Field(..., description="Invitation ID")
    workspace_id: str = Field(..., description="Workspace ID")
    workspace_name: Optional[str] = Field(None, description="Workspace name")
    workspace_slug: Optional[str] = Field(None, description="Workspace slug")
    invited_by: str = Field(..., description="User ID who sent invitation")
    inviter_name: Optional[str] = Field(None, description="Inviter name")
    inviter_email: Optional[str] = Field(None, description="Inviter email")
    role_id: str = Field(..., description="Role ID")
    role_name: Optional[str] = Field(None, description="Role name")
    message: Optional[str] = Field(None, description="Invitation message")
    created_at: Optional[str] = Field(None, description="Creation timestamp (ISO format)")


class UserPendingInvitationsResponse(BaseModel):
    """Response schema for user pending invitations."""
    user_id: str = Field(..., description="User ID")
    pending_invitations: List[PendingInvitationItem] = Field(..., description="List of pending invitations")
    count: int = Field(..., description="Total count")


class WorkspaceInvitationItem(BaseModel):
    """Schema for a single workspace invitation."""
    id: str = Field(..., description="Invitation ID")
    invitee_id: Optional[str] = Field(None, description="Invitee user ID")
    invitee_name: Optional[str] = Field(None, description="Invitee name")
    invitee_email: str = Field(..., description="Invitee email")
    invited_by: str = Field(..., description="User ID who sent invitation")
    inviter_name: Optional[str] = Field(None, description="Inviter name")
    role_id: str = Field(..., description="Role ID")
    role_name: Optional[str] = Field(None, description="Role name")
    status: str = Field(..., description="Invitation status (PENDING, ACCEPTED, DECLINED, CANCELLED)")
    message: Optional[str] = Field(None, description="Invitation message")
    created_at: Optional[str] = Field(None, description="Creation timestamp (ISO format)")
    accepted_at: Optional[str] = Field(None, description="Acceptance timestamp (ISO format)")
    declined_at: Optional[str] = Field(None, description="Decline timestamp (ISO format)")


class WorkspaceInvitationsResponse(BaseModel):
    """Response schema for workspace invitations."""
    workspace_id: str = Field(..., description="Workspace ID")
    invitations: List[WorkspaceInvitationItem] = Field(..., description="List of invitations")
    count: int = Field(..., description="Total count")


# ============================================================================
# INVITE USER SCHEMAS
# ============================================================================

class InviteUserRequest(BaseModel):
    """Request schema for inviting user."""
    invitee_id: str = Field(..., description="User ID to invite")
    role_id: str = Field(..., description="Role ID to assign")
    message: Optional[str] = Field(None, max_length=500, description="Invitation message")


class InviteUserResponse(BaseModel):
    """Response schema for inviting user."""
    id: str = Field(..., description="Invitation ID")
    workspace_id: str = Field(..., description="Workspace ID")
    invitee_id: str = Field(..., description="Invitee user ID")
    invitee_email: str = Field(..., description="Invitee email")
    role_id: str = Field(..., description="Role ID")
    status: str = Field(..., description="Invitation status")
    message: Optional[str] = Field(None, description="Invitation message")


# ============================================================================
# ACCEPT/DECLINE INVITATION SCHEMAS
# ============================================================================

class AcceptInvitationResponse(BaseModel):
    """Response schema for accepting invitation."""
    invitation_id: str = Field(..., description="Invitation ID")
    member_id: str = Field(..., description="Created member ID")
    workspace_id: str = Field(..., description="Workspace ID")
    status: str = Field(..., description="Invitation status")
    accepted_at: Optional[str] = Field(None, description="Acceptance timestamp (ISO format)")


class DeclineInvitationResponse(BaseModel):
    """Response schema for declining invitation."""
    id: str = Field(..., description="Invitation ID")
    status: str = Field(..., description="Invitation status")
    declined_at: Optional[str] = Field(None, description="Decline timestamp (ISO format)")


# ============================================================================
# CANCEL/RESEND INVITATION SCHEMAS
# ============================================================================

class CancelInvitationResponse(BaseModel):
    """Response schema for canceling invitation."""
    id: str = Field(..., description="Invitation ID")
    status: str = Field(..., description="Invitation status")


class ResendInvitationResponse(BaseModel):
    """Response schema for resending invitation."""
    success: bool = Field(..., description="Success status")
    invitation_id: str = Field(..., description="Invitation ID")
    invitee_email: str = Field(..., description="Invitee email")

