"""Edge schemas for frontend."""

from typing import Optional, List
from pydantic import BaseModel, Field


# ============================================================================
# CREATE REQUEST/RESPONSE
# ============================================================================

class CreateEdgeRequest(BaseModel):
    """Request schema for creating an edge."""
    from_node_id: str = Field(..., description="Source node ID")
    to_node_id: str = Field(..., description="Target node ID")


class CreateEdgeResponse(BaseModel):
    """Response schema for creating an edge."""
    id: str = Field(..., description="Edge ID")


# ============================================================================
# EDGE ITEM (for lists)
# ============================================================================

class EdgeItem(BaseModel):
    """Schema for edge item in lists."""
    id: str
    from_node_id: str
    to_node_id: str


# ============================================================================
# EDGE RESPONSE
# ============================================================================

class EdgeResponse(BaseModel):
    """Response schema for edge details."""
    id: str
    workflow_id: str
    from_node_id: str
    to_node_id: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    created_by: Optional[str] = None


# ============================================================================
# WORKFLOW EDGES RESPONSE
# ============================================================================

class WorkflowEdgesResponse(BaseModel):
    """Response schema for workflow edges list."""
    workflow_id: str
    edges: List[EdgeItem]
    count: int


# ============================================================================
# NODE EDGES RESPONSE
# ============================================================================

class OutgoingEdgeItem(BaseModel):
    """Schema for outgoing edge item."""
    id: str
    to_node_id: str


class IncomingEdgeItem(BaseModel):
    """Schema for incoming edge item."""
    id: str
    from_node_id: str


class OutgoingEdgesResponse(BaseModel):
    """Response schema for outgoing edges."""
    node_id: str
    edges: List[OutgoingEdgeItem]
    count: int


class IncomingEdgesResponse(BaseModel):
    """Response schema for incoming edges."""
    node_id: str
    edges: List[IncomingEdgeItem]
    count: int


# ============================================================================
# UPDATE REQUEST/RESPONSE
# ============================================================================

class UpdateEdgeRequest(BaseModel):
    """Request schema for updating edge."""
    from_node_id: Optional[str] = Field(None, description="New source node ID")
    to_node_id: Optional[str] = Field(None, description="New target node ID")


# ============================================================================
# DELETE RESPONSE
# ============================================================================

class DeleteEdgeResponse(BaseModel):
    """Response schema for deleting an edge."""
    success: bool
    deleted_id: str

