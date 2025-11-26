"""
Edge management routes.

Handles edge creation, retrieval, update, and deletion for workflows.
Edges represent connections between nodes in a workflow graph.
"""
from fastapi import APIRouter, Depends, Request, status, Path, Query
from typing import Dict, Any, Optional

from src.miniflow.server.dependencies import get_edge_service
from src.miniflow.services import EdgeService
from src.miniflow.server.helpers import (
    validate_workspace_member,
    authenticate_user,
    AuthUser,
)
from src.miniflow.server.schemas.base_schema import create_success_response
from src.miniflow.server.schemas.routes.workflow_schemas.edge_schemas import (
    CreateEdgeRequest,
    UpdateEdgeRequest,
)

router = APIRouter(prefix="/workspaces", tags=["edges"])


# ============================================================================
# GET ALL EDGES
# ============================================================================

@router.get(
    "/{workspace_id}/workflows/{workflow_id}/edges",
    summary="Get all edges",
    description="Get all edges for a workflow with pagination and filtering",
    status_code=status.HTTP_200_OK,
)
async def get_all_edges(
    request: Request,
    workspace_id: str = Depends(validate_workspace_member),
    workflow_id: str = Path(..., description="Workflow ID"),
    page: int = Query(1, ge=1, description="Page number (starts from 1)"),
    page_size: int = Query(100, ge=1, le=1000, description="Number of items per page (1-1000)"),
    order_by: Optional[str] = Query(None, description="Field to order by (default: created_at)"),
    order_desc: bool = Query(False, description="Order descending (default: False)"),
    include_deleted: bool = Query(False, description="Include deleted edges"),
    from_node_id: Optional[str] = Query(None, description="Filter by source node ID"),
    to_node_id: Optional[str] = Query(None, description="Filter by target node ID"),
    edge_service: EdgeService = Depends(get_edge_service),
) -> Dict[str, Any]:
    """
    Get all edges for a workflow with pagination and filtering.
    
    - **workspace_id**: Workspace ID (path parameter)
    - **workflow_id**: Workflow ID (path parameter)
    - **page**: Page number (query parameter, default: 1, min: 1)
    - **page_size**: Number of items per page (query parameter, default: 100, min: 1, max: 1000)
    - **order_by**: Field to order by (query parameter, optional, default: created_at)
    - **order_desc**: Order descending (query parameter, default: False)
    - **include_deleted**: Include deleted edges (query parameter, default: False)
    - **from_node_id**: Filter by source node ID (query parameter, optional)
    - **to_node_id**: Filter by target node ID (query parameter, optional)
    
    Requires workspace membership.
    Returns paginated list of edges.
    """
    result = edge_service.get_all_edges(
        workflow_id=workflow_id,
        page=page,
        page_size=page_size,
        order_by=order_by,
        order_desc=order_desc,
        include_deleted=include_deleted,
        from_node_id=from_node_id,
        to_node_id=to_node_id,
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="Edges retrieved successfully",
        code=status.HTTP_200_OK,
    ).model_dump()


# ============================================================================
# GET EDGE
# ============================================================================

@router.get(
    "/{workspace_id}/workflows/{workflow_id}/edges/{edge_id}",
    summary="Get edge",
    description="Get detailed information about a specific edge",
    status_code=status.HTTP_200_OK,
)
async def get_edge(
    request: Request,
    workspace_id: str = Depends(validate_workspace_member),
    workflow_id: str = Path(..., description="Workflow ID"),
    edge_id: str = Path(..., description="Edge ID"),
    edge_service: EdgeService = Depends(get_edge_service),
) -> Dict[str, Any]:
    """
    Get detailed information about a specific edge.
    
    - **workspace_id**: Workspace ID (path parameter)
    - **workflow_id**: Workflow ID (path parameter)
    - **edge_id**: Edge ID (path parameter)
    
    Requires workspace membership.
    Returns edge information including source and target node IDs.
    """
    result = edge_service.get_edge(
        edge_id=edge_id,
        workflow_id=workflow_id,
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="Edge retrieved successfully",
        code=status.HTTP_200_OK,
    ).model_dump()


# ============================================================================
# CREATE EDGE
# ============================================================================

