"""
Variable request schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional


class CreateVariableRequest(BaseModel):
    """Request schema for creating a variable."""
    key: str = Field(..., description="Variable key", min_length=1)
    value: str = Field(..., description="Variable value")
    description: Optional[str] = Field(None, description="Optional variable description")
    is_secret: bool = Field(False, description="Whether the variable is secret (encrypted)")


class UpdateVariableRequest(BaseModel):
    """Request schema for updating a variable."""
    key: Optional[str] = Field(None, description="Variable key", min_length=1)
    value: Optional[str] = Field(None, description="Variable value")
    description: Optional[str] = Field(None, description="Variable description")
    is_secret: Optional[bool] = Field(None, description="Whether the variable is secret (encrypted)")

