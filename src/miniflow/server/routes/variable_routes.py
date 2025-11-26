"""
Variable management routes.

Handles variable creation, retrieval, update, and deletion for workspaces.
Variables can be secret (encrypted) or non-secret (plain text).
"""
from fastapi import APIRouter, Depends, Request, status, Path, Query
from typing import Dict, Any, Optional

from src.miniflow.server.dependencies import get_variable_service
from src.miniflow.services import VariableService
from src.miniflow.server.helpers import (
    validate_workspace_member,
    authenticate_user,
    AuthUser,
)
from src.miniflow.server.schemas.base_schema import create_success_response
from src.miniflow.server.schemas.routes.resource_schemas.variable_schemas import (
    CreateVariableRequest,
    UpdateVariableRequest,
)

router = APIRouter(prefix="/workspaces", tags=["variables"])


# ============================================================================
# GET ALL VARIABLES
# ============================================================================

@router.get(
    "/{workspace_id}/variables",
    summary="Get all variables",
    description="Get all variables for a workspace with pagination",
    status_code=status.HTTP_200_OK,
)
async def get_all_variables(
    request: Request,
    workspace_id: str = Depends(validate_workspace_member),
    page: int = Query(1, ge=1, description="Page number (starts from 1)"),
    page_size: int = Query(100, ge=1, le=1000, description="Number of items per page (1-1000)"),
    order_by: Optional[str] = Query(None, description="Field to order by (default: created_at)"),
    order_desc: bool = Query(False, description="Order descending (default: False)"),
    include_deleted: bool = Query(False, description="Include deleted variables"),
    variable_service: VariableService = Depends(get_variable_service),
) -> Dict[str, Any]:
    """
    Get all variables for a workspace with pagination.
    
    - **workspace_id**: Workspace ID (path parameter)
    - **page**: Page number (query parameter, default: 1, min: 1)
    - **page_size**: Number of items per page (query parameter, default: 100, min: 1, max: 1000)
    - **order_by**: Field to order by (query parameter, optional, default: created_at)
    - **order_desc**: Order descending (query parameter, default: False)
    - **include_deleted**: Include deleted variables (query parameter, default: False)
    
    Requires workspace membership.
    Returns paginated list of variables. Secret variables are automatically decrypted.
    """
    result = variable_service.get_all_variables_with_pagination(
        workspace_id=workspace_id,
        page=page,
        page_size=page_size,
        order_by=order_by,
        order_desc=order_desc,
        include_deleted=include_deleted,
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="Variables retrieved successfully",
        code=status.HTTP_200_OK,
    ).model_dump()


# ============================================================================
# GET VARIABLE
# ============================================================================

@router.get(
    "/{workspace_id}/variables/{variable_id}",
    summary="Get variable",
    description="Get detailed information about a specific variable",
    status_code=status.HTTP_200_OK,
)
async def get_variable(
    request: Request,
    workspace_id: str = Depends(validate_workspace_member),
    variable_id: str = Path(..., description="Variable ID"),
    variable_service: VariableService = Depends(get_variable_service),
) -> Dict[str, Any]:
    """
    Get detailed information about a specific variable.
    
    - **workspace_id**: Workspace ID (path parameter)
    - **variable_id**: Variable ID (path parameter)
    
    Requires workspace membership.
    Returns variable information. Secret variables are automatically decrypted.
    """
    result = variable_service.get_variable(
        variable_id=variable_id,
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="Variable retrieved successfully",
        code=status.HTTP_200_OK,
    ).model_dump()


# ============================================================================
# CREATE VARIABLE
# ============================================================================

@router.post(
    "/{workspace_id}/variables",
    summary="Create variable",
    description="Create a new variable for a workspace",
    status_code=status.HTTP_201_CREATED,
)
async def create_variable(
    request: Request,
    workspace_id: str = Depends(validate_workspace_member),
    body: CreateVariableRequest = ...,
    current_user: AuthUser = Depends(authenticate_user),
    variable_service: VariableService = Depends(get_variable_service),
) -> Dict[str, Any]:
    """
    Create a new variable for a workspace.
    
    - **workspace_id**: Workspace ID (path parameter)
    - **key**: Variable key (request body, required, must be unique in workspace)
    - **value**: Variable value (request body, required)
    - **description**: Optional description (request body, optional)
    - **is_secret**: Whether the variable is secret (request body, optional, default: False)
        - If True, the value will be encrypted at rest
        - If False, the value will be stored as plain text
    
    Requires workspace membership.
    The authenticated user will be recorded as the owner.
    Secret variables are automatically encrypted.
    """
    result = variable_service.create_variable(
        workspace_id=workspace_id,
        owner_id=current_user["user_id"],
        key=body.key,
        value=body.value,
        description=body.description,
        is_secret=body.is_secret,
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="Variable created successfully",
        code=status.HTTP_201_CREATED,
    ).model_dump()


# ============================================================================
# UPDATE VARIABLE
# ============================================================================

@router.put(
    "/{workspace_id}/variables/{variable_id}",
    summary="Update variable",
    description="Update an existing variable",
    status_code=status.HTTP_200_OK,
)
async def update_variable(
    request: Request,
    workspace_id: str = Depends(validate_workspace_member),
    variable_id: str = Path(..., description="Variable ID"),
    body: UpdateVariableRequest = ...,
    current_user: AuthUser = Depends(authenticate_user),
    variable_service: VariableService = Depends(get_variable_service),
) -> Dict[str, Any]:
    """
    Update an existing variable.
    
    - **workspace_id**: Workspace ID (path parameter)
    - **variable_id**: Variable ID (path parameter)
    - **key**: Variable key (request body, optional, must be unique in workspace if changed)
    - **value**: Variable value (request body, optional)
    - **description**: Variable description (request body, optional)
    - **is_secret**: Whether the variable is secret (request body, optional)
        - Changing from secret to non-secret will decrypt the value
        - Changing from non-secret to secret will encrypt the value
    
    Requires workspace membership.
    The authenticated user will be recorded as the updater.
    Secret variables are automatically encrypted/decrypted based on is_secret flag.
    """
    result = variable_service.update_variable(
        variable_id=variable_id,
        key=body.key,
        value=body.value,
        description=body.description,
        is_secret=body.is_secret,
        updated_by=current_user["user_id"],
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="Variable updated successfully",
        code=status.HTTP_200_OK,
    ).model_dump()


# ============================================================================
# DELETE VARIABLE
# ============================================================================

@router.delete(
    "/{workspace_id}/variables/{variable_id}",
    summary="Delete variable",
    description="Delete a variable",
    status_code=status.HTTP_200_OK,
)
async def delete_variable(
    request: Request,
    workspace_id: str = Depends(validate_workspace_member),
    variable_id: str = Path(..., description="Variable ID"),
    variable_service: VariableService = Depends(get_variable_service),
) -> Dict[str, Any]:
    """
    Delete a variable.
    
    - **workspace_id**: Workspace ID (path parameter)
    - **variable_id**: Variable ID (path parameter)
    
    Requires workspace membership.
    Permanently deletes the variable.
    """
    result = variable_service.delete_variable(
        variable_id=variable_id,
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="Variable deleted successfully",
        code=status.HTTP_200_OK,
    ).model_dump()

