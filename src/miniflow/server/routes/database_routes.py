"""
Database connection management routes.

Handles database connection creation, retrieval, update, and deletion for workspaces.
Database passwords are automatically encrypted at rest.
"""
from fastapi import APIRouter, Depends, Request, status, Path, Query
from typing import Dict, Any, Optional

from src.miniflow.server.dependencies import get_database_service
from src.miniflow.services import DatabaseService
from src.miniflow.server.helpers import (
    validate_workspace_member,
    authenticate_user,
    AuthUser,
)
from src.miniflow.server.schemas.base_schema import create_success_response
from src.miniflow.server.schemas.routes.resource_schemas.database_schemas import (
    CreateDatabaseRequest,
    UpdateDatabaseRequest,
)

router = APIRouter(prefix="/workspaces", tags=["databases"])


# ============================================================================
# GET ALL DATABASES
# ============================================================================

@router.get(
    "/{workspace_id}/databases",
    summary="Get all databases",
    description="Get all database connections for a workspace with pagination",
    status_code=status.HTTP_200_OK,
)
async def get_all_databases(
    request: Request,
    workspace_id: str = Depends(validate_workspace_member),
    page: int = Query(1, ge=1, description="Page number (starts from 1)"),
    page_size: int = Query(100, ge=1, le=1000, description="Number of items per page (1-1000)"),
    order_by: Optional[str] = Query(None, description="Field to order by (default: created_at)"),
    order_desc: bool = Query(False, description="Order descending (default: False)"),
    include_deleted: bool = Query(False, description="Include deleted databases"),
    database_service: DatabaseService = Depends(get_database_service),
) -> Dict[str, Any]:
    """
    Get all database connections for a workspace with pagination.
    
    - **workspace_id**: Workspace ID (path parameter)
    - **page**: Page number (query parameter, default: 1, min: 1)
    - **page_size**: Number of items per page (query parameter, default: 100, min: 1, max: 1000)
    - **order_by**: Field to order by (query parameter, optional, default: created_at)
    - **order_desc**: Order descending (query parameter, default: False)
    - **include_deleted**: Include deleted databases (query parameter, default: False)
    
    Requires workspace membership.
    Returns paginated list of database connections. Passwords are automatically decrypted.
    """
    result = database_service.get_all_databases_with_pagination(
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
        message="Databases retrieved successfully",
        code=status.HTTP_200_OK,
    ).model_dump()


# ============================================================================
# GET DATABASE
# ============================================================================

@router.get(
    "/{workspace_id}/databases/{database_id}",
    summary="Get database",
    description="Get detailed information about a specific database connection",
    status_code=status.HTTP_200_OK,
)
async def get_database(
    request: Request,
    workspace_id: str = Depends(validate_workspace_member),
    database_id: str = Path(..., description="Database ID"),
    database_service: DatabaseService = Depends(get_database_service),
) -> Dict[str, Any]:
    """
    Get detailed information about a specific database connection.
    
    - **workspace_id**: Workspace ID (path parameter)
    - **database_id**: Database ID (path parameter)
    
    Requires workspace membership.
    Returns database connection information. Password is automatically decrypted.
    """
    result = database_service.get_database(
        database_id=database_id,
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="Database retrieved successfully",
        code=status.HTTP_200_OK,
    ).model_dump()


# ============================================================================
# CREATE DATABASE
# ============================================================================

