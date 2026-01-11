"""Trigger schemas for frontend."""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


# ============================================================================
# CREATE REQUEST/RESPONSE
# ============================================================================

class CreateTriggerRequest(BaseModel):
    """Request schema for creating a trigger."""
    name: str = Field(..., description="Trigger name (unique within workspace)")
    trigger_type: str = Field(..., description="Trigger type (API, SCHEDULED, WEBHOOK, EVENT)")
    config: Dict[str, Any] = Field(..., description="Trigger configuration")
    description: Optional[str] = Field(None, description="Trigger description")
    input_mapping: Optional[Dict[str, Any]] = Field(None, description="Input mapping rules")
    is_enabled: bool = Field(default=True, description="Is enabled (default: True)")


class CreateTriggerResponse(BaseModel):
    """Response schema for creating a trigger."""
    id: str = Field(..., description="Trigger ID")


# ============================================================================
# TRIGGER ITEM (for lists)
# ============================================================================

class TriggerItem(BaseModel):
    """Schema for trigger item in lists."""
    id: str
    name: str
    description: Optional[str] = None
    workflow_id: Optional[str] = None
    trigger_type: Optional[str] = None
    is_enabled: bool = False


# ============================================================================
# TRIGGER RESPONSE
# ============================================================================

class TriggerResponse(BaseModel):
    """Response schema for trigger details."""
    id: str
    workspace_id: str
    workflow_id: str
    name: str
    description: Optional[str] = None
    trigger_type: Optional[str] = None
    config: Dict[str, Any]
    input_mapping: Dict[str, Any]
    is_enabled: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    created_by: Optional[str] = None


# ============================================================================
# WORKSPACE TRIGGERS RESPONSE
# ============================================================================

class WorkspaceTriggersResponse(BaseModel):
    """Response schema for workspace triggers list."""
    workspace_id: str
    triggers: List[TriggerItem]
    count: int


# ============================================================================
# WORKFLOW TRIGGERS RESPONSE
# ============================================================================

class WorkflowTriggerItem(BaseModel):
    """Schema for workflow trigger item."""
    id: str
    name: str
    description: Optional[str] = None
    trigger_type: Optional[str] = None
    config: Dict[str, Any]
    is_enabled: bool


class WorkflowTriggersResponse(BaseModel):
    """Response schema for workflow triggers list."""
    workflow_id: str
    triggers: List[WorkflowTriggerItem]
    count: int


# ============================================================================
# UPDATE REQUEST/RESPONSE
# ============================================================================

class UpdateTriggerRequest(BaseModel):
    """Request schema for updating trigger."""
    name: Optional[str] = Field(None, description="New name")
    description: Optional[str] = Field(None, description="New description")
    trigger_type: Optional[str] = Field(None, description="New trigger type")
    config: Optional[Dict[str, Any]] = Field(None, description="New configuration")
    input_mapping: Optional[Dict[str, Any]] = Field(None, description="New input mapping")


# ============================================================================
# ENABLE/DISABLE RESPONSE
# ============================================================================

class EnableTriggerResponse(BaseModel):
    """Response schema for enabling trigger."""
    success: bool
    is_enabled: bool


class DisableTriggerResponse(BaseModel):
    """Response schema for disabling trigger."""
    success: bool
    is_enabled: bool


# ============================================================================
# DELETE RESPONSE
# ============================================================================

class DeleteTriggerResponse(BaseModel):
    """Response schema for deleting a trigger."""
    success: bool
    deleted_id: str


# ============================================================================
# LIMITS RESPONSE
# ============================================================================

class TriggerLimitsResponse(BaseModel):
    """Response schema for trigger limits."""
    min_triggers_per_workflow: int
    max_triggers_per_workflow: int

