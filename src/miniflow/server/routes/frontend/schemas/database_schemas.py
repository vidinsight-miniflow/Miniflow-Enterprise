"""Database service schemas for frontend routes."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# ============================================================================
# CREATE DATABASE SCHEMAS
# ============================================================================

class CreateDatabaseRequest(BaseModel):
    """Request schema for creating database connection."""
    name: str = Field(..., min_length=1, description="Database connection name (unique within workspace)")
    database_type: str = Field(..., description="Database type (POSTGRESQL, MYSQL, MONGODB, REDIS, etc.)")
    host: Optional[str] = Field(None, description="Server host address")
    port: Optional[int] = Field(None, ge=1, le=65535, description="Port number")
    database_name: Optional[str] = Field(None, description="Database name")
    username: Optional[str] = Field(None, description="Username")
    password: Optional[str] = Field(None, description="Password (will be encrypted)")
    connection_string: Optional[str] = Field(None, description="Connection string (alternative to host)")
    ssl_enabled: bool = Field(default=False, description="Enable SSL?")
    additional_params: Optional[Dict[str, Any]] = Field(None, description="Additional connection parameters")
    description: Optional[str] = Field(None, max_length=500, description="Description")
    tags: Optional[List[str]] = Field(None, description="Tags")


class CreateDatabaseResponse(BaseModel):
    """Response schema for creating database."""
    id: str = Field(..., description="Database ID")


# ============================================================================
# DATABASE DETAILS SCHEMAS
# ============================================================================

class DatabaseItem(BaseModel):
    """Schema for a single database in list."""
    id: str = Field(..., description="Database ID")
    name: str = Field(..., description="Database name")
    database_type: Optional[str] = Field(None, description="Database type")
    host: Optional[str] = Field(None, description="Host address")
    port: Optional[int] = Field(None, description="Port number")
    database_name: Optional[str] = Field(None, description="Database name")
    description: Optional[str] = Field(None, description="Description")
    tags: Optional[List[str]] = Field(None, description="Tags")
    is_active: bool = Field(True, description="Is database connection active?")
    last_tested_at: Optional[str] = Field(None, description="Last test timestamp (ISO format)")
    last_test_status: Optional[str] = Field(None, description="Last test status")


class DatabaseResponse(BaseModel):
    """Response schema for database details."""
    id: str = Field(..., description="Database ID")
    workspace_id: str = Field(..., description="Workspace ID")
    owner_id: str = Field(..., description="Owner user ID")
    name: str = Field(..., description="Database name")
    database_type: Optional[str] = Field(None, description="Database type")
    host: Optional[str] = Field(None, description="Host address")
    port: Optional[int] = Field(None, description="Port number")
    database_name: Optional[str] = Field(None, description="Database name")
    username: Optional[str] = Field(None, description="Username")
    password: Optional[str] = Field(None, description="Password (masked if include_password=False)")
    connection_string: Optional[str] = Field(None, description="Connection string")
    ssl_enabled: bool = Field(False, description="Is SSL enabled?")
    additional_params: Optional[Dict[str, Any]] = Field(None, description="Additional parameters")
    description: Optional[str] = Field(None, description="Description")
    tags: Optional[List[str]] = Field(None, description="Tags")
    is_active: bool = Field(True, description="Is database connection active?")
    last_tested_at: Optional[str] = Field(None, description="Last test timestamp (ISO format)")
    last_test_status: Optional[str] = Field(None, description="Last test status")
    created_at: Optional[str] = Field(None, description="Creation timestamp (ISO format)")


class WorkspaceDatabasesResponse(BaseModel):
    """Response schema for workspace databases list."""
    workspace_id: str = Field(..., description="Workspace ID")
    databases: List[DatabaseItem] = Field(..., description="List of databases")
    count: int = Field(..., description="Total database count")


# ============================================================================
# UPDATE DATABASE SCHEMAS
# ============================================================================

class UpdateDatabaseRequest(BaseModel):
    """Request schema for updating database."""
    name: Optional[str] = Field(None, min_length=1, description="New database name")
    host: Optional[str] = Field(None, description="New host address")
    port: Optional[int] = Field(None, ge=1, le=65535, description="New port number")
    database_name: Optional[str] = Field(None, description="New database name")
    username: Optional[str] = Field(None, description="New username")
    password: Optional[str] = Field(None, description="New password (will be encrypted)")
    connection_string: Optional[str] = Field(None, description="New connection string")
    ssl_enabled: Optional[bool] = Field(None, description="Enable SSL?")
    additional_params: Optional[Dict[str, Any]] = Field(None, description="New additional parameters")
    description: Optional[str] = Field(None, max_length=500, description="New description")
    tags: Optional[List[str]] = Field(None, description="New tags")


# ============================================================================
# TEST CONNECTION SCHEMAS
# ============================================================================

class UpdateTestStatusRequest(BaseModel):
    """Request schema for updating test status."""
    status: str = Field(..., description="Test status (SUCCESS, FAILED)")


class UpdateTestStatusResponse(BaseModel):
    """Response schema for updating test status."""
    success: bool = Field(..., description="Success status")
    status: str = Field(..., description="Test status")


# ============================================================================
# ACTIVATE/DEACTIVATE DATABASE SCHEMAS
# ============================================================================

class ActivateDatabaseResponse(BaseModel):
    """Response schema for activating database."""
    success: bool = Field(..., description="Success status")
    is_active: bool = Field(True, description="Is database connection active?")


class DeactivateDatabaseResponse(BaseModel):
    """Response schema for deactivating database."""
    success: bool = Field(..., description="Success status")
    is_active: bool = Field(False, description="Is database connection active?")


# ============================================================================
# DELETE DATABASE SCHEMAS
# ============================================================================

class DeleteDatabaseResponse(BaseModel):
    """Response schema for deleting database."""
    success: bool = Field(..., description="Success status")
    deleted_id: str = Field(..., description="Deleted database ID")

