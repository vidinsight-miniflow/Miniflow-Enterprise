"""Node schemas for frontend."""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


# ============================================================================
# CREATE REQUEST/RESPONSE
# ============================================================================

class CreateNodeRequest(BaseModel):
    """Request schema for creating a node."""
    name: str = Field(..., description="Node name (unique within workflow)")
    script_id: Optional[str] = Field(None, description="Global script ID (XOR with custom_script_id)")
    custom_script_id: Optional[str] = Field(None, description="Custom script ID (XOR with script_id)")
    description: Optional[str] = Field(None, description="Node description")
    input_params: Optional[Dict[str, Any]] = Field(None, description="Input parameters")
    output_params: Optional[Dict[str, Any]] = Field(None, description="Output parameters")
    meta_data: Optional[Dict[str, Any]] = Field(None, description="Metadata")
    max_retries: int = Field(default=3, ge=0, description="Max retries (>= 0)")
    timeout_seconds: int = Field(default=300, gt=0, description="Timeout in seconds (> 0)")


class CreateNodeResponse(BaseModel):
    """Response schema for creating a node."""
    id: str = Field(..., description="Node ID")


# ============================================================================
# NODE ITEM (for lists)
# ============================================================================

class NodeItem(BaseModel):
    """Schema for node item in lists."""
    id: str
    name: str
    description: Optional[str] = None
    script_id: Optional[str] = None
    custom_script_id: Optional[str] = None
    script_type: Optional[str] = None
    max_retries: Optional[int] = None
    timeout_seconds: Optional[int] = None
    meta_data: Optional[Dict[str, Any]] = None


# ============================================================================
# NODE RESPONSE
# ============================================================================

class NodeResponse(BaseModel):
    """Response schema for node details."""
    id: str
    workflow_id: str
    name: str
    description: Optional[str] = None
    script_id: Optional[str] = None
    custom_script_id: Optional[str] = None
    script_type: Optional[str] = None
    input_params: Optional[Dict[str, Any]] = None
    output_params: Optional[Dict[str, Any]] = None
    meta_data: Optional[Dict[str, Any]] = None
    max_retries: int
    timeout_seconds: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    created_by: Optional[str] = None


# ============================================================================
# WORKFLOW NODES RESPONSE
# ============================================================================

class WorkflowNodesResponse(BaseModel):
    """Response schema for workflow nodes list."""
    workflow_id: str
    nodes: List[NodeItem]
    count: int


# ============================================================================
# NODE FORM SCHEMA RESPONSE
# ============================================================================

class NodeFormSchemaResponse(BaseModel):
    """Response schema for node form schema."""
    node_id: str
    node_name: Optional[str] = None
    script_id: Optional[str] = None
    custom_script_id: Optional[str] = None
    script_name: Optional[str] = None
    script_type: Optional[str] = None
    form_schema: Dict[str, Any]
    output_schema: Dict[str, Any]


# ============================================================================
# UPDATE REQUEST/RESPONSE
# ============================================================================

class UpdateNodeRequest(BaseModel):
    """Request schema for updating node."""
    name: Optional[str] = Field(None, description="New name")
    description: Optional[str] = Field(None, description="New description")
    script_id: Optional[str] = Field(None, description="New global script ID")
    custom_script_id: Optional[str] = Field(None, description="New custom script ID")
    meta_data: Optional[Dict[str, Any]] = Field(None, description="New metadata")
    max_retries: Optional[int] = Field(None, ge=0, description="New max retries (>= 0)")
    timeout_seconds: Optional[int] = Field(None, gt=0, description="New timeout (> 0)")


class UpdateNodeInputParamsRequest(BaseModel):
    """Request schema for updating node input parameters."""
    input_params: Dict[str, Any] = Field(..., description="Input parameters")


class SyncInputSchemaValuesRequest(BaseModel):
    """Request schema for syncing input schema values."""
    values: Dict[str, Any] = Field(..., description="Values dictionary {param_name: value}")


class ResetInputParamsResponse(BaseModel):
    """Response schema for resetting input params."""
    success: bool


# ============================================================================
# DELETE RESPONSE
# ============================================================================

class DeleteNodeResponse(BaseModel):
    """Response schema for deleting a node."""
    success: bool
    deleted_id: str

