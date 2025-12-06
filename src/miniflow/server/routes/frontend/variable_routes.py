"""Variable routes for frontend."""

from fastapi import APIRouter, Request, Depends, Path, Query

from miniflow.server.dependencies import (
    get_variable_service,
    authenticate_user,
    require_workspace_access,
)
from miniflow.server.dependencies.auth import AuthenticatedUser
from miniflow.server.schemas.base_schemas import create_success_response
from .schemas.variable_schemas import (
    CreateVariableRequest,
    CreateVariableResponse,
    VariableResponse,
    WorkspaceVariablesResponse,
    UpdateVariableRequest,
    DeleteVariableResponse,
)

router = APIRouter(prefix="/workspaces", tags=["Variables"])


# ============================================================================
# CREATE VARIABLE ENDPOINTS
# ============================================================================

@router.post("/{workspace_id}/variables", response_model_exclude_none=True)
async def create_variable(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    variable_data: CreateVariableRequest = ...,
    service = Depends(get_variable_service),
    current_user: AuthenticatedUser = Depends(authenticate_user),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Create a new environment variable.
    
    Requires: Workspace access
    Note: Secret variables will be encrypted automatically.
    """
    result = service.create_variable(
        workspace_id=workspace_id,
        owner_id=current_user["user_id"],
        key=variable_data.key,
        value=variable_data.value,
        description=variable_data.description,
        is_secret=variable_data.is_secret
    )
    
    response_data = CreateVariableResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Variable created successfully."
    )


# ============================================================================
# GET VARIABLE ENDPOINTS
# ============================================================================

@router.get("/{workspace_id}/variables/{variable_id}", response_model_exclude_none=True)
async def get_variable(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    variable_id: str = Path(..., description="Variable ID"),
    decrypt_secret: bool = Query(default=False, description="Decrypt secret value"),
    service = Depends(get_variable_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Get variable details.
    
    Requires: Workspace access
    Note: Secret values are masked by default. Set decrypt_secret=True to get actual value.
    """
    result = service.get_variable(
        variable_id=variable_id,
        decrypt_secret=decrypt_secret
    )
    
    response_data = VariableResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump()
    )


@router.get("/{workspace_id}/variables/key/{key}", response_model_exclude_none=True)
async def get_variable_by_key(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    key: str = Path(..., description="Variable key"),
    decrypt_secret: bool = Query(default=False, description="Decrypt secret value"),
    service = Depends(get_variable_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Get variable by key.
    
    Requires: Workspace access
    """
    result = service.get_variable_by_key(
        workspace_id=workspace_id,
        key=key,
        decrypt_secret=decrypt_secret
    )
    
    response_data = VariableResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump()
    )


@router.get("/{workspace_id}/variables", response_model_exclude_none=True)
async def get_workspace_variables(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    service = Depends(get_variable_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Get all workspace variables.
    
    Requires: Workspace access
    Note: Secret values are automatically masked.
    """
    result = service.get_workspace_variables(
        workspace_id=workspace_id
    )
    
    response_data = WorkspaceVariablesResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump()
    )


# ============================================================================
# UPDATE VARIABLE ENDPOINTS
# ============================================================================

@router.put("/{workspace_id}/variables/{variable_id}", response_model_exclude_none=True)
async def update_variable(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    variable_id: str = Path(..., description="Variable ID"),
    variable_data: UpdateVariableRequest = ...,
    service = Depends(get_variable_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Update variable.
    
    Requires: Workspace access
    Note: Changing is_secret will re-encrypt/decrypt the value automatically.
    """
    result = service.update_variable(
        variable_id=variable_id,
        key=variable_data.key,
        value=variable_data.value,
        description=variable_data.description,
        is_secret=variable_data.is_secret
    )
    
    response_data = VariableResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Variable updated successfully."
    )


# ============================================================================
# DELETE VARIABLE ENDPOINTS
# ============================================================================

@router.delete("/{workspace_id}/variables/{variable_id}", response_model_exclude_none=True)
async def delete_variable(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    variable_id: str = Path(..., description="Variable ID"),
    service = Depends(get_variable_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Delete variable.
    
    Requires: Workspace access
    """
    result = service.delete_variable(
        variable_id=variable_id
    )
    
    response_data = DeleteVariableResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Variable deleted successfully."
    )

