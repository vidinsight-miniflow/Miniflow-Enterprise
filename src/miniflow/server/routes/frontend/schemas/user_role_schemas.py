"""User role service schemas for frontend routes."""

from typing import Optional, Dict, List
from datetime import datetime
from pydantic import BaseModel, Field


# ============================================================================
# OUTPUT SCHEMAS
# ============================================================================

class UserRoleResponse(BaseModel):
    """Response schema for user role data."""
    id: str = Field(..., description="Role ID")
    name: str = Field(..., description="Role name")
    description: Optional[str] = Field(None, description="Role description")
    can_edit_workspace: bool = Field(default=False, description="Can edit workspace")
    can_delete_workspace: bool = Field(default=False, description="Can delete workspace")
    can_invite_members: bool = Field(default=False, description="Can invite members")
    can_remove_members: bool = Field(default=False, description="Can remove members")
    can_manage_api_keys: bool = Field(default=False, description="Can manage API keys")
    can_manage_credentials: bool = Field(default=False, description="Can manage credentials")
    can_manage_files: bool = Field(default=False, description="Can manage files")
    can_manage_variables: bool = Field(default=False, description="Can manage variables")
    can_manage_databases: bool = Field(default=False, description="Can manage databases")
    can_manage_custom_scripts: bool = Field(default=False, description="Can manage custom scripts")
    can_manage_workflows: bool = Field(default=False, description="Can manage workflows")
    can_execute_workflows: bool = Field(default=False, description="Can execute workflows")
    can_view_executions: bool = Field(default=False, description="Can view executions")
    can_manage_executions: bool = Field(default=False, description="Can manage executions")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    @classmethod
    def from_dict(cls, data: dict) -> "UserRoleResponse":
        """Create from service dict output."""
        standardized = data.copy()
        if "record_id" in standardized:
            standardized["id"] = standardized.pop("record_id")
        if "id" not in standardized and "role_id" in standardized:
            standardized["id"] = standardized.pop("role_id")
        return cls(**standardized)


class UserRoleListResponse(BaseModel):
    """Response schema for user role list."""
    items: List["UserRoleResponse"] = Field(..., description="List of user roles")


class RolePermissionsResponse(BaseModel):
    """Response schema for role permissions."""
    role_id: str = Field(..., description="Role ID")
    permissions: Dict[str, bool] = Field(..., description="Permission dictionary")


class PermissionCheckResponse(BaseModel):
    """Response schema for permission check."""
    role_id: str = Field(..., description="Role ID")
    permission: str = Field(..., description="Permission name")
    has_permission: bool = Field(..., description="Has permission?")

