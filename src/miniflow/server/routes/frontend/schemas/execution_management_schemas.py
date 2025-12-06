"""Execution management schemas for frontend."""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


# ============================================================================
# START EXECUTION REQUEST/RESPONSE
# ============================================================================

class StartExecutionByWorkflowRequest(BaseModel):
    """Request schema for starting execution by workflow (test)."""
    input_data: Optional[Dict[str, Any]] = Field(None, description="Test input data")


class StartExecutionResponse(BaseModel):
    """Response schema for starting execution."""
    id: str = Field(..., description="Execution ID")
    started_at: Optional[str] = None
    execution_inputs_count: int = Field(..., description="Number of execution inputs created")


# ============================================================================
# EXECUTION ITEM (for lists)
# ============================================================================

class ExecutionItem(BaseModel):
    """Schema for execution item in lists."""
    id: str
    workflow_id: Optional[str] = None
    trigger_id: Optional[str] = None
    status: Optional[str] = None
    started_at: Optional[str] = None
    ended_at: Optional[str] = None
    duration: Optional[float] = None


# ============================================================================
# EXECUTION RESPONSE
# ============================================================================

class ExecutionResponse(BaseModel):
    """Response schema for execution details."""
    id: str
    workspace_id: str
    workflow_id: str
    trigger_id: Optional[str] = None
    status: Optional[str] = None
    started_at: Optional[str] = None
    ended_at: Optional[str] = None
    duration: Optional[float] = None
    trigger_data: Dict[str, Any]
    results: Dict[str, Any]
    retry_count: int
    max_retries: int
    is_retry: bool
    triggered_by: Optional[str] = None
    created_at: Optional[str] = None


# ============================================================================
# WORKSPACE EXECUTIONS RESPONSE
# ============================================================================

class WorkspaceExecutionsResponse(BaseModel):
    """Response schema for workspace executions list."""
    workspace_id: str
    executions: List[ExecutionItem]
    count: int


# ============================================================================
# WORKFLOW EXECUTIONS RESPONSE
# ============================================================================

class WorkflowExecutionsResponse(BaseModel):
    """Response schema for workflow executions list."""
    workflow_id: str
    executions: List[ExecutionItem]
    count: int


# ============================================================================
# EXECUTION STATS RESPONSE
# ============================================================================

class ExecutionStatsResponse(BaseModel):
    """Response schema for execution statistics."""
    workspace_id: str
    total: int
    pending: int
    running: int
    completed: int
    failed: int
    cancelled: int

