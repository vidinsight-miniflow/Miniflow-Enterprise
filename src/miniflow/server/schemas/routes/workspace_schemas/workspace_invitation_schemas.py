"""
Workspace invitation request schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional


class InviteUserToWorkspaceRequest(BaseModel):
    """Request schema for inviting a user to a workspace."""
    user_id: str = Field(..., description="User ID to invite")
    role_id: str = Field(..., description="Role ID for the invitation")
    message: Optional[str] = Field(None, description="Optional invitation message")

