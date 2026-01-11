"""Workflow management schemas for frontend."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# ============================================================================
# CREATE REQUEST/RESPONSE
# ============================================================================

class CreateWorkflowRequest(BaseModel):
    """Request schema for creating a workflow."""
    name: str = Field(..., description="Workflow name (unique within workspace)")
    description: Optional[str] = Field(None, description="Workflow description")
    priority: int = Field(default=1, ge=1, description="Priority (must be >= 1)")
    tags: Optional[List[str]] = Field(None, description="Tags")


class CreateWorkflowResponse(BaseModel):
    """Response schema for creating a workflow."""
    id: str = Field(..., description="Workflow ID")


# ============================================================================
# WORKFLOW ITEM (for lists)
# ============================================================================

class WorkflowItem(BaseModel):
    """Schema for workflow item in lists."""
    id: str
    name: str
    description: Optional[str] = None
    priority: int
    status: Optional[str] = None
    tags: Optional[List[str]] = None
    created_at: Optional[str] = None


# ============================================================================
# WORKFLOW RESPONSE
# ============================================================================

class WorkflowResponse(BaseModel):
    """Response schema for workflow details."""
    id: str
    workspace_id: str
    name: str
    description: Optional[str] = None
    priority: int
    status: Optional[str] = None
    status_message: Optional[str] = None
    tags: Optional[List[str]] = None
    node_count: int
    edge_count: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    created_by: Optional[str] = None


# ============================================================================
# WORKSPACE WORKFLOWS RESPONSE
# ============================================================================

class WorkspaceWorkflowsResponse(BaseModel):
    """Response schema for workspace workflows list."""
    workspace_id: str
    workflows: List[WorkflowItem]
    count: int


# ============================================================================
# UPDATE REQUEST/RESPONSE
# ============================================================================

class UpdateWorkflowRequest(BaseModel):
    """Request schema for updating workflow."""
    name: Optional[str] = Field(None, description="New name")
    description: Optional[str] = Field(None, description="New description")
    priority: Optional[int] = Field(None, ge=1, description="New priority (must be >= 1)")
    tags: Optional[List[str]] = Field(None, description="New tags")


# ============================================================================
# STATUS MANAGEMENT RESPONSE
# ============================================================================

class ActivateWorkflowResponse(BaseModel):
    """Response schema for activating workflow."""
    success: bool
    status: str


class DeactivateWorkflowRequest(BaseModel):
    """Request schema for deactivating workflow."""
    reason: Optional[str] = Field(None, description="Deactivation reason")


class DeactivateWorkflowResponse(BaseModel):
    """Response schema for deactivating workflow."""
    success: bool
    status: str


class ArchiveWorkflowResponse(BaseModel):
    """Response schema for archiving workflow."""
    success: bool
    status: str


class SetDraftResponse(BaseModel):
    """Response schema for setting workflow to draft."""
    success: bool
    status: str


# ============================================================================
# DELETE RESPONSE
# ============================================================================

class DeleteWorkflowResponse(BaseModel):
    """Response schema for deleting a workflow."""
    success: bool
    deleted_id: str


# ============================================================================
# GRAPH RESPONSE
# ============================================================================

class GraphNodeItem(BaseModel):
    """Schema for graph node item."""
    id: str
    name: Optional[str] = None
    description: Optional[str] = None
    script_id: Optional[str] = None
    custom_script_id: Optional[str] = None
    script_type: Optional[str] = None
    max_retries: Optional[int] = None
    timeout_seconds: Optional[int] = None
    meta_data: Optional[Dict[str, Any]] = None


class GraphEdgeItem(BaseModel):
    """Schema for graph edge item."""
    id: str
    from_node_id: str
    to_node_id: str


class WorkflowGraphResponse(BaseModel):
    """Response schema for workflow graph."""
    workflow_id: str
    workflow_name: Optional[str] = None
    status: Optional[str] = None
    nodes: List[GraphNodeItem]
    edges: List[GraphEdgeItem]

