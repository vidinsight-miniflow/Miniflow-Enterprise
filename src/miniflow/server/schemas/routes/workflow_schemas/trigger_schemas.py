"""
Trigger request schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from src.miniflow.database.models.enums import TriggerType


class CreateTriggerRequest(BaseModel):
    """Request schema for creating a trigger."""
    name: str = Field(..., description="Trigger name (must be unique in workspace)", min_length=1)
    trigger_type: TriggerType = Field(..., description="Trigger type (e.g., MANUAL, SCHEDULED, WEBHOOK, EVENT)")
    config: Dict[str, Any] = Field(..., description="Trigger configuration (JSON object)")
    description: Optional[str] = Field(None, description="Trigger description")
    input_mapping: Optional[Dict[str, Any]] = Field(None, description="Input mapping rules (format: {VARIABLE_NAME: {type: str, value: Any}})")
    is_enabled: bool = Field(True, description="Whether the trigger is enabled")


class UpdateTriggerRequest(BaseModel):
    """Request schema for updating a trigger."""
    name: Optional[str] = Field(None, description="Trigger name (must be unique in workspace if changed)", min_length=1)
    description: Optional[str] = Field(None, description="Trigger description")
    trigger_type: Optional[TriggerType] = Field(None, description="Trigger type")
    config: Optional[Dict[str, Any]] = Field(None, description="Trigger configuration (JSON object)")
    input_mapping: Optional[Dict[str, Any]] = Field(None, description="Input mapping rules")
    is_enabled: Optional[bool] = Field(None, description="Whether the trigger is enabled")

