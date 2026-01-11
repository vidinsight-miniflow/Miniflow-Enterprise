"""Node routes for frontend."""

from fastapi import APIRouter, Request, Depends, Path

from miniflow.server.dependencies import (
    get_node_service,
    authenticate_user,
    require_workspace_access,
)
from miniflow.server.dependencies.auth import AuthenticatedUser
from miniflow.server.schemas.base_schemas import create_success_response
from .schemas.node_schemas import (
    CreateNodeRequest,
    CreateNodeResponse,
    NodeResponse,
    NodeFormSchemaResponse,
    WorkflowNodesResponse,
    UpdateNodeRequest,
    UpdateNodeInputParamsRequest,
    SyncInputSchemaValuesRequest,
    ResetInputParamsResponse,
    DeleteNodeResponse,
)

router = APIRouter(prefix="/workspaces", tags=["Nodes"])


# ============================================================================
# CREATE NODE ENDPOINTS
# ============================================================================

@router.post("/{workspace_id}/workflows/{workflow_id}/nodes", response_model_exclude_none=True)
async def create_node(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    workflow_id: str = Path(..., description="Workflow ID"),
    node_data: CreateNodeRequest = ...,
    service = Depends(get_node_service),
    current_user: AuthenticatedUser = Depends(authenticate_user),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Create a new node.
    
    Requires: Workspace access
    Note: Either script_id or custom_script_id must be provided (XOR). Input params are validated against script's input_schema.
    """
    result = service.create_node(
        workflow_id=workflow_id,
        name=node_data.name,
        created_by=current_user["user_id"],
        script_id=node_data.script_id,
        custom_script_id=node_data.custom_script_id,
        description=node_data.description,
        input_params=node_data.input_params,
        output_params=node_data.output_params,
        meta_data=node_data.meta_data,
        max_retries=node_data.max_retries,
        timeout_seconds=node_data.timeout_seconds
    )
    
    response_data = CreateNodeResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Node created successfully."
    )


# ============================================================================
# GET NODE ENDPOINTS
# ============================================================================

@router.get("/{workspace_id}/workflows/{workflow_id}/nodes/{node_id}", response_model_exclude_none=True)
async def get_node(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    workflow_id: str = Path(..., description="Workflow ID"),
    node_id: str = Path(..., description="Node ID"),
    service = Depends(get_node_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Get node details.
    
    Requires: Workspace access
    """
    result = service.get_node(
        node_id=node_id
    )
    
    response_data = NodeResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump()
    )


@router.get("/{workspace_id}/workflows/{workflow_id}/nodes/{node_id}/form-schema", response_model_exclude_none=True)
async def get_node_form_schema(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    workflow_id: str = Path(..., description="Workflow ID"),
    node_id: str = Path(..., description="Node ID"),
    service = Depends(get_node_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Get node form schema for frontend.
    
    Requires: Workspace access
    Note: Returns script's input_schema converted to frontend format.
    """
    result = service.get_node_form_schema(
        node_id=node_id
    )
    
    response_data = NodeFormSchemaResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump()
    )


@router.get("/{workspace_id}/workflows/{workflow_id}/nodes", response_model_exclude_none=True)
async def get_workflow_nodes(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    workflow_id: str = Path(..., description="Workflow ID"),
    service = Depends(get_node_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Get all workflow nodes.
    
    Requires: Workspace access
    """
    result = service.get_workflow_nodes(
        workflow_id=workflow_id
    )
    
    response_data = WorkflowNodesResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump()
    )


# ============================================================================
# UPDATE NODE ENDPOINTS
# ============================================================================

@router.put("/{workspace_id}/workflows/{workflow_id}/nodes/{node_id}", response_model_exclude_none=True)
async def update_node(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    workflow_id: str = Path(..., description="Workflow ID"),
    node_id: str = Path(..., description="Node ID"),
    node_data: UpdateNodeRequest = ...,
    service = Depends(get_node_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Update node information.
    
    Requires: Workspace access
    Note: If script is changed, input_params may be reset.
    """
    result = service.update_node(
        node_id=node_id,
        name=node_data.name,
        description=node_data.description,
        script_id=node_data.script_id,
        custom_script_id=node_data.custom_script_id,
        meta_data=node_data.meta_data,
        max_retries=node_data.max_retries,
        timeout_seconds=node_data.timeout_seconds
    )
    
    response_data = NodeResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Node updated successfully."
    )


@router.put("/{workspace_id}/workflows/{workflow_id}/nodes/{node_id}/input-params", response_model_exclude_none=True)
async def update_node_input_params(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    workflow_id: str = Path(..., description="Workflow ID"),
    node_id: str = Path(..., description="Node ID"),
    params_data: UpdateNodeInputParamsRequest = ...,
    service = Depends(get_node_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Update node input parameters.
    
    Requires: Workspace access
    Note: Input params are validated against script's input_schema.
    """
    result = service.update_node_input_params(
        node_id=node_id,
        input_params=params_data.input_params
    )
    
    response_data = NodeResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Node input parameters updated successfully."
    )


@router.put("/{workspace_id}/workflows/{workflow_id}/nodes/{node_id}/sync-input-values", response_model_exclude_none=True)
async def sync_input_schema_values(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    workflow_id: str = Path(..., description="Workflow ID"),
    node_id: str = Path(..., description="Node ID"),
    sync_data: SyncInputSchemaValuesRequest = ...,
    service = Depends(get_node_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Sync input schema values from frontend.
    
    Requires: Workspace access
    Note: Syncs all parameter values, using defaults for missing values.
    """
    result = service.sync_input_schema_values(
        node_id=node_id,
        values=sync_data.values
    )
    
    response_data = NodeResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Input schema values synced successfully."
    )


@router.post("/{workspace_id}/workflows/{workflow_id}/nodes/{node_id}/reset-input-params", response_model_exclude_none=True)
async def reset_input_params_to_defaults(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    workflow_id: str = Path(..., description="Workflow ID"),
    node_id: str = Path(..., description="Node ID"),
    service = Depends(get_node_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Reset input parameters to script defaults.
    
    Requires: Workspace access
    """
    result = service.reset_input_params_to_defaults(
        node_id=node_id
    )
    
    response_data = NodeResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Input parameters reset to defaults successfully."
    )


# ============================================================================
# DELETE NODE ENDPOINTS
# ============================================================================

@router.delete("/{workspace_id}/workflows/{workflow_id}/nodes/{node_id}", response_model_exclude_none=True)
async def delete_node(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    workflow_id: str = Path(..., description="Workflow ID"),
    node_id: str = Path(..., description="Node ID"),
    service = Depends(get_node_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Delete node.
    
    Requires: Workspace access
    Note: Connected edges will be deleted (cascade).
    """
    result = service.delete_node(
        node_id=node_id
    )
    
    response_data = DeleteNodeResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Node deleted successfully."
    )

