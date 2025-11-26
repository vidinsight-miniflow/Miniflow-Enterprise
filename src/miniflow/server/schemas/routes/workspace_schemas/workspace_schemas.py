"""
Workspace route schemas.

Request and Response models for workspace management endpoints.
"""
from typing import Optional
from pydantic import BaseModel, Field


# ============================================================================
# CREATE WORKSPACE
# ============================================================================

class CreateWorkspaceRequest(BaseModel):
    """Create workspace request schema"""
    name: str = Field(..., min_length=1, max_length=100, description="Workspace name")
    slug: str = Field(..., min_length=1, max_length=100, description="Workspace slug (URL-friendly identifier)")
    description: Optional[str] = Field(None, max_length=500, description="Workspace description")


# ============================================================================
# UPDATE WORKSPACE
# ============================================================================

class UpdateWorkspaceRequest(BaseModel):
    """Update workspace request schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Workspace name")
    slug: Optional[str] = Field(None, min_length=1, max_length=100, description="Workspace slug")
    description: Optional[str] = Field(None, max_length=500, description="Workspace description")


# ============================================================================
# GET WORKSPACE DETAILS / LIMITS
# ============================================================================

# Response is dict from service, no specific schema needed

