"""
Trigger management routes.

Handles trigger creation, retrieval, update, and deletion for workflows.
Triggers define how workflows are executed (manual, scheduled, webhook, event).
"""
from fastapi import APIRouter, Depends, Request, status, Path, Query
from typing import Dict, Any, Optional

from src.miniflow.server.dependencies import get_trigger_service
from src.miniflow.services import TriggerService
from src.miniflow.database.models.enums import TriggerType
from src.miniflow.server.helpers import (
    validate_workspace_member,
    authenticate_user,
    AuthUser,
)
from src.miniflow.server.schemas.base_schema import create_success_response
from src.miniflow.server.schemas.routes.workflow_schemas.trigger_schemas import (
    CreateTriggerRequest,
    UpdateTriggerRequest,
)

router = APIRouter(prefix="/workspaces", tags=["triggers"])


# ============================================================================
# GET ALL TRIGGERS
# ============================================================================

@router.get(
    "/{workspace_id}/triggers",
    summary="Get all triggers",
    description="Get all triggers for a workspace with pagination and filtering",
    status_code=status.HTTP_200_OK,
)
async def get_all_triggers(
    request: Request,
    workspace_id: str = Depends(validate_workspace_member),
    page: int = Query(1, ge=1, description="Page number (starts from 1)"),
    page_size: int = Query(100, ge=1, le=1000, description="Number of items per page (1-1000)"),
    order_by: Optional[str] = Query(None, description="Field to order by (default: created_at)"),
    order_desc: bool = Query(False, description="Order descending (default: False)"),
    include_deleted: bool = Query(False, description="Include deleted triggers"),
    workflow_id: Optional[str] = Query(None, description="Filter by workflow ID"),
    trigger_type: Optional[TriggerType] = Query(None, description="Filter by trigger type"),
    is_enabled: Optional[bool] = Query(None, description="Filter by enabled status"),
    trigger_service: TriggerService = Depends(get_trigger_service),
) -> Dict[str, Any]:
    """
    Get all triggers for a workspace with pagination and filtering.
    
    - **workspace_id**: Workspace ID (path parameter)
    - **page**: Page number (query parameter, default: 1, min: 1)
    - **page_size**: Number of items per page (query parameter, default: 100, min: 1, max: 1000)
    - **order_by**: Field to order by (query parameter, optional, default: created_at)
    - **order_desc**: Order descending (query parameter, default: False)
    - **include_deleted**: Include deleted triggers (query parameter, default: False)
    - **workflow_id**: Filter by workflow ID (query parameter, optional)
    - **trigger_type**: Filter by trigger type (query parameter, optional)
        - Supported values: MANUAL, SCHEDULED, WEBHOOK, EVENT
    - **is_enabled**: Filter by enabled status (query parameter, optional)
    
    Requires workspace membership.
    Returns paginated list of triggers.
    """
    result = trigger_service.get_all_triggers(
        workspace_id=workspace_id,
        page=page,
        page_size=page_size,
        order_by=order_by,
        order_desc=order_desc,
        include_deleted=include_deleted,
        workflow_id=workflow_id,
        trigger_type=trigger_type,
        is_enabled=is_enabled,
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="Triggers retrieved successfully",
        code=status.HTTP_200_OK,
    ).model_dump()


# ============================================================================
# GET TRIGGER
# ============================================================================

@router.get(
    "/{workspace_id}/triggers/{trigger_id}",
    summary="Get trigger",
    description="Get detailed information about a specific trigger",
    status_code=status.HTTP_200_OK,
)
async def get_trigger(
    request: Request,
    workspace_id: str = Depends(validate_workspace_member),
    trigger_id: str = Path(..., description="Trigger ID"),
    trigger_service: TriggerService = Depends(get_trigger_service),
) -> Dict[str, Any]:
    """
    Get detailed information about a specific trigger.
    
    - **workspace_id**: Workspace ID (path parameter)
    - **trigger_id**: Trigger ID (path parameter)
    
    Requires workspace membership.
    Returns trigger information including configuration and input mapping.
    """
    result = trigger_service.get_trigger(
        trigger_id=trigger_id,
        workspace_id=workspace_id,
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="Trigger retrieved successfully",
        code=status.HTTP_200_OK,
    ).model_dump()


# ============================================================================
# CREATE TRIGGER
# ============================================================================

