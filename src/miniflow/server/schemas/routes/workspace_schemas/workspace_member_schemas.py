"""
Workspace Member route schemas.

Request and Response models for workspace member management endpoints.
"""
from typing import Optional
from pydantic import BaseModel, Field


# ============================================================================
# CHANGE USER ROLE
# ============================================================================

class ChangeUserRoleRequest(BaseModel):
    """Change user role request schema"""
    role_id: str = Field(..., description="New role ID")


# ============================================================================
# GET USER WORKSPACES / GET WORKSPACE MEMBERS / GET WORKSPACE MEMBER
# ============================================================================

# Response is dict/list from service, no specific schema needed

