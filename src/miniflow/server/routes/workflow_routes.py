"""
Workflow management routes.

Handles workflow creation, retrieval, update, and deletion for workspaces.
Workflows are automatically created with a default API trigger.
"""
from fastapi import APIRouter, Depends, Request, status, Path, Query
from typing import Dict, Any, Optional

from src.miniflow.server.dependencies import get_workflow_service
from src.miniflow.services import WorkflowService
from src.miniflow.database.models.enums import WorkflowStatus
from src.miniflow.server.helpers import (
    validate_workspace_member,
    authenticate_user,
    AuthUser,
)
from src.miniflow.server.schemas.base_schema import create_success_response
from src.miniflow.server.schemas.routes.workflow_schemas.workflow_schemas import (
    CreateWorkflowRequest,
    UpdateWorkflowRequest,
)

router = APIRouter(prefix="/workspaces", tags=["workflows"])


# ============================================================================
# GET ALL WORKFLOWS
# ============================================================================

@router.get(
    "/{workspace_id}/workflows",
    summary="Get all workflows",
    description="Get all workflows for a workspace with pagination and filtering",
    status_code=status.HTTP_200_OK,
)
async def get_all_workflows(
    request: Request,
    workspace_id: str = Depends(validate_workspace_member),
    page: int = Query(1, ge=1, description="Page number (starts from 1)"),
    page_size: int = Query(100, ge=1, le=1000, description="Number of items per page (1-1000)"),
    order_by: Optional[str] = Query(None, description="Field to order by (default: created_at)"),
    order_desc: bool = Query(False, description="Order descending (default: False)"),
    include_deleted: bool = Query(False, description="Include deleted workflows"),
    status_filter: Optional[WorkflowStatus] = Query(None, description="Filter by workflow status", alias="status"),
    workflow_service: WorkflowService = Depends(get_workflow_service),
) -> Dict[str, Any]:
    """
    Get all workflows for a workspace with pagination and filtering.
    
    - **workspace_id**: Workspace ID (path parameter)
    - **page**: Page number (query parameter, default: 1, min: 1)
    - **page_size**: Number of items per page (query parameter, default: 100, min: 1, max: 1000)
    - **order_by**: Field to order by (query parameter, optional, default: created_at)
    - **order_desc**: Order descending (query parameter, default: False)
    - **include_deleted**: Include deleted workflows (query parameter, default: False)
    - **status**: Filter by workflow status (query parameter, optional)
        - Supported values: DRAFT, ACTIVE, DEACTIVATED, ARCHIVED
    
    Requires workspace membership.
    Returns paginated list of workflows.
    """
    result = workflow_service.get_all_workflows(
        workspace_id=workspace_id,
        page=page,
        page_size=page_size,
        order_by=order_by,
        order_desc=order_desc,
        include_deleted=include_deleted,
        status=status_filter,
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="Workflows retrieved successfully",
        code=status.HTTP_200_OK,
    ).model_dump()


# ============================================================================
# GET WORKFLOW
# ============================================================================

@router.get(
    "/{workspace_id}/workflows/{workflow_id}",
    summary="Get workflow",
    description="Get detailed information about a specific workflow",
    status_code=status.HTTP_200_OK,
)
async def get_workflow(
    request: Request,
    workspace_id: str = Depends(validate_workspace_member),
    workflow_id: str = Path(..., description="Workflow ID"),
    workflow_service: WorkflowService = Depends(get_workflow_service),
) -> Dict[str, Any]:
    """
    Get detailed information about a specific workflow.
    
    - **workspace_id**: Workspace ID (path parameter)
    - **workflow_id**: Workflow ID (path parameter)
    
    Requires workspace membership.
    Returns workflow information including status, priority, and tags.
    """
    result = workflow_service.get_workflow(
        workflow_id=workflow_id,
        workspace_id=workspace_id,
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="Workflow retrieved successfully",
        code=status.HTTP_200_OK,
    ).model_dump()


# ============================================================================
# CREATE WORKFLOW
# ============================================================================

