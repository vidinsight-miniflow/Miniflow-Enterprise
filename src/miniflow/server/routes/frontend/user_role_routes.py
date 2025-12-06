"""User role routes for frontend."""

from fastapi import APIRouter, Request, Depends, Query

from miniflow.server.dependencies import (
    get_user_role_service,
    authenticate_user,
)
from miniflow.server.dependencies.auth import AuthenticatedUser
from miniflow.server.schemas.base_schemas import create_success_response
from .schemas.user_role_schemas import (
    UserRoleResponse,
    UserRoleListResponse,
    RolePermissionsResponse,
    PermissionCheckResponse,
)

router = APIRouter(prefix="/user-roles", tags=["User Roles"])


def _standardize_role_dict(data: dict) -> dict:
    """Standardize role dict: record_id -> id."""
    standardized = data.copy()
    if "record_id" in standardized:
        standardized["id"] = standardized.pop("record_id")
    if "id" not in standardized and "role_id" in standardized:
        standardized["id"] = standardized.pop("role_id")
    return standardized


@router.get("", response_model_exclude_none=True)
async def get_all_user_roles(
    request: Request,
    service = Depends(get_user_role_service),
    current_user: AuthenticatedUser = Depends(authenticate_user),
) -> dict:
    """
    Get all user roles.
    
    Requires: User authentication
    """
    roles = service.get_all_user_roles()
    standardized = [_standardize_role_dict(role) for role in roles]
    response_data = UserRoleListResponse(items=[UserRoleResponse.from_dict(role) for role in standardized])
    return create_success_response(request, data=response_data.model_dump())


@router.get("/{role_id}", response_model_exclude_none=True)
async def get_user_role_by_id(
    request: Request,
    role_id: str,
    service = Depends(get_user_role_service),
    current_user: AuthenticatedUser = Depends(authenticate_user),
) -> dict:
    """
    Get user role by ID.
    
    Requires: User authentication
    """
    role = service.get_user_role_by_id(role_id=role_id)
    standardized = _standardize_role_dict(role)
    response_data = UserRoleResponse.from_dict(standardized)
    return create_success_response(request, data=response_data.model_dump())


@router.get("/name/{role_name}", response_model_exclude_none=True)
async def get_user_role_by_name(
    request: Request,
    role_name: str,
    service = Depends(get_user_role_service),
    current_user: AuthenticatedUser = Depends(authenticate_user),
) -> dict:
    """
    Get user role by name.
    
    Requires: User authentication
    """
    role = service.get_user_role_by_name(role_name=role_name)
    standardized = _standardize_role_dict(role)
    response_data = UserRoleResponse.from_dict(standardized)
    return create_success_response(request, data=response_data.model_dump())


@router.get("/{role_id}/permissions", response_model_exclude_none=True)
async def get_role_permissions(
    request: Request,
    role_id: str,
    service = Depends(get_user_role_service),
    current_user: AuthenticatedUser = Depends(authenticate_user),
) -> dict:
    """
    Get all permissions for a role.
    
    Requires: User authentication
    """
    permissions = service.get_role_permissions(role_id=role_id)
    response_data = RolePermissionsResponse(role_id=role_id, permissions=permissions)
    return create_success_response(request, data=response_data.model_dump())


@router.get("/{role_id}/check-permission", response_model_exclude_none=True)
async def check_permission(
    request: Request,
    role_id: str,
    permission: str = Query(..., description="Permission name (e.g., 'can_edit_workspace')"),
    service = Depends(get_user_role_service),
    current_user: AuthenticatedUser = Depends(authenticate_user),
) -> dict:
    """
    Check if a role has a specific permission.
    
    Requires: User authentication
    """
    has_permission = service.check_permission(role_id=role_id, permission=permission)
    response_data = PermissionCheckResponse(
        role_id=role_id,
        permission=permission,
        has_permission=has_permission
    )
    return create_success_response(request, data=response_data.model_dump())

