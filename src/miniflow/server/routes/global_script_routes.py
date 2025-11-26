"""
Global Script management routes.

Handles global script creation, retrieval, update, and deletion.
Global scripts are available to all workspaces and not workspace-specific.
"""
from fastapi import APIRouter, Depends, Request, status, Path, Query
from typing import Dict, Any, Optional

from src.miniflow.server.dependencies import get_global_script_service
from src.miniflow.services import GlobalScriptService
from src.miniflow.server.helpers import authenticate_user, AuthUser
from src.miniflow.server.schemas.base_schema import create_success_response
from src.miniflow.server.schemas.routes.script_schemas.global_script_schemas import (
    CreateGlobalScriptRequest,
    UpdateGlobalScriptRequest,
)

router = APIRouter(prefix="/scripts", tags=["global-scripts"])


# ============================================================================
# GET ALL SCRIPTS
# ============================================================================

@router.get(
    "",
    summary="Get all global scripts",
    description="Get all global scripts with pagination and filtering",
    status_code=status.HTTP_200_OK,
)
async def get_all_scripts(
    request: Request,
    page: int = Query(1, ge=1, description="Page number (starts from 1)"),
    page_size: int = Query(100, ge=1, le=1000, description="Number of items per page (1-1000)"),
    order_by: Optional[str] = Query(None, description="Field to order by (default: created_at)"),
    order_desc: bool = Query(False, description="Order descending (default: False)"),
    include_deleted: bool = Query(False, description="Include deleted scripts"),
    category: Optional[str] = Query(None, description="Filter by category"),
    subcategory: Optional[str] = Query(None, description="Filter by subcategory"),
    script_service: GlobalScriptService = Depends(get_global_script_service),
) -> Dict[str, Any]:
    """
    Get all global scripts with pagination and filtering.
    
    - **page**: Page number (query parameter, default: 1, min: 1)
    - **page_size**: Number of items per page (query parameter, default: 100, min: 1, max: 1000)
    - **order_by**: Field to order by (query parameter, optional, default: created_at)
    - **order_desc**: Order descending (query parameter, default: False)
    - **include_deleted**: Include deleted scripts (query parameter, default: False)
    - **category**: Filter by category (query parameter, optional)
    - **subcategory**: Filter by subcategory (query parameter, optional)
    
    Public endpoint - no authentication required.
    Returns paginated list of global scripts (metadata only, not content).
    """
    result = script_service.get_all_scripts(
        page=page,
        page_size=page_size,
        order_by=order_by,
        order_desc=order_desc,
        include_deleted=include_deleted,
        category=category,
        subcategory=subcategory,
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="Global scripts retrieved successfully",
        code=status.HTTP_200_OK,
    ).model_dump()


# ============================================================================
# GET SCRIPT
# ============================================================================

@router.get(
    "/{script_id}",
    summary="Get global script",
    description="Get detailed information about a specific global script",
    status_code=status.HTTP_200_OK,
)
async def get_script(
    request: Request,
    script_id: str = Path(..., description="Script ID"),
    script_service: GlobalScriptService = Depends(get_global_script_service),
) -> Dict[str, Any]:
    """
    Get detailed information about a specific global script.
    
    - **script_id**: Script ID (path parameter)
    
    Public endpoint - no authentication required.
    Returns script metadata (not the script content).
    Use GET /scripts/{script_id}/content to get the script content.
    """
    result = script_service.get_script(
        script_id=script_id,
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="Global script retrieved successfully",
        code=status.HTTP_200_OK,
    ).model_dump()


# ============================================================================
# GET SCRIPT CONTENT
# ============================================================================

