"""
Workflow request schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from src.miniflow.database.models.enums import WorkflowStatus


class CreateWorkflowRequest(BaseModel):
    """Request schema for creating a workflow."""
    name: str = Field(..., description="Workflow name (must be unique in workspace)", min_length=1)
    description: Optional[str] = Field(None, description="Workflow description")
    priority: int = Field(1, ge=1, description="Priority level (default: 1, min: 1)")
    status: Optional[WorkflowStatus] = Field(WorkflowStatus.DRAFT, description="Workflow status (default: DRAFT)")
    status_message: Optional[str] = Field(None, description="Status message")
    tags: Optional[List[str]] = Field(None, description="Optional tags")


class UpdateWorkflowRequest(BaseModel):
    """Request schema for updating a workflow."""
    name: Optional[str] = Field(None, description="Workflow name (must be unique in workspace if changed)", min_length=1)
    description: Optional[str] = Field(None, description="Workflow description")
    priority: Optional[int] = Field(None, ge=1, description="Priority level (min: 1)")
    status: Optional[WorkflowStatus] = Field(None, description="Workflow status")
    status_message: Optional[str] = Field(None, description="Status message")
    tags: Optional[List[str]] = Field(None, description="Tags")

