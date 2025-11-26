"""
Database request schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from src.miniflow.database.models.enums import DatabaseType


class CreateDatabaseRequest(BaseModel):
    """Request schema for creating a database connection."""
    name: str = Field(..., description="Database name", min_length=1)
    database_type: DatabaseType = Field(..., description="Database type (e.g., POSTGRESQL, MYSQL, MONGODB)")
    host: Optional[str] = Field(None, description="Database host (required if connection_string not provided)")
    port: Optional[int] = Field(None, description="Database port")
    database_name: Optional[str] = Field(None, description="Database name")
    username: Optional[str] = Field(None, description="Database username")
    password: Optional[str] = Field(None, description="Database password (will be encrypted)")
    connection_string: Optional[str] = Field(None, description="Full connection string (alternative to host/port/username/password)")
    ssl_enabled: bool = Field(False, description="Whether SSL is enabled")
    additional_params: Optional[Dict[str, Any]] = Field(None, description="Additional connection parameters")
    description: Optional[str] = Field(None, description="Optional database description")
    tags: Optional[List[str]] = Field(None, description="Optional tags")
    is_active: bool = Field(True, description="Whether the database connection is active")


class UpdateDatabaseRequest(BaseModel):
    """Request schema for updating a database connection."""
    name: Optional[str] = Field(None, description="Database name", min_length=1)
    host: Optional[str] = Field(None, description="Database host")
    port: Optional[int] = Field(None, description="Database port")
    database_name: Optional[str] = Field(None, description="Database name")
    username: Optional[str] = Field(None, description="Database username")
    password: Optional[str] = Field(None, description="Database password (will be encrypted)")
    connection_string: Optional[str] = Field(None, description="Full connection string")
    ssl_enabled: Optional[bool] = Field(None, description="Whether SSL is enabled")
    additional_params: Optional[Dict[str, Any]] = Field(None, description="Additional connection parameters")
    description: Optional[str] = Field(None, description="Database description")
    tags: Optional[List[str]] = Field(None, description="Tags")
    is_active: Optional[bool] = Field(None, description="Whether the database connection is active")

