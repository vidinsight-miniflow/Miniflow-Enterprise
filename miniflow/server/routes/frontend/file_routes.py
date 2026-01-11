"""File routes for frontend."""

from fastapi import APIRouter, Request, Depends, Path, File, UploadFile, Form
from fastapi.responses import StreamingResponse, Response
from typing import Optional, List

from miniflow.server.dependencies import (
    get_file_service,
    authenticate_user,
    require_workspace_access,
)
from miniflow.server.dependencies.auth import AuthenticatedUser
from miniflow.server.schemas.base_schemas import create_success_response
from .schemas.file_schemas import (
    UploadFileResponse,
    FileResponse,
    WorkspaceFilesResponse,
    UpdateFileRequest,
    DeleteFileResponse,
)

router = APIRouter(prefix="/workspaces", tags=["Files"])


# ============================================================================
# UPLOAD FILE ENDPOINTS
# ============================================================================

@router.post("/{workspace_id}/files", response_model_exclude_none=True)
async def upload_file(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    file: UploadFile = File(..., description="File to upload"),
    name: Optional[str] = Form(None, description="File name (optional, auto-generated if not provided)"),
    description: Optional[str] = Form(None, description="File description"),
    tags: Optional[str] = Form(None, description="Tags (comma-separated)"),
    service = Depends(get_file_service),
    current_user: AuthenticatedUser = Depends(authenticate_user),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Upload a file.
    
    Requires: Workspace access
    Content-Type: multipart/form-data
    Note: File size and storage limits are checked automatically.
    """
    # Parse tags
    tag_list = None
    if tags:
        tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
    
    # UploadFile.file is a SpooledTemporaryFile (BinaryIO)
    # Helper function needs filename attribute, so we set it on the file object
    file_obj = file.file
    if hasattr(file, 'filename') and file.filename:
        # Set filename attribute for helper function
        file_obj.filename = file.filename
    
    result = service.upload_file(
        workspace_id=workspace_id,
        owner_id=current_user["user_id"],
        uploaded_file=file_obj,  # FastAPI UploadFile.file is BinaryIO (SpooledTemporaryFile)
        name=name,
        description=description,
        tags=tag_list,
        file_metadata=None
    )
    
    response_data = UploadFileResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="File uploaded successfully."
    )


# ============================================================================
# GET FILE ENDPOINTS
# ============================================================================

@router.get("/{workspace_id}/files/{file_id}", response_model_exclude_none=True)
async def get_file(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    file_id: str = Path(..., description="File ID"),
    service = Depends(get_file_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Get file details.
    
    Requires: Workspace access
    """
    result = service.get_file(
        file_id=file_id
    )
    
    response_data = FileResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump()
    )


@router.get("/{workspace_id}/files", response_model_exclude_none=True)
async def get_workspace_files(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    service = Depends(get_file_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Get all workspace files.
    
    Requires: Workspace access
    """
    result = service.get_workspace_files(
        workspace_id=workspace_id
    )
    
    response_data = WorkspaceFilesResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump()
    )


@router.get("/{workspace_id}/files/{file_id}/download", response_model_exclude_none=True)
async def download_file(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    file_id: str = Path(..., description="File ID"),
    service = Depends(get_file_service),
    _: str = Depends(require_workspace_access),
) -> StreamingResponse:
    """
    Download file content.
    
    Requires: Workspace access
    Returns: File content as binary stream
    """
    # Get file details first
    file_details = service.get_file(file_id=file_id)
    
    # Get file content
    file_content = service.get_file_content(file_id=file_id)
    
    # Get file metadata
    file_name = file_details.get("name") or file_details.get("original_filename") or "file"
    mime_type = file_details.get("mime_type") or "application/octet-stream"
    
    return StreamingResponse(
        iter([file_content]),
        media_type=mime_type,
        headers={
            "Content-Disposition": f'attachment; filename="{file_name}"'
        }
    )


# ============================================================================
# UPDATE FILE ENDPOINTS
# ============================================================================

@router.put("/{workspace_id}/files/{file_id}", response_model_exclude_none=True)
async def update_file(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    file_id: str = Path(..., description="File ID"),
    file_data: UpdateFileRequest = ...,
    service = Depends(get_file_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Update file metadata.
    
    Requires: Workspace access
    Note: File content cannot be changed. Upload a new file instead.
    """
    result = service.update_file(
        file_id=file_id,
        name=file_data.name,
        description=file_data.description,
        tags=file_data.tags
    )
    
    response_data = FileResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="File metadata updated successfully."
    )


# ============================================================================
# DELETE FILE ENDPOINTS
# ============================================================================

@router.delete("/{workspace_id}/files/{file_id}", response_model_exclude_none=True)
async def delete_file(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    file_id: str = Path(..., description="File ID"),
    service = Depends(get_file_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Delete file.
    
    Requires: Workspace access
    Note: Both file storage and database record will be deleted.
    """
    result = service.delete_file(
        file_id=file_id
    )
    
    response_data = DeleteFileResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="File deleted successfully."
    )

