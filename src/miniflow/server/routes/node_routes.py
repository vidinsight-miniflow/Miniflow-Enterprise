"""
Node management routes.

Handles node creation, retrieval, update, and deletion for workflows.
Nodes represent executable steps in a workflow and can use global or custom scripts.
"""
from fastapi import APIRouter, Depends, Request, status, Path, Query
from typing import Dict, Any, Optional

from src.miniflow.server.dependencies import get_node_service
from src.miniflow.services import NodeService
from src.miniflow.server.helpers import (
    validate_workspace_member,
    authenticate_user,
    AuthUser,
)
from src.miniflow.server.schemas.base_schema import create_success_response
from src.miniflow.server.schemas.routes.workflow_schemas.node_schemas import (
    CreateNodeRequest,
    UpdateNodeRequest,
    UpdateNodeInputParamsRequest,
)

router = APIRouter(prefix="/workspaces", tags=["nodes"])


# ============================================================================
# GET ALL NODES
# ============================================================================

@router.get(
    "/{workspace_id}/workflows/{workflow_id}/nodes",
    summary="Get all nodes",
    description="Get all nodes for a workflow with pagination",
    status_code=status.HTTP_200_OK,
)
async def get_all_nodes(
    request: Request,
    workspace_id: str = Depends(validate_workspace_member),
    workflow_id: str = Path(..., description="Workflow ID"),
    page: int = Query(1, ge=1, description="Page number (starts from 1)"),
    page_size: int = Query(100, ge=1, le=1000, description="Number of items per page (1-1000)"),
    order_by: Optional[str] = Query(None, description="Field to order by (default: created_at)"),
    order_desc: bool = Query(False, description="Order descending (default: False)"),
    include_deleted: bool = Query(False, description="Include deleted nodes"),
    node_service: NodeService = Depends(get_node_service),
) -> Dict[str, Any]:
    """
    Get all nodes for a workflow with pagination.
    
    - **workspace_id**: Workspace ID (path parameter)
    - **workflow_id**: Workflow ID (path parameter)
    - **page**: Page number (query parameter, default: 1, min: 1)
    - **page_size**: Number of items per page (query parameter, default: 100, min: 1, max: 1000)
    - **order_by**: Field to order by (query parameter, optional, default: created_at)
    - **order_desc**: Order descending (query parameter, default: False)
    - **include_deleted**: Include deleted nodes (query parameter, default: False)
    
    Requires workspace membership.
    Returns paginated list of nodes.
    """
    result = node_service.get_all_nodes(
        workflow_id=workflow_id,
        page=page,
        page_size=page_size,
        order_by=order_by,
        order_desc=order_desc,
        include_deleted=include_deleted,
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="Nodes retrieved successfully",
        code=status.HTTP_200_OK,
    ).model_dump()


# ============================================================================
# GET NODE
# ============================================================================

@router.get(
    "/{workspace_id}/workflows/{workflow_id}/nodes/{node_id}",
    summary="Get node",
    description="Get detailed information about a specific node",
    status_code=status.HTTP_200_OK,
)
async def get_node(
    request: Request,
    workspace_id: str = Depends(validate_workspace_member),
    workflow_id: str = Path(..., description="Workflow ID"),
    node_id: str = Path(..., description="Node ID"),
    node_service: NodeService = Depends(get_node_service),
) -> Dict[str, Any]:
    """
    Get detailed information about a specific node.
    
    - **workspace_id**: Workspace ID (path parameter)
    - **workflow_id**: Workflow ID (path parameter)
    - **node_id**: Node ID (path parameter)
    
    Requires workspace membership.
    Returns node information including script references and parameters.
    """
    result = node_service.get_node(
        node_id=node_id,
        workflow_id=workflow_id,
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="Node retrieved successfully",
        code=status.HTTP_200_OK,
    ).model_dump()


# ============================================================================
# GET NODE FORM SCHEMA
# ============================================================================

