"""
File management routes.

Handles file upload, retrieval, update, and deletion for workspaces.
Files are stored in workspace-specific directories with automatic storage limit management.
"""
from fastapi import APIRouter, Depends, Request, status, Path, Query, UploadFile, File, Form, Response
from typing import Dict, Any, Optional

from src.miniflow.server.dependencies import get_file_service
from src.miniflow.services import FileService
from src.miniflow.server.helpers import (
    validate_workspace_member,
    authenticate_user,
    AuthUser,
)
from src.miniflow.server.schemas.base_schema import create_success_response
from src.miniflow.server.schemas.routes.resource_schemas.file_schemas import (
    UpdateFileRequest,
)

router = APIRouter(prefix="/workspaces", tags=["files"])


# ============================================================================
# GET ALL FILES
# ============================================================================

@router.get(
    "/{workspace_id}/files",
    summary="Get all files",
    description="Get all files for a workspace with pagination",
    status_code=status.HTTP_200_OK,
)
async def get_all_files(
    request: Request,
    workspace_id: str = Depends(validate_workspace_member),
    page: int = Query(1, ge=1, description="Page number (starts from 1)"),
    page_size: int = Query(100, ge=1, le=1000, description="Number of items per page (1-1000)"),
    order_by: Optional[str] = Query(None, description="Field to order by (default: created_at)"),
    order_desc: bool = Query(False, description="Order descending (default: False)"),
    include_deleted: bool = Query(False, description="Include deleted files"),
    file_service: FileService = Depends(get_file_service),
) -> Dict[str, Any]:
    """
    Get all files for a workspace with pagination.
    
    - **workspace_id**: Workspace ID (path parameter)
    - **page**: Page number (query parameter, default: 1, min: 1)
    - **page_size**: Number of items per page (query parameter, default: 100, min: 1, max: 1000)
    - **order_by**: Field to order by (query parameter, optional, default: created_at)
    - **order_desc**: Order descending (query parameter, default: False)
    - **include_deleted**: Include deleted files (query parameter, default: False)
    
    Requires workspace membership.
    Returns paginated list of file metadata.
    """
    result = file_service.get_all_files_with_pagination(
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
        message="Files retrieved successfully",
        code=status.HTTP_200_OK,
    ).model_dump()


# ============================================================================
# GET FILE
# ============================================================================

@router.get(
    "/{workspace_id}/files/{file_id}",
    summary="Get file metadata",
    description="Get detailed information about a specific file",
    status_code=status.HTTP_200_OK,
)
async def get_file(
    request: Request,
    workspace_id: str = Depends(validate_workspace_member),
    file_id: str = Path(..., description="File ID"),
    file_service: FileService = Depends(get_file_service),
) -> Dict[str, Any]:
    """
    Get detailed information about a specific file.
    
    - **workspace_id**: Workspace ID (path parameter)
    - **file_id**: File ID (path parameter)
    
    Requires workspace membership.
    Returns file metadata (not the file content).
    Use GET /workspaces/{workspace_id}/files/{file_id}/content to download the file.
    """
    result = file_service.get_file(
        file_id=file_id,
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="File metadata retrieved successfully",
        code=status.HTTP_200_OK,
    ).model_dump()


# ============================================================================
# GET FILE CONTENT
# ============================================================================

@router.get(
    "/{workspace_id}/files/{file_id}/content",
    summary="Download file",
    description="Download the actual file content",
    status_code=status.HTTP_200_OK,
)
async def get_file_content(
    request: Request,
    workspace_id: str = Depends(validate_workspace_member),
    file_id: str = Path(..., description="File ID"),
    file_service: FileService = Depends(get_file_service),
) -> Response:
    """
    Download the actual file content.
    
    - **workspace_id**: Workspace ID (path parameter)
    - **file_id**: File ID (path parameter)
    
    Requires workspace membership.
    Returns the file content as binary data with appropriate Content-Type header.
    """
    file_content = file_service.get_file_content(
        file_id=file_id,
    )
    
    # Get file metadata to set proper headers
    file_metadata = file_service.get_file(file_id=file_id)
    
    return Response(
        content=file_content,
        media_type=file_metadata.get("mime_type", "application/octet-stream"),
        headers={
            "Content-Disposition": f'attachment; filename="{file_metadata.get("original_filename", "file")}"',
        },
    )


