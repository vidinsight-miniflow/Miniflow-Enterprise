"""Custom script routes for frontend."""

from typing import Optional
from fastapi import APIRouter, Request, Depends, Path, Query

from miniflow.server.dependencies import (
    get_custom_script_service,
    authenticate_user,
    authenticate_admin,
    require_workspace_access,
)
from miniflow.server.dependencies.auth import AuthenticatedUser
from miniflow.server.schemas.base_schemas import create_success_response
from miniflow.models.enums import ScriptApprovalStatus
from .schemas.custom_script_schemas import (
    CreateCustomScriptRequest,
    CreateCustomScriptResponse,
    CustomScriptResponse,
    ScriptContentResponse,
    WorkspaceScriptsResponse,
    UpdateCustomScriptRequest,
    ApproveScriptRequest,
    ApproveScriptResponse,
    RejectScriptRequest,
    RejectScriptResponse,
    ResetApprovalStatusResponse,
    MarkDangerousResponse,
    UnmarkDangerousResponse,
    DeleteCustomScriptResponse,
)

router = APIRouter(prefix="/workspaces", tags=["Custom Scripts"])


# ============================================================================
# CREATE SCRIPT ENDPOINTS
# ============================================================================

@router.post("/{workspace_id}/scripts", response_model_exclude_none=True)
async def create_custom_script(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    script_data: CreateCustomScriptRequest = ...,
    service = Depends(get_custom_script_service),
    current_user: AuthenticatedUser = Depends(authenticate_user),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Create a new custom script.
    
    Requires: Workspace access
    Note: Script content cannot be changed after creation. Script is created with PENDING approval status.
    """
    result = service.create_custom_script(
        workspace_id=workspace_id,
        uploaded_by=current_user["user_id"],
        name=script_data.name,
        content=script_data.content,
        description=script_data.description,
        category=script_data.category,
        subcategory=script_data.subcategory,
        required_packages=script_data.required_packages,
        input_schema=script_data.input_schema,
        output_schema=script_data.output_schema,
        tags=script_data.tags,
        documentation_url=script_data.documentation_url
    )
    
    response_data = CreateCustomScriptResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Custom script created successfully. Waiting for approval."
    )


# ============================================================================
# GET SCRIPT ENDPOINTS
# ============================================================================

@router.get("/{workspace_id}/scripts/{script_id}", response_model_exclude_none=True)
async def get_custom_script(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    script_id: str = Path(..., description="Script ID"),
    service = Depends(get_custom_script_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Get custom script details (without content).
    
    Requires: Workspace access
    """
    result = service.get_custom_script(
        script_id=script_id
    )
    
    response_data = CustomScriptResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump()
    )


