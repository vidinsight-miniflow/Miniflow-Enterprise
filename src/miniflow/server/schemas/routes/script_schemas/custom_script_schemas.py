"""
Custom Script request schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from src.miniflow.database.models.enums import ScriptApprovalStatus, ScriptTestStatus


class CreateCustomScriptRequest(BaseModel):
    """Request schema for creating a custom script."""
    name: str = Field(..., description="Script name (must be unique in workspace)", min_length=1)
    content: str = Field(..., description="Script content (Python code)", min_length=1)
    description: Optional[str] = Field(None, description="Script description")
    category: Optional[str] = Field(None, description="Script category")
    subcategory: Optional[str] = Field(None, description="Script subcategory")
    required_packages: Optional[List[str]] = Field(None, description="Required Python packages")
    input_schema: Optional[Dict[str, Any]] = Field(None, description="Input validation schema")
    output_schema: Optional[Dict[str, Any]] = Field(None, description="Output validation schema")
    tags: Optional[List[str]] = Field(None, description="Optional tags")
    documentation_url: Optional[str] = Field(None, description="Documentation URL")


class UpdateCustomScriptRequest(BaseModel):
    """Request schema for updating a custom script."""
    description: Optional[str] = Field(None, description="Script description")
    tags: Optional[List[str]] = Field(None, description="Tags")
    documentation_url: Optional[str] = Field(None, description="Documentation URL")