# ============================================================================
# CREATE FILE (UPLOAD)
# ============================================================================

@router.post(
    "/{workspace_id}/files",
    summary="Upload file",
    description="Upload a new file to a workspace",
    status_code=status.HTTP_201_CREATED,
)
async def create_file(
    request: Request,
    workspace_id: str = Depends(validate_workspace_member),
    file: UploadFile = File(..., description="File to upload"),
    name: Optional[str] = Form(None, description="File name (optional, uses original filename if not provided)"),
    description: Optional[str] = Form(None, description="File description"),
    tags: Optional[str] = Form(None, description="Comma-separated tags"),
    current_user: AuthUser = Depends(authenticate_user),
    file_service: FileService = Depends(get_file_service),
) -> Dict[str, Any]:
    """
    Upload a new file to a workspace.
    
    - **workspace_id**: Workspace ID (path parameter)
    - **file**: File to upload (multipart/form-data, required)
    - **name**: File name (form field, optional, uses original filename if not provided)
    - **description**: File description (form field, optional)
    - **tags**: Comma-separated tags (form field, optional)
    
    Requires workspace membership.
    The authenticated user will be recorded as the owner.
    
    File size and storage limits are automatically validated.
    File extensions and MIME types are validated by the service.
    """
    # Parse tags if provided
    tags_list = None
    if tags:
        tags_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
    
    result = file_service.create_file(
        workspace_id=workspace_id,
        owner_id=current_user["user_id"],
        uploaded_file=file.file,
        name=name,
        description=description,
        tags=tags_list,
        file_metadata=None,
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="File uploaded successfully",
        code=status.HTTP_201_CREATED,
    ).model_dump()


# ============================================================================
# UPDATE FILE
# ============================================================================

@router.put(
    "/{workspace_id}/files/{file_id}",
    summary="Update file metadata",
    description="Update file metadata (name, description, tags)",
    status_code=status.HTTP_200_OK,
)
async def update_file(
    request: Request,
    workspace_id: str = Depends(validate_workspace_member),
    file_id: str = Path(..., description="File ID"),
    body: UpdateFileRequest = ...,
    current_user: AuthUser = Depends(authenticate_user),
    file_service: FileService = Depends(get_file_service),
) -> Dict[str, Any]:
    """
    Update file metadata.
    
    - **workspace_id**: Workspace ID (path parameter)
    - **file_id**: File ID (path parameter)
    - **name**: File name (request body, optional, must be unique in workspace if changed)
    - **description**: File description (request body, optional)
    - **tags**: Tags (request body, optional)
    
    Requires workspace membership.
    The authenticated user will be recorded as the updater.
    Note: This endpoint only updates metadata, not the file content.
    """
    result = file_service.update_file(
        file_id=file_id,
        name=body.name,
        description=body.description,
        tags=body.tags,
        updated_by=current_user["user_id"],
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="File metadata updated successfully",
        code=status.HTTP_200_OK,
    ).model_dump()


# ============================================================================
# DELETE FILE
# ============================================================================

@router.delete(
    "/{workspace_id}/files/{file_id}",
    summary="Delete file",
    description="Delete a file from workspace",
    status_code=status.HTTP_200_OK,
)
async def delete_file(
    request: Request,
    workspace_id: str = Depends(validate_workspace_member),
    file_id: str = Path(..., description="File ID"),
    file_service: FileService = Depends(get_file_service),
) -> Dict[str, Any]:
    """
    Delete a file from workspace.
    
    - **workspace_id**: Workspace ID (path parameter)
    - **file_id**: File ID (path parameter)
    
    Requires workspace membership.
    Permanently deletes the file from storage and database.
    Workspace storage is automatically updated.
    """
    result = file_service.delete_file(
        file_id=file_id,
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="File deleted successfully",
        code=status.HTTP_200_OK,
    ).model_dump()