@router.get(
    "/{workspace_id}/workflows/{workflow_id}/nodes/{node_id}/form-schema",
    summary="Get node form schema",
    description="Get frontend form schema for a node based on script's input_schema",
    status_code=status.HTTP_200_OK,
)
async def get_node_form_schema(
    request: Request,
    workspace_id: str = Depends(validate_workspace_member),
    workflow_id: str = Path(..., description="Workflow ID"),
    node_id: str = Path(..., description="Node ID"),
    node_service: NodeService = Depends(get_node_service),
) -> Dict[str, Any]:
    """
    Get frontend form schema for a node.
    
    - **workspace_id**: Workspace ID (path parameter)
    - **workflow_id**: Workflow ID (path parameter)
    - **node_id**: Node ID (path parameter)
    
    Requires workspace membership.
    Returns frontend-formatted schema derived from script's input_schema,
    merged with node's existing input_params values.
    Used for building dynamic forms in the frontend.
    """
    result = node_service.get_node_form_schema(
        node_id=node_id,
        workflow_id=workflow_id,
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="Node form schema retrieved successfully",
        code=status.HTTP_200_OK,
    ).model_dump()


# ============================================================================
# CREATE NODE
# ============================================================================

@router.post(
    "/{workspace_id}/workflows/{workflow_id}/nodes",
    summary="Create node",
    description="Create a new node for a workflow",
    status_code=status.HTTP_201_CREATED,
)
async def create_node(
    request: Request,
    workspace_id: str = Depends(validate_workspace_member),
    workflow_id: str = Path(..., description="Workflow ID"),
    body: CreateNodeRequest = ...,
    current_user: AuthUser = Depends(authenticate_user),
    node_service: NodeService = Depends(get_node_service),
) -> Dict[str, Any]:
    """
    Create a new node for a workflow.
    
    - **workspace_id**: Workspace ID (path parameter)
    - **workflow_id**: Workflow ID (path parameter)
    - **name**: Node name (request body, required, must be unique in workflow)
    - **script_id**: Global script ID (request body, optional, either script_id or custom_script_id must be provided)
    - **custom_script_id**: Custom script ID (request body, optional, either script_id or custom_script_id must be provided)
    - **description**: Node description (request body, optional)
    - **input_params**: Input parameters (request body, optional, frontend format, validated against script's input_schema)
    - **output_params**: Output parameters (request body, optional)
    - **meta_data**: Metadata (request body, optional)
    - **max_retries**: Maximum retry attempts (request body, optional, default: 3, min: 0)
    - **timeout_seconds**: Timeout in seconds (request body, optional, default: 300, min: 1)
    
    Requires workspace membership.
    The authenticated user will be recorded as the creator.
    Exactly one of script_id or custom_script_id must be provided.
    If custom_script_id is used, it must belong to the same workspace as the workflow.
    Input parameters are validated against the script's input_schema.
    """
    result = node_service.create_node(
        workflow_id=workflow_id,
        name=body.name,
        script_id=body.script_id,
        custom_script_id=body.custom_script_id,
        description=body.description,
        input_params=body.input_params,
        output_params=body.output_params,
        meta_data=body.meta_data,
        max_retries=body.max_retries,
        timeout_seconds=body.timeout_seconds,
        created_by=current_user["user_id"],
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="Node created successfully",
        code=status.HTTP_201_CREATED,
    ).model_dump()


# ============================================================================
# UPDATE NODE
# ============================================================================

