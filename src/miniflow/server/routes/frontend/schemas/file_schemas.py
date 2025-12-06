"""File service schemas for frontend routes."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# ============================================================================
# UPLOAD FILE SCHEMAS
# ============================================================================

class UploadFileResponse(BaseModel):
    """Response schema for uploading file."""
    id: str = Field(..., description="File ID")


# ============================================================================
# FILE DETAILS SCHEMAS
# ============================================================================

class FileItem(BaseModel):
    """Schema for a single file in list."""
    id: str = Field(..., description="File ID")
    name: str = Field(..., description="File name")
    original_filename: Optional[str] = Field(None, description="Original filename")
    file_size: int = Field(..., description="File size in bytes")
    file_size_mb: float = Field(..., description="File size in MB")
    mime_type: Optional[str] = Field(None, description="MIME type")
    file_extension: Optional[str] = Field(None, description="File extension")
    description: Optional[str] = Field(None, description="Description")
    tags: Optional[List[str]] = Field(None, description="Tags")
    created_at: Optional[str] = Field(None, description="Creation timestamp (ISO format)")


class FileResponse(BaseModel):
    """Response schema for file details."""
    id: str = Field(..., description="File ID")
    workspace_id: str = Field(..., description="Workspace ID")
    owner_id: str = Field(..., description="Owner user ID")
    name: str = Field(..., description="File name")
    original_filename: Optional[str] = Field(None, description="Original filename")
    file_size: int = Field(..., description="File size in bytes")
    file_size_mb: float = Field(..., description="File size in MB")
    mime_type: Optional[str] = Field(None, description="MIME type")
    file_extension: Optional[str] = Field(None, description="File extension")
    description: Optional[str] = Field(None, description="Description")
    tags: Optional[List[str]] = Field(None, description="Tags")
    file_metadata: Optional[Dict[str, Any]] = Field(None, description="File metadata")
    created_at: Optional[str] = Field(None, description="Creation timestamp (ISO format)")


class WorkspaceFilesResponse(BaseModel):
    """Response schema for workspace files list."""
    workspace_id: str = Field(..., description="Workspace ID")
    files: List[FileItem] = Field(..., description="List of files")
    count: int = Field(..., description="Total file count")
    total_size_bytes: int = Field(..., description="Total size in bytes")
    total_size_mb: float = Field(..., description="Total size in MB")


# ============================================================================
# UPDATE FILE SCHEMAS
# ============================================================================

class UpdateFileRequest(BaseModel):
    """Request schema for updating file metadata."""
    name: Optional[str] = Field(None, min_length=1, description="New file name")
    description: Optional[str] = Field(None, max_length=500, description="New description")
    tags: Optional[List[str]] = Field(None, description="New tags")


# ============================================================================
# DELETE FILE SCHEMAS
# ============================================================================

class DeleteFileResponse(BaseModel):
    """Response schema for deleting file."""
    success: bool = Field(..., description="Success status")
    deleted_id: str = Field(..., description="Deleted file ID")

