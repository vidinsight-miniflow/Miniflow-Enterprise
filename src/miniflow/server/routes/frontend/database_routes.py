"""Database routes for frontend."""

from fastapi import APIRouter, Request, Depends, Path, Query

from miniflow.server.dependencies import (
    get_database_service,
    authenticate_user,
    require_workspace_access,
)
from miniflow.server.dependencies.auth import AuthenticatedUser
from miniflow.server.schemas.base_schemas import create_success_response
from miniflow.models.enums import DatabaseType
from .schemas.database_schemas import (
    CreateDatabaseRequest,
    CreateDatabaseResponse,
    DatabaseResponse,
    WorkspaceDatabasesResponse,
    UpdateDatabaseRequest,
    UpdateTestStatusRequest,
    UpdateTestStatusResponse,
    ActivateDatabaseResponse,
    DeactivateDatabaseResponse,
    DeleteDatabaseResponse,
)

router = APIRouter(prefix="/workspaces", tags=["Databases"])


# ============================================================================
# CREATE DATABASE ENDPOINTS
# ============================================================================

@router.post("/{workspace_id}/databases", response_model_exclude_none=True)
async def create_database(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    database_data: CreateDatabaseRequest = ...,
    service = Depends(get_database_service),
    current_user: AuthenticatedUser = Depends(authenticate_user),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Create a new database connection.
    
    Requires: Workspace access
    Note: Password will be encrypted automatically.
    """
    try:
        db_type = DatabaseType(database_data.database_type.upper())
    except ValueError:
        from miniflow.core.exceptions import InvalidInputError
        raise InvalidInputError(
            field_name="database_type",
            message=f"Invalid database type. Valid types: {', '.join([dt.value for dt in DatabaseType])}"
        )
    
    result = service.create_database(
        workspace_id=workspace_id,
        owner_id=current_user["user_id"],
        name=database_data.name,
        database_type=db_type,
        host=database_data.host,
        port=database_data.port,
        database_name=database_data.database_name,
        username=database_data.username,
        password=database_data.password,
        connection_string=database_data.connection_string,
        ssl_enabled=database_data.ssl_enabled,
        additional_params=database_data.additional_params,
        description=database_data.description,
        tags=database_data.tags
    )
    
    response_data = CreateDatabaseResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Database connection created successfully."
    )


# ============================================================================
# GET DATABASE ENDPOINTS
# ============================================================================

@router.get("/{workspace_id}/databases/{database_id}", response_model_exclude_none=True)
async def get_database(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    database_id: str = Path(..., description="Database ID"),
    include_password: bool = Query(default=False, description="Include password (decrypted)"),
    service = Depends(get_database_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Get database connection details.
    
    Requires: Workspace access
    Note: Password is masked by default. Set include_password=True to get actual password.
    """
    result = service.get_database(
        database_id=database_id,
        include_password=include_password
    )
    
    response_data = DatabaseResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump()
    )


@router.get("/{workspace_id}/databases", response_model_exclude_none=True)
async def get_workspace_databases(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    database_type: str = Query(None, description="Filter by database type"),
    service = Depends(get_database_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Get all workspace database connections.
    
    Requires: Workspace access
    """
    db_type = None
    if database_type:
        try:
            db_type = DatabaseType(database_type.upper())
        except ValueError:
            pass
    
    result = service.get_workspace_databases(
        workspace_id=workspace_id,
        database_type=db_type
    )
    
    response_data = WorkspaceDatabasesResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump()
    )


# ============================================================================
# UPDATE DATABASE ENDPOINTS
# ============================================================================

@router.put("/{workspace_id}/databases/{database_id}", response_model_exclude_none=True)
async def update_database(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    database_id: str = Path(..., description="Database ID"),
    database_data: UpdateDatabaseRequest = ...,
    service = Depends(get_database_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Update database connection.
    
    Requires: Workspace access
    Note: Password will be re-encrypted if provided.
    """
    result = service.update_database(
        database_id=database_id,
        name=database_data.name,
        host=database_data.host,
        port=database_data.port,
        database_name=database_data.database_name,
        username=database_data.username,
        password=database_data.password,
        connection_string=database_data.connection_string,
        ssl_enabled=database_data.ssl_enabled,
        additional_params=database_data.additional_params,
        description=database_data.description,
        tags=database_data.tags
    )
    
    response_data = DatabaseResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Database connection updated successfully."
    )


# ============================================================================
# TEST CONNECTION ENDPOINTS
# ============================================================================

@router.post("/{workspace_id}/databases/{database_id}/test-status", response_model_exclude_none=True)
async def update_test_status(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    database_id: str = Path(..., description="Database ID"),
    status_data: UpdateTestStatusRequest = ...,
    service = Depends(get_database_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Update database connection test status.
    
    Requires: Workspace access
    Note: Usually called after testing the connection.
    """
    result = service.update_test_status(
        database_id=database_id,
        status=status_data.status
    )
    
    response_data = UpdateTestStatusResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Test status updated successfully."
    )


# ============================================================================
# ACTIVATE/DEACTIVATE DATABASE ENDPOINTS
# ============================================================================

@router.post("/{workspace_id}/databases/{database_id}/activate", response_model_exclude_none=True)
async def activate_database(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    database_id: str = Path(..., description="Database ID"),
    service = Depends(get_database_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Activate database connection.
    
    Requires: Workspace access
    """
    result = service.activate_database(
        database_id=database_id
    )
    
    response_data = ActivateDatabaseResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Database connection activated successfully."
    )


@router.post("/{workspace_id}/databases/{database_id}/deactivate", response_model_exclude_none=True)
async def deactivate_database(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    database_id: str = Path(..., description="Database ID"),
    service = Depends(get_database_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Deactivate database connection.
    
    Requires: Workspace access
    """
    result = service.deactivate_database(
        database_id=database_id
    )
    
    response_data = DeactivateDatabaseResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Database connection deactivated successfully."
    )


# ============================================================================
# DELETE DATABASE ENDPOINTS
# ============================================================================

@router.delete("/{workspace_id}/databases/{database_id}", response_model_exclude_none=True)
async def delete_database(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    database_id: str = Path(..., description="Database ID"),
    service = Depends(get_database_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Delete database connection.
    
    Requires: Workspace access
    """
    result = service.delete_database(
        database_id=database_id
    )
    
    response_data = DeleteDatabaseResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Database connection deleted successfully."
    )