@router.get(
    "/{script_id}/content",
    summary="Get script content",
    description="Get script content, input schema, and output schema",
    status_code=status.HTTP_200_OK,
)
async def get_script_content(
    request: Request,
    script_id: str = Path(..., description="Script ID"),
    script_service: GlobalScriptService = Depends(get_global_script_service),
) -> Dict[str, Any]:
    """
    Get script content, input schema, and output schema.
    
    - **script_id**: Script ID (path parameter)
    
    Public endpoint - no authentication required.
    Returns script content, input schema, and output schema.
    """
    result = script_service.get_script_content(
        script_id=script_id,
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="Script content retrieved successfully",
        code=status.HTTP_200_OK,
    ).model_dump()


# ============================================================================
# CREATE SCRIPT
# ============================================================================

@router.post(
    "",
    summary="Create global script",
    description="Create a new global script",
    status_code=status.HTTP_201_CREATED,
)
async def create_script(
    request: Request,
    body: CreateGlobalScriptRequest = ...,
    current_user: AuthUser = Depends(authenticate_user),
    script_service: GlobalScriptService = Depends(get_global_script_service),
) -> Dict[str, Any]:
    """
    Create a new global script.
    
    - **name**: Script name (request body, required, must be unique globally)
    - **category**: Script category (request body, required)
    - **description**: Script description (request body, optional)
    - **subcategory**: Script subcategory (request body, optional)
    - **content**: Script content (request body, required, Python code)
    - **script_metadata**: Optional script metadata (request body, optional)
    - **required_packages**: Required Python packages (request body, optional)
    - **input_schema**: Input validation schema (request body, optional)
    - **output_schema**: Output validation schema (request body, optional)
    - **tags**: Optional tags (request body, optional)
    - **documentation_url**: Documentation URL (request body, optional)
    
    Requires authentication.
    Script name must be unique globally and within the category/subcategory combination.
    Script file is automatically created and stored.
    """
    result = script_service.create_script(
        name=body.name,
        category=body.category,
        description=body.description,
        subcategory=body.subcategory,
        content=body.content,
        script_metadata=body.script_metadata,
        required_packages=body.required_packages,
        input_schema=body.input_schema,
        output_schema=body.output_schema,
        tags=body.tags,
        documentation_url=body.documentation_url,
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="Global script created successfully",
        code=status.HTTP_201_CREATED,
    ).model_dump()


# ============================================================================
# UPDATE SCRIPT
# ============================================================================

@router.put(
    "/{script_id}",
    summary="Update global script",
    description="Update global script metadata",
    status_code=status.HTTP_200_OK,
)
async def update_script(
    request: Request,
    script_id: str = Path(..., description="Script ID"),
    body: UpdateGlobalScriptRequest = ...,
    current_user: AuthUser = Depends(authenticate_user),
    script_service: GlobalScriptService = Depends(get_global_script_service),
) -> Dict[str, Any]:
    """
    Update global script metadata.
    
    - **script_id**: Script ID (path parameter)
    - **description**: Script description (request body, optional)
    - **tags**: Tags (request body, optional)
    - **documentation_url**: Documentation URL (request body, optional)
    
    Requires authentication.
    Note: This endpoint only updates metadata, not the script content.
    """
    result = script_service.update_script(
        script_id=script_id,
        description=body.description,
        tags=body.tags,
        documentation_url=body.documentation_url,
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="Global script updated successfully",
        code=status.HTTP_200_OK,
    ).model_dump()


# ============================================================================
# DELETE SCRIPT
# ============================================================================

@router.delete(
    "/{script_id}",
    summary="Delete global script",
    description="Delete a global script",
    status_code=status.HTTP_200_OK,
)
async def delete_script(
    request: Request,
    script_id: str = Path(..., description="Script ID"),
    current_user: AuthUser = Depends(authenticate_user),
    script_service: GlobalScriptService = Depends(get_global_script_service),
) -> Dict[str, Any]:
    """
    Delete a global script.
    
    - **script_id**: Script ID (path parameter)
    
    Requires authentication.
    Permanently deletes the script and its file from storage.
    """
    result = script_service.delete_script(
        script_id=script_id,
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="Global script deleted successfully",
        code=status.HTTP_200_OK,
    ).model_dump()

