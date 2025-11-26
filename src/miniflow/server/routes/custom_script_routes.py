"""
Custom Script management routes.

Handles custom script creation, retrieval, update, and deletion for workspaces.
Custom scripts are workspace-specific and require approval before use.
"""
from fastapi import APIRouter, Depends, Request, status, Path, Query
from typing import Dict, Any, Optional

from src.miniflow.server.dependencies import get_custom_script_service
from src.miniflow.services import CustomScriptService
from src.miniflow.database.models.enums import ScriptApprovalStatus, ScriptTestStatus
from src.miniflow.server.helpers import (
    validate_workspace_member,
    authenticate_user,
    AuthUser,
)
from src.miniflow.server.schemas.base_schema import create_success_response
from src.miniflow.server.schemas.routes.script_schemas.custom_script_schemas import (
    CreateCustomScriptRequest,
    UpdateCustomScriptRequest,
)

router = APIRouter(prefix="/workspaces", tags=["custom-scripts"])


# ============================================================================
# GET ALL CUSTOM SCRIPTS
# ============================================================================

@router.get(
    "/{workspace_id}/custom-scripts",
    summary="Get all custom scripts",
    description="Get all custom scripts for a workspace with pagination and filtering",
    status_code=status.HTTP_200_OK,
)
async def get_all_custom_scripts(
    request: Request,
    workspace_id: str = Depends(validate_workspace_member),
    page: int = Query(1, ge=1, description="Page number (starts from 1)"),
    page_size: int = Query(100, ge=1, le=1000, description="Number of items per page (1-1000)"),
    order_by: Optional[str] = Query(None, description="Field to order by (default: created_at)"),
    order_desc: bool = Query(False, description="Order descending (default: False)"),
    include_deleted: bool = Query(False, description="Include deleted scripts"),
    category: Optional[str] = Query(None, description="Filter by category"),
    subcategory: Optional[str] = Query(None, description="Filter by subcategory"),
    approval_status: Optional[ScriptApprovalStatus] = Query(None, description="Filter by approval status"),
    test_status: Optional[ScriptTestStatus] = Query(None, description="Filter by test status"),
    script_service: CustomScriptService = Depends(get_custom_script_service),
) -> Dict[str, Any]:
    """
    Get all custom scripts for a workspace with pagination and filtering.
    
    - **workspace_id**: Workspace ID (path parameter)
    - **page**: Page number (query parameter, default: 1, min: 1)
    - **page_size**: Number of items per page (query parameter, default: 100, min: 1, max: 1000)
    - **order_by**: Field to order by (query parameter, optional, default: created_at)
    - **order_desc**: Order descending (query parameter, default: False)
    - **include_deleted**: Include deleted scripts (query parameter, default: False)
    - **category**: Filter by category (query parameter, optional)
    - **subcategory**: Filter by subcategory (query parameter, optional)
    - **approval_status**: Filter by approval status (query parameter, optional)
        - Supported values: PENDING, APPROVED, REJECTED, REVISION_NEEDED
    - **test_status**: Filter by test status (query parameter, optional)
        - Supported values: UNTESTED, TESTING, PASSED, FAILED, PARTIAL
    
    Requires workspace membership.
    Returns paginated list of custom scripts (metadata only, not content).
    """
    result = script_service.get_all_custom_scripts(
        workspace_id=workspace_id,
        page=page,
        page_size=page_size,
        order_by=order_by,
        order_desc=order_desc,
        include_deleted=include_deleted,
        category=category,
        subcategory=subcategory,
        approval_status=approval_status,
        test_status=test_status,
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="Custom scripts retrieved successfully",
        code=status.HTTP_200_OK,
    ).model_dump()


# ============================================================================
# GET CUSTOM SCRIPT
# ============================================================================

@router.get(
    "/{workspace_id}/custom-scripts/{custom_script_id}",
    summary="Get custom script",
    description="Get detailed information about a specific custom script",
    status_code=status.HTTP_200_OK,
)
async def get_custom_script(
    request: Request,
    workspace_id: str = Depends(validate_workspace_member),
    custom_script_id: str = Path(..., description="Custom Script ID"),
    script_service: CustomScriptService = Depends(get_custom_script_service),
) -> Dict[str, Any]:
    """
    Get detailed information about a specific custom script.
    
    - **workspace_id**: Workspace ID (path parameter)
    - **custom_script_id**: Custom Script ID (path parameter)
    
    Requires workspace membership.
    Returns script metadata (not the script content).
    Use GET /workspaces/{workspace_id}/custom-scripts/{custom_script_id}/content to get the script content.
    """
    result = script_service.get_custom_script(
        custom_script_id=custom_script_id,
        workspace_id=workspace_id,
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="Custom script retrieved successfully",
        code=status.HTTP_200_OK,
    ).model_dump()


# ============================================================================
# GET CUSTOM SCRIPT CONTENT
# ============================================================================