@router.post(
    "/{workspace_id}/databases",
    summary="Create database connection",
    description="Create a new database connection for a workspace",
    status_code=status.HTTP_201_CREATED,
)
async def create_database(
    request: Request,
    workspace_id: str = Depends(validate_workspace_member),
    body: CreateDatabaseRequest = ...,
    current_user: AuthUser = Depends(authenticate_user),
    database_service: DatabaseService = Depends(get_database_service),
) -> Dict[str, Any]:
    """
    Create a new database connection for a workspace.
    
    - **workspace_id**: Workspace ID (path parameter)
    - **name**: Database name (request body, required, must be unique in workspace)
    - **database_type**: Database type (request body, required)
        - Supported types: POSTGRESQL, MYSQL, MONGODB, REDIS, MSSQL, ORACLE, SQLITE, CASSANDRA, ELASTICSEARCH, DYNAMODB, BIGQUERY, SNOWFLAKE, REDSHIFT
    - **host**: Database host (request body, optional, required if connection_string not provided)
    - **port**: Database port (request body, optional)
    - **database_name**: Database name (request body, optional)
    - **username**: Database username (request body, optional)
    - **password**: Database password (request body, optional, will be encrypted)
    - **connection_string**: Full connection string (request body, optional, alternative to host/port/username/password)
    - **ssl_enabled**: Whether SSL is enabled (request body, optional, default: False)
    - **additional_params**: Additional connection parameters (request body, optional)
    - **description**: Optional description (request body, optional)
    - **tags**: Optional tags (request body, optional)
    - **is_active**: Whether the connection is active (request body, optional, default: True)
    
    Requires workspace membership.
    Either connection_string or host must be provided.
    The authenticated user will be recorded as the owner.
    Password is automatically encrypted.
    """
    result = database_service.create_database(
        workspace_id=workspace_id,
        owner_id=current_user["user_id"],
        name=body.name,
        database_type=body.database_type,
        host=body.host,
        port=body.port,
        database_name=body.database_name,
        username=body.username,
        password=body.password,
        connection_string=body.connection_string,
        ssl_enabled=body.ssl_enabled,
        additional_params=body.additional_params,
        description=body.description,
        tags=body.tags,
        is_active=body.is_active,
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="Database connection created successfully",
        code=status.HTTP_201_CREATED,
    ).model_dump()


# ============================================================================
# UPDATE DATABASE
# ============================================================================

@router.put(
    "/{workspace_id}/databases/{database_id}",
    summary="Update database connection",
    description="Update an existing database connection",
    status_code=status.HTTP_200_OK,
)
async def update_database(
    request: Request,
    workspace_id: str = Depends(validate_workspace_member),
    database_id: str = Path(..., description="Database ID"),
    body: UpdateDatabaseRequest = ...,
    current_user: AuthUser = Depends(authenticate_user),
    database_service: DatabaseService = Depends(get_database_service),
) -> Dict[str, Any]:
    """
    Update an existing database connection.
    
    - **workspace_id**: Workspace ID (path parameter)
    - **database_id**: Database ID (path parameter)
    - **name**: Database name (request body, optional, must be unique in workspace if changed)
    - **host**: Database host (request body, optional)
    - **port**: Database port (request body, optional)
    - **database_name**: Database name (request body, optional)
    - **username**: Database username (request body, optional)
    - **password**: Database password (request body, optional, will be encrypted)
    - **connection_string**: Full connection string (request body, optional)
    - **ssl_enabled**: Whether SSL is enabled (request body, optional)
    - **additional_params**: Additional connection parameters (request body, optional)
    - **description**: Database description (request body, optional)
    - **tags**: Tags (request body, optional)
    - **is_active**: Whether the connection is active (request body, optional)
    
    Requires workspace membership.
    The authenticated user will be recorded as the updater.
    Password is automatically encrypted.
    """
    result = database_service.update_database(
        database_id=database_id,
        name=body.name,
        host=body.host,
        port=body.port,
        database_name=body.database_name,
        username=body.username,
        password=body.password,
        connection_string=body.connection_string,
        ssl_enabled=body.ssl_enabled,
        additional_params=body.additional_params,
        description=body.description,
        tags=body.tags,
        is_active=body.is_active,
        updated_by=current_user["user_id"],
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="Database connection updated successfully",
        code=status.HTTP_200_OK,
    ).model_dump()


# ============================================================================
# DELETE DATABASE
# ============================================================================

@router.delete(
    "/{workspace_id}/databases/{database_id}",
    summary="Delete database connection",
    description="Delete a database connection",
    status_code=status.HTTP_200_OK,
)
async def delete_database(
    request: Request,
    workspace_id: str = Depends(validate_workspace_member),
    database_id: str = Path(..., description="Database ID"),
    database_service: DatabaseService = Depends(get_database_service),
) -> Dict[str, Any]:
    """
    Delete a database connection.
    
    - **workspace_id**: Workspace ID (path parameter)
    - **database_id**: Database ID (path parameter)
    
    Requires workspace membership.
    Permanently deletes the database connection.
    """
    result = database_service.delete_database(
        database_id=database_id,
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="Database connection deleted successfully",
        code=status.HTTP_200_OK,
    ).model_dump()