@router.post(
    "/{workspace_id}/workflows/{workflow_id}/edges",
    summary="Create edge",
    description="Create a new edge connecting two nodes in a workflow",
    status_code=status.HTTP_201_CREATED,
)
async def create_edge(
    request: Request,
    workspace_id: str = Depends(validate_workspace_member),
    workflow_id: str = Path(..., description="Workflow ID"),
    body: CreateEdgeRequest = ...,
    current_user: AuthUser = Depends(authenticate_user),
    edge_service: EdgeService = Depends(get_edge_service),
) -> Dict[str, Any]:
    """
    Create a new edge connecting two nodes in a workflow.
    
    - **workspace_id**: Workspace ID (path parameter)
    - **workflow_id**: Workflow ID (path parameter)
    - **from_node_id**: Source node ID (request body, required, must belong to the workflow)
    - **to_node_id**: Target node ID (request body, required, must belong to the workflow)
    
    Requires workspace membership.
    The authenticated user will be recorded as the creator.
    Both nodes must belong to the specified workflow.
    Edge cannot connect a node to itself (self-loop prevention).
    Edge must be unique between the two nodes (duplicate prevention).
    """
    result = edge_service.create_edge(
        workflow_id=workflow_id,
        from_node_id=body.from_node_id,
        to_node_id=body.to_node_id,
        created_by=current_user["user_id"],
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="Edge created successfully",
        code=status.HTTP_201_CREATED,
    ).model_dump()


# ============================================================================
# UPDATE EDGE
# ============================================================================

@router.put(
    "/{workspace_id}/workflows/{workflow_id}/edges/{edge_id}",
    summary="Update edge",
    description="Update an existing edge",
    status_code=status.HTTP_200_OK,
)
async def update_edge(
    request: Request,
    workspace_id: str = Depends(validate_workspace_member),
    workflow_id: str = Path(..., description="Workflow ID"),
    edge_id: str = Path(..., description="Edge ID"),
    body: UpdateEdgeRequest = ...,
    current_user: AuthUser = Depends(authenticate_user),
    edge_service: EdgeService = Depends(get_edge_service),
) -> Dict[str, Any]:
    """
    Update an existing edge.
    
    - **workspace_id**: Workspace ID (path parameter)
    - **workflow_id**: Workflow ID (path parameter)
    - **edge_id**: Edge ID (path parameter)
    - **from_node_id**: Source node ID (request body, optional, must belong to the workflow)
    - **to_node_id**: Target node ID (request body, optional, must belong to the workflow)
    
    Requires workspace membership.
    The authenticated user will be recorded as the updater.
    Both nodes must belong to the specified workflow.
    Edge cannot connect a node to itself (self-loop prevention).
    Updated edge must be unique between the two nodes (duplicate prevention).
    """
    result = edge_service.update_edge(
        edge_id=edge_id,
        workflow_id=workflow_id,
        from_node_id=body.from_node_id,
        to_node_id=body.to_node_id,
        updated_by=current_user["user_id"],
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="Edge updated successfully",
        code=status.HTTP_200_OK,
    ).model_dump()


# ============================================================================
# DELETE EDGE
# ============================================================================

@router.delete(
    "/{workspace_id}/workflows/{workflow_id}/edges/{edge_id}",
    summary="Delete edge",
    description="Delete an edge",
    status_code=status.HTTP_200_OK,
)
async def delete_edge(
    request: Request,
    workspace_id: str = Depends(validate_workspace_member),
    workflow_id: str = Path(..., description="Workflow ID"),
    edge_id: str = Path(..., description="Edge ID"),
    edge_service: EdgeService = Depends(get_edge_service),
) -> Dict[str, Any]:
    """
    Delete an edge.
    
    - **workspace_id**: Workspace ID (path parameter)
    - **workflow_id**: Workflow ID (path parameter)
    - **edge_id**: Edge ID (path parameter)
    
    Requires workspace membership.
    Permanently deletes the edge connection between nodes.
    """
    result = edge_service.delete_edge(
        edge_id=edge_id,
        workflow_id=workflow_id,
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="Edge deleted successfully",
        code=status.HTTP_200_OK,
    ).model_dump()