@router.put(
    "/{workspace_id}/workflows/{workflow_id}/nodes/{node_id}",
    summary="Update node",
    description="Update an existing node",
    status_code=status.HTTP_200_OK,
)
async def update_node(
    request: Request,
    workspace_id: str = Depends(validate_workspace_member),
    workflow_id: str = Path(..., description="Workflow ID"),
    node_id: str = Path(..., description="Node ID"),
    body: UpdateNodeRequest = ...,
    current_user: AuthUser = Depends(authenticate_user),
    node_service: NodeService = Depends(get_node_service),
) -> Dict[str, Any]:
    """
    Update an existing node.
    
    - **workspace_id**: Workspace ID (path parameter)
    - **workflow_id**: Workflow ID (path parameter)
    - **node_id**: Node ID (path parameter)
    - **name**: Node name (request body, optional, must be unique in workflow if changed)
    - **description**: Node description (request body, optional)
    - **script_id**: Global script ID (request body, optional)
    - **custom_script_id**: Custom script ID (request body, optional)
    - **input_params**: Input parameters (request body, optional, frontend format)
    - **output_params**: Output parameters (request body, optional)
    - **meta_data**: Metadata (request body, optional)
    - **max_retries**: Maximum retry attempts (request body, optional, min: 0)
    - **timeout_seconds**: Timeout in seconds (request body, optional, min: 1)
    
    Requires workspace membership.
    The authenticated user will be recorded as the updater.
    Exactly one of script_id or custom_script_id must remain after update.
    Input parameters are validated against the script's input_schema.
    """
    result = node_service.update_node(
        node_id=node_id,
        workflow_id=workflow_id,
        name=body.name,
        description=body.description,
        script_id=body.script_id,
        custom_script_id=body.custom_script_id,
        input_params=body.input_params,
        output_params=body.output_params,
        meta_data=body.meta_data,
        max_retries=body.max_retries,
        timeout_seconds=body.timeout_seconds,
        updated_by=current_user["user_id"],
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="Node updated successfully",
        code=status.HTTP_200_OK,
    ).model_dump()


# ============================================================================
# UPDATE NODE INPUT PARAMS
# ============================================================================

@router.patch(
    "/{workspace_id}/workflows/{workflow_id}/nodes/{node_id}/input-params",
    summary="Update node input parameters",
    description="Update only the input parameters of a node",
    status_code=status.HTTP_200_OK,
)
async def update_node_input_params(
    request: Request,
    workspace_id: str = Depends(validate_workspace_member),
    workflow_id: str = Path(..., description="Workflow ID"),
    node_id: str = Path(..., description="Node ID"),
    body: UpdateNodeInputParamsRequest = ...,
    current_user: AuthUser = Depends(authenticate_user),
    node_service: NodeService = Depends(get_node_service),
) -> Dict[str, Any]:
    """
    Update only the input parameters of a node.
    
    - **workspace_id**: Workspace ID (path parameter)
    - **workflow_id**: Workflow ID (path parameter)
    - **node_id**: Node ID (path parameter)
    - **input_params**: Input parameters (request body, required, frontend format, validated against script's input_schema)
    
    Requires workspace membership.
    The authenticated user will be recorded as the updater.
    This endpoint is optimized for updating only input parameters without affecting other node properties.
    Input parameters are validated against the script's input_schema.
    """
    result = node_service.update_node_input_params(
        node_id=node_id,
        workflow_id=workflow_id,
        input_params=body.input_params,
        updated_by=current_user["user_id"],
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="Node input parameters updated successfully",
        code=status.HTTP_200_OK,
    ).model_dump()


# ============================================================================
# DELETE NODE
# ============================================================================

@router.delete(
    "/{workspace_id}/workflows/{workflow_id}/nodes/{node_id}",
    summary="Delete node",
    description="Delete a node",
    status_code=status.HTTP_200_OK,
)
async def delete_node(
    request: Request,
    workspace_id: str = Depends(validate_workspace_member),
    workflow_id: str = Path(..., description="Workflow ID"),
    node_id: str = Path(..., description="Node ID"),
    node_service: NodeService = Depends(get_node_service),
) -> Dict[str, Any]:
    """
    Delete a node.
    
    - **workspace_id**: Workspace ID (path parameter)
    - **workflow_id**: Workflow ID (path parameter)
    - **node_id**: Node ID (path parameter)
    
    Requires workspace membership.
    Permanently deletes the node and all associated edges (CASCADE).
    """
    result = node_service.delete_node(
        node_id=node_id,
        workflow_id=workflow_id,
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="Node deleted successfully",
        code=status.HTTP_200_OK,
    ).model_dump()

