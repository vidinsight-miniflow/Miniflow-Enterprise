"""Workspace management service schemas for frontend routes."""

from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


# ============================================================================
# CREATE WORKSPACE SCHEMAS
# ============================================================================

class CreateWorkspaceRequest(BaseModel):
    """Request schema for creating workspace."""
    name: str = Field(..., min_length=1, max_length=100, description="Workspace name")
    slug: str = Field(..., min_length=1, max_length=50, description="URL-friendly workspace slug")
    description: Optional[str] = Field(None, max_length=500, description="Workspace description")


class CreateWorkspaceResponse(BaseModel):
    """Response schema for creating workspace."""
    id: str = Field(..., description="Workspace ID")
    name: str = Field(..., description="Workspace name")
    slug: str = Field(..., description="Workspace slug")
    description: Optional[str] = Field(None, description="Workspace description")
    owner_id: str = Field(..., description="Owner user ID")
    plan_id: str = Field(..., description="Plan ID")


# ============================================================================
# WORKSPACE DETAILS SCHEMAS
# ============================================================================

class WorkspaceResponse(BaseModel):
    """Response schema for workspace basic info."""
    id: str = Field(..., description="Workspace ID")
    name: str = Field(..., description="Workspace name")
    slug: str = Field(..., description="Workspace slug")
    owner_id: str = Field(..., description="Owner user ID")
    plan_id: str = Field(..., description="Plan ID")
    is_suspended: bool = Field(False, description="Is workspace suspended?")


class WorkspaceDetailsResponse(BaseModel):
    """Response schema for workspace details."""
    id: str = Field(..., description="Workspace ID")
    name: str = Field(..., description="Workspace name")
    slug: str = Field(..., description="Workspace slug")
    description: Optional[str] = Field(None, description="Workspace description")
    owner_id: str = Field(..., description="Owner user ID")
    owner_name: Optional[str] = Field(None, description="Owner name")
    owner_email: Optional[str] = Field(None, description="Owner email")
    plan_id: str = Field(..., description="Plan ID")
    is_suspended: bool = Field(False, description="Is workspace suspended?")
    suspension_reason: Optional[str] = Field(None, description="Suspension reason")
    created_at: Optional[str] = Field(None, description="Creation timestamp (ISO format)")


class WorkspaceLimitsResponse(BaseModel):
    """Response schema for workspace limits and usage."""
    members: Dict[str, Any] = Field(..., description="Member limits and usage")
    workflows: Dict[str, Any] = Field(..., description="Workflow limits and usage")
    custom_scripts: Dict[str, Any] = Field(..., description="Custom script limits and usage")
    storage_mb: Dict[str, Any] = Field(..., description="Storage limits and usage")
    api_keys: Dict[str, Any] = Field(..., description="API key limits and usage")
    monthly_executions: Dict[str, Any] = Field(..., description="Monthly execution limits and usage")
    concurrent_executions: Dict[str, Any] = Field(..., description="Concurrent execution limits")
    billing_period: Dict[str, Optional[str]] = Field(..., description="Billing period dates")
    max_file_size_mb: Optional[int] = Field(None, description="Maximum file size in MB")


# ============================================================================
# UPDATE WORKSPACE SCHEMAS
# ============================================================================

class UpdateWorkspaceRequest(BaseModel):
    """Request schema for updating workspace."""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Workspace name")
    slug: Optional[str] = Field(None, min_length=1, max_length=50, description="Workspace slug")
    description: Optional[str] = Field(None, max_length=500, description="Workspace description")


class UpdateWorkspaceResponse(BaseModel):
    """Response schema for updating workspace."""
    id: str = Field(..., description="Workspace ID")
    name: str = Field(..., description="Workspace name")
    slug: str = Field(..., description="Workspace slug")
    description: Optional[str] = Field(None, description="Workspace description")


# ============================================================================
# DELETE WORKSPACE SCHEMAS
# ============================================================================

class DeleteWorkspaceResponse(BaseModel):
    """Response schema for deleting workspace."""
    success: bool = Field(..., description="Success status")
    workspace_id: str = Field(..., description="Deleted workspace ID")
    deleted_members: int = Field(..., description="Number of deleted members")
    deleted_invitations: int = Field(..., description="Number of deleted invitations")


# ============================================================================
# SUSPEND/UNSUSPEND SCHEMAS
# ============================================================================

class SuspendWorkspaceRequest(BaseModel):
    """Request schema for suspending workspace."""
    reason: str = Field(..., min_length=1, description="Suspension reason")


class SuspendWorkspaceResponse(BaseModel):
    """Response schema for suspending workspace."""
    success: bool = Field(..., description="Success status")
    suspended_at: str = Field(..., description="Suspension timestamp (ISO format)")


class UnsuspendWorkspaceResponse(BaseModel):
    """Response schema for unsuspending workspace."""
    success: bool = Field(..., description="Success status")


# ============================================================================
# TRANSFER OWNERSHIP SCHEMAS
# ============================================================================

class TransferOwnershipRequest(BaseModel):
    """Request schema for transferring ownership."""
    new_owner_id: str = Field(..., description="New owner user ID")


class TransferOwnershipResponse(BaseModel):
    """Response schema for transferring ownership."""
    success: bool = Field(..., description="Success status")
    workspace_id: str = Field(..., description="Workspace ID")
    previous_owner_id: str = Field(..., description="Previous owner ID")
    new_owner_id: str = Field(..., description="New owner ID")

