"""
Node request schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class CreateNodeRequest(BaseModel):
    """Request schema for creating a node."""
    name: str = Field(..., description="Node name (must be unique in workflow)", min_length=1)
    script_id: Optional[str] = Field(None, description="Global script ID (either script_id or custom_script_id must be provided)")
    custom_script_id: Optional[str] = Field(None, description="Custom script ID (either script_id or custom_script_id must be provided)")
    description: Optional[str] = Field(None, description="Node description")
    input_params: Optional[Dict[str, Any]] = Field(None, description="Input parameters (frontend format, will be validated against script's input_schema)")
    output_params: Optional[Dict[str, Any]] = Field(None, description="Output parameters")
    meta_data: Optional[Dict[str, Any]] = Field(None, description="Metadata")
    max_retries: int = Field(3, ge=0, description="Maximum retry attempts (default: 3, min: 0)")
    timeout_seconds: int = Field(300, gt=0, description="Timeout in seconds (default: 300, min: 1)")


class UpdateNodeRequest(BaseModel):
    """Request schema for updating a node."""
    name: Optional[str] = Field(None, description="Node name (must be unique in workflow if changed)", min_length=1)
    description: Optional[str] = Field(None, description="Node description")
    script_id: Optional[str] = Field(None, description="Global script ID")
    custom_script_id: Optional[str] = Field(None, description="Custom script ID")
    input_params: Optional[Dict[str, Any]] = Field(None, description="Input parameters (frontend format)")
    output_params: Optional[Dict[str, Any]] = Field(None, description="Output parameters")
    meta_data: Optional[Dict[str, Any]] = Field(None, description="Metadata")
    max_retries: Optional[int] = Field(None, ge=0, description="Maximum retry attempts (min: 0)")
    timeout_seconds: Optional[int] = Field(None, gt=0, description="Timeout in seconds (min: 1)")


class UpdateNodeInputParamsRequest(BaseModel):
    """Request schema for updating only input parameters of a node."""
    input_params: Dict[str, Any] = Field(..., description="Input parameters (frontend format, will be validated against script's input_schema)")