@router.post(
    "/{workspace_id}/workflows",
    summary="Create workflow",
    description="Create a new workflow for a workspace",
    status_code=status.HTTP_201_CREATED,
)
async def create_workflow(
    request: Request,
    workspace_id: str = Depends(validate_workspace_member),
    body: CreateWorkflowRequest = ...,
    current_user: AuthUser = Depends(authenticate_user),
    workflow_service: WorkflowService = Depends(get_workflow_service),
) -> Dict[str, Any]:
    """
    Create a new workflow for a workspace.
    
    - **workspace_id**: Workspace ID (path parameter)
    - **name**: Workflow name (request body, required, must be unique in workspace)
    - **description**: Workflow description (request body, optional)
    - **priority**: Priority level (request body, optional, default: 1, min: 1)
    - **status**: Workflow status (request body, optional, default: DRAFT)
        - Supported values: DRAFT, ACTIVE, DEACTIVATED, ARCHIVED
    - **status_message**: Status message (request body, optional)
    - **tags**: Optional tags (request body, optional)
    
    Requires workspace membership.
    The authenticated user will be recorded as the creator.
    A default API trigger (WEBHOOK type) named "DEFAULT" is automatically created with the workflow.
    """
    result = workflow_service.create_workflow(
        workspace_id=workspace_id,
        name=body.name,
        description=body.description,
        priority=body.priority,
        status=body.status,
        status_message=body.status_message,
        tags=body.tags,
        created_by=current_user["user_id"],
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="Workflow created successfully",
        code=status.HTTP_201_CREATED,
    ).model_dump()


# ============================================================================
# UPDATE WORKFLOW
# ============================================================================

@router.put(
    "/{workspace_id}/workflows/{workflow_id}",
    summary="Update workflow",
    description="Update an existing workflow",
    status_code=status.HTTP_200_OK,
)
async def update_workflow(
    request: Request,
    workspace_id: str = Depends(validate_workspace_member),
    workflow_id: str = Path(..., description="Workflow ID"),
    body: UpdateWorkflowRequest = ...,
    current_user: AuthUser = Depends(authenticate_user),
    workflow_service: WorkflowService = Depends(get_workflow_service),
) -> Dict[str, Any]:
    """
    Update an existing workflow.
    
    - **workspace_id**: Workspace ID (path parameter)
    - **workflow_id**: Workflow ID (path parameter)
    - **name**: Workflow name (request body, optional, must be unique in workspace if changed)
    - **description**: Workflow description (request body, optional)
    - **priority**: Priority level (request body, optional, min: 1)
    - **status**: Workflow status (request body, optional)
        - Supported values: DRAFT, ACTIVE, DEACTIVATED, ARCHIVED
    - **status_message**: Status message (request body, optional)
    - **tags**: Tags (request body, optional)
    
    Requires workspace membership.
    The authenticated user will be recorded as the updater.
    """
    result = workflow_service.update_workflow(
        workflow_id=workflow_id,
        workspace_id=workspace_id,
        name=body.name,
        description=body.description,
        priority=body.priority,
        status=body.status,
        status_message=body.status_message,
        tags=body.tags,
        updated_by=current_user["user_id"],
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="Workflow updated successfully",
        code=status.HTTP_200_OK,
    ).model_dump()


# ============================================================================
# DELETE WORKFLOW
# ============================================================================

@router.delete(
    "/{workspace_id}/workflows/{workflow_id}",
    summary="Delete workflow",
    description="Delete a workflow",
    status_code=status.HTTP_200_OK,
)
async def delete_workflow(
    request: Request,
    workspace_id: str = Depends(validate_workspace_member),
    workflow_id: str = Path(..., description="Workflow ID"),
    workflow_service: WorkflowService = Depends(get_workflow_service),
) -> Dict[str, Any]:
    """
    Delete a workflow.
    
    - **workspace_id**: Workspace ID (path parameter)
    - **workflow_id**: Workflow ID (path parameter)
    
    Requires workspace membership.
    Permanently deletes the workflow and all associated nodes, edges, triggers, and executions (CASCADE).
    """
    result = workflow_service.delete_workflow(
        workflow_id=workflow_id,
        workspace_id=workspace_id,
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="Workflow deleted successfully",
        code=status.HTTP_200_OK,
    ).model_dump()

