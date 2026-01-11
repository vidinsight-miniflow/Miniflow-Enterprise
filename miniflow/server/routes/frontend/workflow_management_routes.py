"""Workflow management routes for frontend."""

from typing import Optional
from fastapi import APIRouter, Request, Depends, Path, Query

from miniflow.server.dependencies import (
    get_workflow_service,
    authenticate_user,
    require_workspace_access,
)
from miniflow.server.dependencies.auth import AuthenticatedUser
from miniflow.server.schemas.base_schemas import create_success_response
from miniflow.models.enums import WorkflowStatus
from .schemas.workflow_management_schemas import (
    CreateWorkflowRequest,
    CreateWorkflowResponse,
    WorkflowResponse,
    WorkspaceWorkflowsResponse,
    UpdateWorkflowRequest,
    ActivateWorkflowResponse,
    DeactivateWorkflowRequest,
    DeactivateWorkflowResponse,
    ArchiveWorkflowResponse,
    SetDraftResponse,
    DeleteWorkflowResponse,
    WorkflowGraphResponse,
)

router = APIRouter(prefix="/workspaces", tags=["Workflows"])


# ============================================================================
# CREATE WORKFLOW ENDPOINTS
# ============================================================================

@router.post("/{workspace_id}/workflows", response_model_exclude_none=True)
async def create_workflow(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    workflow_data: CreateWorkflowRequest = ...,
    service = Depends(get_workflow_service),
    current_user: AuthenticatedUser = Depends(authenticate_user),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Create a new workflow.
    
    Requires: Workspace access
    Note: Workflow is created with DRAFT status. A default API trigger is automatically created.
    """
    result = service.create_workflow(
        workspace_id=workspace_id,
        name=workflow_data.name,
        created_by=current_user["user_id"],
        description=workflow_data.description,
        priority=workflow_data.priority,
        tags=workflow_data.tags
    )
    
    response_data = CreateWorkflowResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Workflow created successfully. Default API trigger has been created."
    )


# ============================================================================
# GET WORKFLOW ENDPOINTS
# ============================================================================

@router.get("/{workspace_id}/workflows/{workflow_id}", response_model_exclude_none=True)
async def get_workflow(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    workflow_id: str = Path(..., description="Workflow ID"),
    service = Depends(get_workflow_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Get workflow details.
    
    Requires: Workspace access
    """
    result = service.get_workflow(
        workflow_id=workflow_id
    )
    
    response_data = WorkflowResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump()
    )


@router.get("/{workspace_id}/workflows", response_model_exclude_none=True)
async def get_workspace_workflows(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    status: Optional[str] = Query(None, description="Filter by status (DRAFT, ACTIVE, DEACTIVATED, ARCHIVED)"),
    service = Depends(get_workflow_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Get all workspace workflows.
    
    Requires: Workspace access
    """
    workflow_status = None
    if status:
        try:
            workflow_status = WorkflowStatus(status.upper())
        except ValueError:
            pass
    
    result = service.get_workspace_workflows(
        workspace_id=workspace_id,
        status=workflow_status
    )
    
    response_data = WorkspaceWorkflowsResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump()
    )


@router.get("/{workspace_id}/workflows/{workflow_id}/graph", response_model_exclude_none=True)
async def get_workflow_graph(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    workflow_id: str = Path(..., description="Workflow ID"),
    service = Depends(get_workflow_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Get workflow graph (nodes and edges).
    
    Requires: Workspace access
    """
    result = service.get_workflow_graph(
        workflow_id=workflow_id
    )
    
    response_data = WorkflowGraphResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump()
    )


# ============================================================================
# UPDATE WORKFLOW ENDPOINTS
# ============================================================================

@router.put("/{workspace_id}/workflows/{workflow_id}", response_model_exclude_none=True)
async def update_workflow(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    workflow_id: str = Path(..., description="Workflow ID"),
    workflow_data: UpdateWorkflowRequest = ...,
    service = Depends(get_workflow_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Update workflow information.
    
    Requires: Workspace access
    """
    result = service.update_workflow(
        workflow_id=workflow_id,
        name=workflow_data.name,
        description=workflow_data.description,
        priority=workflow_data.priority,
        tags=workflow_data.tags
    )
    
    response_data = WorkflowResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Workflow updated successfully."
    )


# ============================================================================
# STATUS MANAGEMENT ENDPOINTS
# ============================================================================

@router.post("/{workspace_id}/workflows/{workflow_id}/activate", response_model_exclude_none=True)
async def activate_workflow(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    workflow_id: str = Path(..., description="Workflow ID"),
    service = Depends(get_workflow_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Activate workflow.
    
    Requires: Workspace access
    Note: Workflow must have at least one node to be activated.
    """
    result = service.activate_workflow(
        workflow_id=workflow_id
    )
    
    response_data = ActivateWorkflowResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Workflow activated successfully."
    )


@router.post("/{workspace_id}/workflows/{workflow_id}/deactivate", response_model_exclude_none=True)
async def deactivate_workflow(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    workflow_id: str = Path(..., description="Workflow ID"),
    deactivate_data: DeactivateWorkflowRequest = ...,
    service = Depends(get_workflow_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Deactivate workflow.
    
    Requires: Workspace access
    """
    result = service.deactivate_workflow(
        workflow_id=workflow_id,
        reason=deactivate_data.reason
    )
    
    response_data = DeactivateWorkflowResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Workflow deactivated successfully."
    )


@router.post("/{workspace_id}/workflows/{workflow_id}/archive", response_model_exclude_none=True)
async def archive_workflow(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    workflow_id: str = Path(..., description="Workflow ID"),
    service = Depends(get_workflow_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Archive workflow.
    
    Requires: Workspace access
    Note: Archived workflows cannot be modified or activated.
    """
    result = service.archive_workflow(
        workflow_id=workflow_id
    )
    
    response_data = ArchiveWorkflowResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Workflow archived successfully."
    )


@router.post("/{workspace_id}/workflows/{workflow_id}/set-draft", response_model_exclude_none=True)
async def set_draft(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    workflow_id: str = Path(..., description="Workflow ID"),
    service = Depends(get_workflow_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Set workflow to draft status.
    
    Requires: Workspace access
    Note: Archived workflows cannot be set to draft.
    """
    result = service.set_draft(
        workflow_id=workflow_id
    )
    
    response_data = SetDraftResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Workflow set to draft status."
    )


# ============================================================================
# DELETE WORKFLOW ENDPOINTS
# ============================================================================

@router.delete("/{workspace_id}/workflows/{workflow_id}", response_model_exclude_none=True)
async def delete_workflow(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    workflow_id: str = Path(..., description="Workflow ID"),
    service = Depends(get_workflow_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Delete workflow.
    
    Requires: Workspace access
    Note: All nodes, edges, and triggers will be deleted (cascade).
    """
    result = service.delete_workflow(
        workflow_id=workflow_id
    )
    
    response_data = DeleteWorkflowResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Workflow deleted successfully."
    )