@router.get("/{workspace_id}/scripts/{script_id}/content", response_model_exclude_none=True)
async def get_script_content(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    script_id: str = Path(..., description="Script ID"),
    service = Depends(get_custom_script_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Get script content and schemas.
    
    Requires: Workspace access
    """
    result = service.get_script_content(
        script_id=script_id
    )
    
    response_data = ScriptContentResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump()
    )


@router.get("/{workspace_id}/scripts", response_model_exclude_none=True)
async def get_workspace_scripts(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    category: Optional[str] = Query(None, description="Filter by category"),
    approval_status: Optional[str] = Query(None, description="Filter by approval status (PENDING, APPROVED, REJECTED)"),
    service = Depends(get_custom_script_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Get all workspace scripts.
    
    Requires: Workspace access
    """
    status = None
    if approval_status:
        try:
            status = ScriptApprovalStatus(approval_status.upper())
        except ValueError:
            pass
    
    result = service.get_workspace_scripts(
        workspace_id=workspace_id,
        category=category,
        approval_status=status
    )
    
    response_data = WorkspaceScriptsResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump()
    )


# ============================================================================
# UPDATE SCRIPT ENDPOINTS
# ============================================================================

@router.put("/{workspace_id}/scripts/{script_id}", response_model_exclude_none=True)
async def update_custom_script(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    script_id: str = Path(..., description="Script ID"),
    script_data: UpdateCustomScriptRequest = ...,
    service = Depends(get_custom_script_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Update script metadata.
    
    Requires: Workspace access
    Note: Script content cannot be changed. Create a new script instead.
    """
    result = service.update_custom_script(
        script_id=script_id,
        description=script_data.description,
        tags=script_data.tags,
        documentation_url=script_data.documentation_url
    )
    
    response_data = CustomScriptResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Script metadata updated successfully."
    )


# ============================================================================
# APPROVAL WORKFLOW ENDPOINTS
# ============================================================================

@router.post("/{workspace_id}/scripts/{script_id}/approve", response_model_exclude_none=True)
async def approve_script(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    script_id: str = Path(..., description="Script ID"),
    approval_data: ApproveScriptRequest = ...,
    service = Depends(get_custom_script_service),
    current_user: AuthenticatedUser = Depends(authenticate_admin),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Approve script.
    
    Requires: Admin authentication + Workspace access
    """
    result = service.approve_script(
        script_id=script_id,
        reviewed_by=current_user["user_id"],
        review_notes=approval_data.review_notes
    )
    
    response_data = ApproveScriptResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Script approved successfully."
    )


@router.post("/{workspace_id}/scripts/{script_id}/reject", response_model_exclude_none=True)
async def reject_script(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    script_id: str = Path(..., description="Script ID"),
    rejection_data: RejectScriptRequest = ...,
    service = Depends(get_custom_script_service),
    current_user: AuthenticatedUser = Depends(authenticate_admin),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Reject script.
    
    Requires: Admin authentication + Workspace access
    Note: Review notes are required for rejection.
    """
    result = service.reject_script(
        script_id=script_id,
        reviewed_by=current_user["user_id"],
        review_notes=rejection_data.review_notes
    )
    
    response_data = RejectScriptResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Script rejected."
    )


@router.post("/{workspace_id}/scripts/{script_id}/reset-approval", response_model_exclude_none=True)
async def reset_approval_status(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    script_id: str = Path(..., description="Script ID"),
    service = Depends(get_custom_script_service),
    current_user: AuthenticatedUser = Depends(authenticate_admin),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Reset approval status to PENDING.
    
    Requires: Admin authentication + Workspace access
    """
    result = service.reset_approval_status(
        script_id=script_id
    )
    
    response_data = ResetApprovalStatusResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Approval status reset to PENDING."
    )


# ============================================================================
# DANGEROUS FLAG ENDPOINTS
# ============================================================================

@router.post("/{workspace_id}/scripts/{script_id}/mark-dangerous", response_model_exclude_none=True)
async def mark_as_dangerous(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    script_id: str = Path(..., description="Script ID"),
    service = Depends(get_custom_script_service),
    current_user: AuthenticatedUser = Depends(authenticate_admin),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Mark script as dangerous.
    
    Requires: Admin authentication + Workspace access
    """
    result = service.mark_as_dangerous(
        script_id=script_id
    )
    
    response_data = MarkDangerousResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Script marked as dangerous."
    )


@router.post("/{workspace_id}/scripts/{script_id}/unmark-dangerous", response_model_exclude_none=True)
async def unmark_as_dangerous(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    script_id: str = Path(..., description="Script ID"),
    service = Depends(get_custom_script_service),
    current_user: AuthenticatedUser = Depends(authenticate_admin),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Unmark script as dangerous.
    
    Requires: Admin authentication + Workspace access
    """
    result = service.unmark_as_dangerous(
        script_id=script_id
    )
    
    response_data = UnmarkDangerousResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Script unmarked as dangerous."
    )


# ============================================================================
# DELETE SCRIPT ENDPOINTS
# ============================================================================

@router.delete("/{workspace_id}/scripts/{script_id}", response_model_exclude_none=True)
async def delete_custom_script(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    script_id: str = Path(..., description="Script ID"),
    service = Depends(get_custom_script_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Delete custom script.
    
    Requires: Workspace access
    Note: Both file and database record will be deleted.
    """
    result = service.delete_custom_script(
        script_id=script_id
    )
    
    response_data = DeleteCustomScriptResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Script deleted successfully."
    )

