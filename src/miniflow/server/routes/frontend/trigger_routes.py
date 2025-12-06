"""Trigger routes for frontend."""

from typing import Optional
from fastapi import APIRouter, Request, Depends, Path, Query

from miniflow.server.dependencies import (
    get_trigger_service,
    authenticate_user,
    require_workspace_access,
)
from miniflow.server.dependencies.auth import AuthenticatedUser
from miniflow.server.schemas.base_schemas import create_success_response
from miniflow.models.enums import TriggerType
from .schemas.trigger_schemas import (
    CreateTriggerRequest,
    CreateTriggerResponse,
    TriggerResponse,
    WorkspaceTriggersResponse,
    WorkflowTriggersResponse,
    UpdateTriggerRequest,
    EnableTriggerResponse,
    DisableTriggerResponse,
    DeleteTriggerResponse,
    TriggerLimitsResponse,
)

router = APIRouter(prefix="/workspaces", tags=["Triggers"])


# ============================================================================
# CREATE TRIGGER ENDPOINTS
# ============================================================================

@router.post("/{workspace_id}/workflows/{workflow_id}/triggers", response_model_exclude_none=True)
async def create_trigger(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    workflow_id: str = Path(..., description="Workflow ID"),
    trigger_data: CreateTriggerRequest = ...,
    service = Depends(get_trigger_service),
    current_user: AuthenticatedUser = Depends(authenticate_user),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Create a new trigger.
    
    Requires: Workspace access
    Note: Trigger limit per workflow is enforced. SCHEDULED triggers require 'cron_expression' in config.
    """
    try:
        trigger_type = TriggerType(trigger_data.trigger_type.upper())
    except ValueError:
        from miniflow.core.exceptions import InvalidInputError
        raise InvalidInputError(
            field_name="trigger_type",
            message=f"Invalid trigger type. Valid types: {', '.join([tt.value for tt in TriggerType])}"
        )
    
    result = service.create_trigger(
        workspace_id=workspace_id,
        workflow_id=workflow_id,
        name=trigger_data.name,
        trigger_type=trigger_type,
        config=trigger_data.config,
        created_by=current_user["user_id"],
        description=trigger_data.description,
        input_mapping=trigger_data.input_mapping,
        is_enabled=trigger_data.is_enabled
    )
    
    response_data = CreateTriggerResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Trigger created successfully."
    )


# ============================================================================
# GET TRIGGER ENDPOINTS
# ============================================================================

@router.get("/{workspace_id}/workflows/{workflow_id}/triggers/{trigger_id}", response_model_exclude_none=True)
async def get_trigger(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    workflow_id: str = Path(..., description="Workflow ID"),
    trigger_id: str = Path(..., description="Trigger ID"),
    service = Depends(get_trigger_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Get trigger details.
    
    Requires: Workspace access
    """
    result = service.get_trigger(
        trigger_id=trigger_id
    )
    
    response_data = TriggerResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump()
    )


@router.get("/{workspace_id}/triggers", response_model_exclude_none=True)
async def get_workspace_triggers(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    trigger_type: Optional[str] = Query(None, description="Filter by trigger type"),
    is_enabled: Optional[bool] = Query(None, description="Filter by enabled status"),
    service = Depends(get_trigger_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Get all workspace triggers.
    
    Requires: Workspace access
    """
    tr_type = None
    if trigger_type:
        try:
            tr_type = TriggerType(trigger_type.upper())
        except ValueError:
            pass
    
    result = service.get_workspace_triggers(
        workspace_id=workspace_id,
        trigger_type=tr_type,
        is_enabled=is_enabled
    )
    
    response_data = WorkspaceTriggersResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump()
    )


@router.get("/{workspace_id}/workflows/{workflow_id}/triggers", response_model_exclude_none=True)
async def get_workflow_triggers(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    workflow_id: str = Path(..., description="Workflow ID"),
    service = Depends(get_trigger_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Get all workflow triggers.
    
    Requires: Workspace access
    """
    result = service.get_workflow_triggers(
        workflow_id=workflow_id
    )
    
    response_data = WorkflowTriggersResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump()
    )


@router.get("/triggers/limits", response_model_exclude_none=True)
async def get_trigger_limits(
    request: Request,
    service = Depends(get_trigger_service),
) -> dict:
    """
    Get trigger limits information.
    
    Public endpoint - no authentication required.
    """
    result = service.get_trigger_limits()
    
    response_data = TriggerLimitsResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump()
    )


# ============================================================================
# UPDATE TRIGGER ENDPOINTS
# ============================================================================

@router.put("/{workspace_id}/workflows/{workflow_id}/triggers/{trigger_id}", response_model_exclude_none=True)
async def update_trigger(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    workflow_id: str = Path(..., description="Workflow ID"),
    trigger_id: str = Path(..., description="Trigger ID"),
    trigger_data: UpdateTriggerRequest = ...,
    service = Depends(get_trigger_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Update trigger information.
    
    Requires: Workspace access
    Note: Config validation is performed based on trigger type.
    """
    tr_type = None
    if trigger_data.trigger_type:
        try:
            tr_type = TriggerType(trigger_data.trigger_type.upper())
        except ValueError:
            from miniflow.core.exceptions import InvalidInputError
            raise InvalidInputError(
                field_name="trigger_type",
                message=f"Invalid trigger type. Valid types: {', '.join([tt.value for tt in TriggerType])}"
            )
    
    result = service.update_trigger(
        trigger_id=trigger_id,
        name=trigger_data.name,
        description=trigger_data.description,
        trigger_type=tr_type,
        config=trigger_data.config,
        input_mapping=trigger_data.input_mapping
    )
    
    response_data = TriggerResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Trigger updated successfully."
    )


# ============================================================================
# ENABLE/DISABLE TRIGGER ENDPOINTS
# ============================================================================

@router.post("/{workspace_id}/workflows/{workflow_id}/triggers/{trigger_id}/enable", response_model_exclude_none=True)
async def enable_trigger(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    workflow_id: str = Path(..., description="Workflow ID"),
    trigger_id: str = Path(..., description="Trigger ID"),
    service = Depends(get_trigger_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Enable trigger.
    
    Requires: Workspace access
    """
    result = service.enable_trigger(
        trigger_id=trigger_id
    )
    
    response_data = EnableTriggerResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Trigger enabled successfully."
    )


@router.post("/{workspace_id}/workflows/{workflow_id}/triggers/{trigger_id}/disable", response_model_exclude_none=True)
async def disable_trigger(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    workflow_id: str = Path(..., description="Workflow ID"),
    trigger_id: str = Path(..., description="Trigger ID"),
    service = Depends(get_trigger_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Disable trigger.
    
    Requires: Workspace access
    """
    result = service.disable_trigger(
        trigger_id=trigger_id
    )
    
    response_data = DisableTriggerResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Trigger disabled successfully."
    )


# ============================================================================
# DELETE TRIGGER ENDPOINTS
# ============================================================================

@router.delete("/{workspace_id}/workflows/{workflow_id}/triggers/{trigger_id}", response_model_exclude_none=True)
async def delete_trigger(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    workflow_id: str = Path(..., description="Workflow ID"),
    trigger_id: str = Path(..., description="Trigger ID"),
    service = Depends(get_trigger_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Delete trigger.
    
    Requires: Workspace access
    Note: DEFAULT trigger cannot be deleted. Minimum trigger count per workflow must be maintained.
    """
    result = service.delete_trigger(
        trigger_id=trigger_id
    )
    
    response_data = DeleteTriggerResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Trigger deleted successfully."
    )

