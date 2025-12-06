"""Execution management routes for frontend."""

from typing import Optional
from fastapi import APIRouter, Request, Depends, Path, Query

from miniflow.server.dependencies import (
    get_execution_service,
    authenticate_user,
    require_workspace_access,
)
from miniflow.server.dependencies.auth import AuthenticatedUser
from miniflow.server.schemas.base_schemas import create_success_response
from miniflow.models.enums import ExecutionStatus
from .schemas.execution_management_schemas import (
    StartExecutionByWorkflowRequest,
    StartExecutionResponse,
    ExecutionResponse,
    WorkspaceExecutionsResponse,
    WorkflowExecutionsResponse,
    ExecutionStatsResponse,
)

router = APIRouter(prefix="/workspaces", tags=["Executions"])


# ============================================================================
# START EXECUTION ENDPOINTS (TEST)
# ============================================================================

@router.post("/{workspace_id}/workflows/{workflow_id}/executions/test", response_model_exclude_none=True)
async def start_execution_by_workflow(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    workflow_id: str = Path(..., description="Workflow ID"),
    execution_data: StartExecutionByWorkflowRequest = ...,
    service = Depends(get_execution_service),
    current_user: AuthenticatedUser = Depends(authenticate_user),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Start execution by workflow (UI test).
    
    Requires: Workspace access
    Note: This is for testing purposes. No trigger validation is performed.
    Execution inputs are automatically created for all workflow nodes.
    """
    result = service.start_execution_by_workflow(
        workspace_id=workspace_id,
        workflow_id=workflow_id,
        input_data=execution_data.input_data,
        triggered_by=current_user["user_id"]
    )
    
    response_data = StartExecutionResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Execution started successfully for testing."
    )


# ============================================================================
# GET EXECUTION ENDPOINTS
# ============================================================================

@router.get("/{workspace_id}/executions/{execution_id}", response_model_exclude_none=True)
async def get_execution(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    execution_id: str = Path(..., description="Execution ID"),
    service = Depends(get_execution_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Get execution details.
    
    Requires: Workspace access
    """
    result = service.get_execution(
        execution_id=execution_id
    )
    
    response_data = ExecutionResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump()
    )


@router.get("/{workspace_id}/executions", response_model_exclude_none=True)
async def get_workspace_executions(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    status: Optional[str] = Query(None, description="Filter by status (PENDING, RUNNING, COMPLETED, FAILED, CANCELLED, TIMEOUT)"),
    service = Depends(get_execution_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Get all workspace executions.
    
    Requires: Workspace access
    """
    execution_status = None
    if status:
        try:
            execution_status = ExecutionStatus(status.upper())
        except ValueError:
            pass
    
    result = service.get_workspace_executions(
        workspace_id=workspace_id,
        status=execution_status
    )
    
    response_data = WorkspaceExecutionsResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump()
    )


@router.get("/{workspace_id}/workflows/{workflow_id}/executions", response_model_exclude_none=True)
async def get_workflow_executions(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    workflow_id: str = Path(..., description="Workflow ID"),
    service = Depends(get_execution_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Get all workflow executions.
    
    Requires: Workspace access
    """
    result = service.get_workflow_executions(
        workflow_id=workflow_id
    )
    
    response_data = WorkflowExecutionsResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump()
    )


@router.get("/{workspace_id}/executions/stats", response_model_exclude_none=True)
async def get_execution_stats(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    service = Depends(get_execution_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Get execution statistics for workspace.
    
    Requires: Workspace access
    """
    result = service.get_execution_stats(
        workspace_id=workspace_id
    )
    
    response_data = ExecutionStatsResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump()
    )

