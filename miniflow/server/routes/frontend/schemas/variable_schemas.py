"""Variable service schemas for frontend routes."""

from typing import Optional, List
from pydantic import BaseModel, Field


# ============================================================================
# CREATE VARIABLE SCHEMAS
# ============================================================================

class CreateVariableRequest(BaseModel):
    """Request schema for creating variable."""
    key: str = Field(..., min_length=1, description="Variable key (unique within workspace)")
    value: str = Field(..., description="Variable value")
    description: Optional[str] = Field(None, max_length=500, description="Variable description")
    is_secret: bool = Field(default=False, description="Is this a secret variable? (will be encrypted)")


class CreateVariableResponse(BaseModel):
    """Response schema for creating variable."""
    id: str = Field(..., description="Variable ID")


# ============================================================================
# VARIABLE DETAILS SCHEMAS
# ============================================================================

class VariableItem(BaseModel):
    """Schema for a single variable in list."""
    id: str = Field(..., description="Variable ID")
    key: str = Field(..., description="Variable key")
    value: str = Field(..., description="Variable value (masked if secret)")
    description: Optional[str] = Field(None, description="Variable description")
    is_secret: bool = Field(False, description="Is this a secret variable?")
    created_at: Optional[str] = Field(None, description="Creation timestamp (ISO format)")


class VariableResponse(BaseModel):
    """Response schema for variable details."""
    id: str = Field(..., description="Variable ID")
    workspace_id: str = Field(..., description="Workspace ID")
    owner_id: str = Field(..., description="Owner user ID")
    key: str = Field(..., description="Variable key")
    value: str = Field(..., description="Variable value (decrypted if secret and decrypt_secret=True)")
    description: Optional[str] = Field(None, description="Variable description")
    is_secret: bool = Field(False, description="Is this a secret variable?")
    created_at: Optional[str] = Field(None, description="Creation timestamp (ISO format)")


class WorkspaceVariablesResponse(BaseModel):
    """Response schema for workspace variables list."""
    workspace_id: str = Field(..., description="Workspace ID")
    variables: List[VariableItem] = Field(..., description="List of variables")
    count: int = Field(..., description="Total variable count")


# ============================================================================
# UPDATE VARIABLE SCHEMAS
# ============================================================================

class UpdateVariableRequest(BaseModel):
    """Request schema for updating variable."""
    key: Optional[str] = Field(None, min_length=1, description="New variable key")
    value: Optional[str] = Field(None, description="New variable value")
    description: Optional[str] = Field(None, max_length=500, description="New description")
    is_secret: Optional[bool] = Field(None, description="New secret status")


# ============================================================================
# DELETE VARIABLE SCHEMAS
# ============================================================================

class DeleteVariableResponse(BaseModel):
    """Response schema for deleting variable."""
    success: bool = Field(..., description="Success status")
    deleted_id: str = Field(..., description="Deleted variable ID")

