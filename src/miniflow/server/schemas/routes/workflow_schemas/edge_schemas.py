"""
Edge request schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional


class CreateEdgeRequest(BaseModel):
    """Request schema for creating an edge."""
    from_node_id: str = Field(..., description="Source node ID (must belong to the workflow)")
    to_node_id: str = Field(..., description="Target node ID (must belong to the workflow)")


class UpdateEdgeRequest(BaseModel):
    """Request schema for updating an edge."""
    from_node_id: Optional[str] = Field(None, description="Source node ID (must belong to the workflow)")
    to_node_id: Optional[str] = Field(None, description="Target node ID (must belong to the workflow)")