@router.get(
    "/{workspace_id}/custom-scripts/{custom_script_id}/content",
    summary="Get custom script content",
    description="Get custom script content, input schema, and output schema",
    status_code=status.HTTP_200_OK,
)
async def get_custom_script_content(
    request: Request,
    workspace_id: str = Depends(validate_workspace_member),
    custom_script_id: str = Path(..., description="Custom Script ID"),
    script_service: CustomScriptService = Depends(get_custom_script_service),
) -> Dict[str, Any]:
    """
    Get custom script content, input schema, and output schema.
    
    - **workspace_id**: Workspace ID (path parameter)
    - **custom_script_id**: Custom Script ID (path parameter)
    
    Requires workspace membership.
    Returns script content, input schema, and output schema.
    """
    result = script_service.get_custom_script_content(
        custom_script_id=custom_script_id,
        workspace_id=workspace_id,
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="Custom script content retrieved successfully",
        code=status.HTTP_200_OK,
    ).model_dump()


# ============================================================================
# CREATE CUSTOM SCRIPT
# ============================================================================

@router.post(
    "/{workspace_id}/custom-scripts",
    summary="Create custom script",
    description="Create a new custom script for a workspace",
    status_code=status.HTTP_201_CREATED,
)
async def create_custom_script(
    request: Request,
    workspace_id: str = Depends(validate_workspace_member),
    body: CreateCustomScriptRequest = ...,
    current_user: AuthUser = Depends(authenticate_user),
    script_service: CustomScriptService = Depends(get_custom_script_service),
) -> Dict[str, Any]:
    """
    Create a new custom script for a workspace.
    
    - **workspace_id**: Workspace ID (path parameter)
    - **name**: Script name (request body, required, must be unique in workspace)
    - **content**: Script content (request body, required, Python code)
    - **description**: Script description (request body, optional)
    - **category**: Script category (request body, optional)
    - **subcategory**: Script subcategory (request body, optional)
    - **required_packages**: Required Python packages (request body, optional)
    - **input_schema**: Input validation schema (request body, optional)
    - **output_schema**: Output validation schema (request body, optional)
    - **tags**: Optional tags (request body, optional)
    - **documentation_url**: Documentation URL (request body, optional)
    
    Requires workspace membership.
    The authenticated user will be recorded as the uploader.
    Script name must be unique in workspace and within the category/subcategory combination.
    Script file is automatically created and stored.
    Workspace custom script count is automatically updated.
    """
    result = script_service.create_custom_script(
        workspace_id=workspace_id,
        uploaded_by=current_user["user_id"],
        name=body.name,
        content=body.content,
        description=body.description,
        category=body.category,
        subcategory=body.subcategory,
        required_packages=body.required_packages,
        input_schema=body.input_schema,
        output_schema=body.output_schema,
        tags=body.tags,
        documentation_url=body.documentation_url,
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="Custom script created successfully",
        code=status.HTTP_201_CREATED,
    ).model_dump()


# ============================================================================
# UPDATE CUSTOM SCRIPT
# ============================================================================

@router.put(
    "/{workspace_id}/custom-scripts/{custom_script_id}",
    summary="Update custom script",
    description="Update custom script metadata",
    status_code=status.HTTP_200_OK,
)
async def update_custom_script(
    request: Request,
    workspace_id: str = Depends(validate_workspace_member),
    custom_script_id: str = Path(..., description="Custom Script ID"),
    body: UpdateCustomScriptRequest = ...,
    current_user: AuthUser = Depends(authenticate_user),
    script_service: CustomScriptService = Depends(get_custom_script_service),
) -> Dict[str, Any]:
    """
    Update custom script metadata.
    
    - **workspace_id**: Workspace ID (path parameter)
    - **custom_script_id**: Custom Script ID (path parameter)
    - **description**: Script description (request body, optional)
    - **tags**: Tags (request body, optional)
    - **documentation_url**: Documentation URL (request body, optional)
    
    Requires workspace membership.
    The authenticated user will be recorded as the updater.
    Note: This endpoint only updates metadata, not the script content.
    """
    result = script_service.update_custom_script(
        custom_script_id=custom_script_id,
        workspace_id=workspace_id,
        description=body.description,
        tags=body.tags,
        documentation_url=body.documentation_url,
        updated_by=current_user["user_id"],
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="Custom script updated successfully",
        code=status.HTTP_200_OK,
    ).model_dump()


# ============================================================================
# DELETE CUSTOM SCRIPT
# ============================================================================

@router.delete(
    "/{workspace_id}/custom-scripts/{custom_script_id}",
    summary="Delete custom script",
    description="Delete a custom script",
    status_code=status.HTTP_200_OK,
)
async def delete_custom_script(
    request: Request,
    workspace_id: str = Depends(validate_workspace_member),
    custom_script_id: str = Path(..., description="Custom Script ID"),
    script_service: CustomScriptService = Depends(get_custom_script_service),
) -> Dict[str, Any]:
    """
    Delete a custom script.
    
    - **workspace_id**: Workspace ID (path parameter)
    - **custom_script_id**: Custom Script ID (path parameter)
    
    Requires workspace membership.
    Permanently deletes the script and its file from storage.
    Workspace custom script count is automatically updated.
    """
    result = script_service.delete_custom_script(
        custom_script_id=custom_script_id,
        workspace_id=workspace_id,
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="Custom script deleted successfully",
        code=status.HTTP_200_OK,
    ).model_dump()

