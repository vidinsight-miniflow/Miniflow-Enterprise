"""Workspace member service schemas for frontend routes."""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


# ============================================================================
# MEMBER LIST SCHEMAS
# ============================================================================

class WorkspaceMemberItem(BaseModel):
    """Schema for a single workspace member."""
    id: str = Field(..., description="Member ID")
    user_id: str = Field(..., description="User ID")
    user_name: Optional[str] = Field(None, description="User name")
    user_email: Optional[str] = Field(None, description="User email")
    role_id: str = Field(..., description="Role ID")
    role_name: str = Field(..., description="Role name")
    joined_at: Optional[str] = Field(None, description="Join timestamp (ISO format)")
    last_accessed_at: Optional[str] = Field(None, description="Last access timestamp (ISO format)")


class WorkspaceMembersResponse(BaseModel):
    """Response schema for workspace members list."""
    workspace_id: str = Field(..., description="Workspace ID")
    members: List[WorkspaceMemberItem] = Field(..., description="List of members")
    total_count: int = Field(..., description="Total member count")


# ============================================================================
# MEMBER DETAILS SCHEMAS
# ============================================================================

class MemberDetailsResponse(BaseModel):
    """Response schema for member details."""
    id: str = Field(..., description="Member ID")
    workspace_id: str = Field(..., description="Workspace ID")
    user_id: str = Field(..., description="User ID")
    user_name: Optional[str] = Field(None, description="User name")
    user_email: Optional[str] = Field(None, description="User email")
    role_id: str = Field(..., description="Role ID")
    role_name: str = Field(..., description="Role name")
    invited_by: Optional[str] = Field(None, description="User ID who invited this member")
    joined_at: Optional[str] = Field(None, description="Join timestamp (ISO format)")
    last_accessed_at: Optional[str] = Field(None, description="Last access timestamp (ISO format)")
    custom_permissions: Optional[Dict[str, bool]] = Field(None, description="Custom permissions override")


# ============================================================================
# USER WORKSPACES SCHEMAS
# ============================================================================

class UserWorkspaceItem(BaseModel):
    """Schema for a single user workspace."""
    workspace_id: str = Field(..., description="Workspace ID")
    workspace_name: str = Field(..., description="Workspace name")
    workspace_slug: str = Field(..., description="Workspace slug")
    role: str = Field(..., description="User role in workspace")


class UserWorkspacesResponse(BaseModel):
    """Response schema for user workspaces."""
    owned_workspaces: List[UserWorkspaceItem] = Field(..., description="Workspaces owned by user")
    memberships: List[UserWorkspaceItem] = Field(..., description="Workspaces where user is a member")


# ============================================================================
# CHANGE ROLE SCHEMAS
# ============================================================================

class ChangeMemberRoleRequest(BaseModel):
    """Request schema for changing member role."""
    new_role_id: str = Field(..., description="New role ID")


class ChangeMemberRoleResponse(BaseModel):
    """Response schema for changing member role."""
    id: str = Field(..., description="Member ID")
    user_id: str = Field(..., description="User ID")
    role_id: str = Field(..., description="New role ID")
    role_name: str = Field(..., description="New role name")


# ============================================================================
# REMOVE MEMBER SCHEMAS
# ============================================================================

class RemoveMemberResponse(BaseModel):
    """Response schema for removing member."""
    success: bool = Field(..., description="Success status")
    workspace_id: str = Field(..., description="Workspace ID")
    removed_user_id: str = Field(..., description="Removed user ID")


# ============================================================================
# CUSTOM PERMISSIONS SCHEMAS
# ============================================================================

class SetCustomPermissionsRequest(BaseModel):
    """Request schema for setting custom permissions."""
    custom_permissions: Dict[str, bool] = Field(..., description="Custom permissions dictionary")


class SetCustomPermissionsResponse(BaseModel):
    """Response schema for setting custom permissions."""
    id: str = Field(..., description="Member ID")
    custom_permissions: Dict[str, bool] = Field(..., description="Custom permissions")


class ClearCustomPermissionsResponse(BaseModel):
    """Response schema for clearing custom permissions."""
    success: bool = Field(..., description="Success status")

