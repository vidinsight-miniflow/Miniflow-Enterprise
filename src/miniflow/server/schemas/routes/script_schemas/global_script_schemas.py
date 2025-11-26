"""
Global Script request schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List


class CreateGlobalScriptRequest(BaseModel):
    """Request schema for creating a global script."""
    name: str = Field(..., description="Script name (must be unique globally)", min_length=1)
    category: str = Field(..., description="Script category", min_length=1)
    description: Optional[str] = Field(None, description="Script description")
    subcategory: Optional[str] = Field(None, description="Script subcategory")
    content: str = Field(..., description="Script content (Python code)", min_length=1)
    script_metadata: Optional[Dict[str, Any]] = Field(None, description="Optional script metadata")
    required_packages: Optional[List[str]] = Field(None, description="Required Python packages")
    input_schema: Optional[Dict[str, Any]] = Field(None, description="Input validation schema")
    output_schema: Optional[Dict[str, Any]] = Field(None, description="Output validation schema")
    tags: Optional[List[str]] = Field(None, description="Optional tags")
    documentation_url: Optional[str] = Field(None, description="Documentation URL")


class UpdateGlobalScriptRequest(BaseModel):
    """Request schema for updating a global script."""
    description: Optional[str] = Field(None, description="Script description")
    tags: Optional[List[str]] = Field(None, description="Tags")
    documentation_url: Optional[str] = Field(None, description="Documentation URL")