@router.post(
    "/{workspace_id}/workflows/{workflow_id}/triggers",
    summary="Create trigger",
    description="Create a new trigger for a workflow",
    status_code=status.HTTP_201_CREATED,
)
async def create_trigger(
    request: Request,
    workspace_id: str = Depends(validate_workspace_member),
    workflow_id: str = Path(..., description="Workflow ID"),
    body: CreateTriggerRequest = ...,
    current_user: AuthUser = Depends(authenticate_user),
    trigger_service: TriggerService = Depends(get_trigger_service),
) -> Dict[str, Any]:
    """
    Create a new trigger for a workflow.
    
    - **workspace_id**: Workspace ID (path parameter)
    - **workflow_id**: Workflow ID (path parameter)
    - **name**: Trigger name (request body, required, must be unique in workspace)
    - **trigger_type**: Trigger type (request body, required)
        - Supported values: MANUAL, SCHEDULED, WEBHOOK, EVENT
    - **config**: Trigger configuration (request body, required, JSON object)
        - Configuration format depends on trigger type
    - **description**: Trigger description (request body, optional)
    - **input_mapping**: Input mapping rules (request body, optional)
        - Format: {VARIABLE_NAME: {type: str, value: Any}}
    - **is_enabled**: Whether the trigger is enabled (request body, optional, default: True)
    
    Requires workspace membership.
    The workflow must belong to the specified workspace.
    The authenticated user will be recorded as the creator.
    Trigger name must be unique in workspace.
    """
    result = trigger_service.create_trigger(
        workspace_id=workspace_id,
        workflow_id=workflow_id,
        name=body.name,
        trigger_type=body.trigger_type,
        config=body.config,
        description=body.description,
        input_mapping=body.input_mapping,
        is_enabled=body.is_enabled,
        created_by=current_user["user_id"],
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="Trigger created successfully",
        code=status.HTTP_201_CREATED,
    ).model_dump()


# ============================================================================
# UPDATE TRIGGER
# ============================================================================

@router.put(
    "/{workspace_id}/triggers/{trigger_id}",
    summary="Update trigger",
    description="Update an existing trigger",
    status_code=status.HTTP_200_OK,
)
async def update_trigger(
    request: Request,
    workspace_id: str = Depends(validate_workspace_member),
    trigger_id: str = Path(..., description="Trigger ID"),
    body: UpdateTriggerRequest = ...,
    current_user: AuthUser = Depends(authenticate_user),
    trigger_service: TriggerService = Depends(get_trigger_service),
) -> Dict[str, Any]:
    """
    Update an existing trigger.
    
    - **workspace_id**: Workspace ID (path parameter)
    - **trigger_id**: Trigger ID (path parameter)
    - **name**: Trigger name (request body, optional, must be unique in workspace if changed)
    - **description**: Trigger description (request body, optional)
    - **trigger_type**: Trigger type (request body, optional)
        - Supported values: MANUAL, SCHEDULED, WEBHOOK, EVENT
    - **config**: Trigger configuration (request body, optional, JSON object)
    - **input_mapping**: Input mapping rules (request body, optional)
        - Format: {VARIABLE_NAME: {type: str, value: Any}}
    - **is_enabled**: Whether the trigger is enabled (request body, optional)
    
    Requires workspace membership.
    The authenticated user will be recorded as the updater.
    """
    result = trigger_service.update_trigger(
        trigger_id=trigger_id,
        workspace_id=workspace_id,
        name=body.name,
        description=body.description,
        trigger_type=body.trigger_type,
        config=body.config,
        input_mapping=body.input_mapping,
        is_enabled=body.is_enabled,
        updated_by=current_user["user_id"],
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="Trigger updated successfully",
        code=status.HTTP_200_OK,
    ).model_dump()


# ============================================================================
# DELETE TRIGGER
# ============================================================================

@router.delete(
    "/{workspace_id}/triggers/{trigger_id}",
    summary="Delete trigger",
    description="Delete a trigger",
    status_code=status.HTTP_200_OK,
)
async def delete_trigger(
    request: Request,
    workspace_id: str = Depends(validate_workspace_member),
    trigger_id: str = Path(..., description="Trigger ID"),
    trigger_service: TriggerService = Depends(get_trigger_service),
) -> Dict[str, Any]:
    """
    Delete a trigger.
    
    - **workspace_id**: Workspace ID (path parameter)
    - **trigger_id**: Trigger ID (path parameter)
    
    Requires workspace membership.
    Permanently deletes the trigger.
    """
    result = trigger_service.delete_trigger(
        trigger_id=trigger_id,
        workspace_id=workspace_id,
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="Trigger deleted successfully",
        code=status.HTTP_200_OK,
    ).model_dump()

