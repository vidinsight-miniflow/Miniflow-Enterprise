"""Edge routes for frontend."""

from fastapi import APIRouter, Request, Depends, Path

from miniflow.server.dependencies import (
    get_edge_service,
    authenticate_user,
    require_workspace_access,
)
from miniflow.server.dependencies.auth import AuthenticatedUser
from miniflow.server.schemas.base_schemas import create_success_response
from .schemas.edge_schemas import (
    CreateEdgeRequest,
    CreateEdgeResponse,
    EdgeResponse,
    WorkflowEdgesResponse,
    OutgoingEdgesResponse,
    IncomingEdgesResponse,
    UpdateEdgeRequest,
    DeleteEdgeResponse,
)

router = APIRouter(prefix="/workspaces", tags=["Edges"])


# ============================================================================
# CREATE EDGE ENDPOINTS
# ============================================================================

@router.post("/{workspace_id}/workflows/{workflow_id}/edges", response_model_exclude_none=True)
async def create_edge(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    workflow_id: str = Path(..., description="Workflow ID"),
    edge_data: CreateEdgeRequest = ...,
    service = Depends(get_edge_service),
    current_user: AuthenticatedUser = Depends(authenticate_user),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Create a new edge (connection between nodes).
    
    Requires: Workspace access
    Note: Self-loops are not allowed. Both nodes must belong to the same workflow.
    """
    result = service.create_edge(
        workflow_id=workflow_id,
        from_node_id=edge_data.from_node_id,
        to_node_id=edge_data.to_node_id,
        created_by=current_user["user_id"]
    )
    
    response_data = CreateEdgeResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Edge created successfully."
    )


# ============================================================================
# GET EDGE ENDPOINTS
# ============================================================================

@router.get("/{workspace_id}/workflows/{workflow_id}/edges/{edge_id}", response_model_exclude_none=True)
async def get_edge(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    workflow_id: str = Path(..., description="Workflow ID"),
    edge_id: str = Path(..., description="Edge ID"),
    service = Depends(get_edge_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Get edge details.
    
    Requires: Workspace access
    """
    result = service.get_edge(
        edge_id=edge_id
    )
    
    response_data = EdgeResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump()
    )


@router.get("/{workspace_id}/workflows/{workflow_id}/edges", response_model_exclude_none=True)
async def get_workflow_edges(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    workflow_id: str = Path(..., description="Workflow ID"),
    service = Depends(get_edge_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Get all workflow edges.
    
    Requires: Workspace access
    """
    result = service.get_workflow_edges(
        workflow_id=workflow_id
    )
    
    response_data = WorkflowEdgesResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump()
    )


@router.get("/{workspace_id}/workflows/{workflow_id}/nodes/{node_id}/outgoing-edges", response_model_exclude_none=True)
async def get_outgoing_edges(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    workflow_id: str = Path(..., description="Workflow ID"),
    node_id: str = Path(..., description="Node ID"),
    service = Depends(get_edge_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Get outgoing edges from a node.
    
    Requires: Workspace access
    """
    result = service.get_outgoing_edges(
        workflow_id=workflow_id,
        node_id=node_id
    )
    
    response_data = OutgoingEdgesResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump()
    )


@router.get("/{workspace_id}/workflows/{workflow_id}/nodes/{node_id}/incoming-edges", response_model_exclude_none=True)
async def get_incoming_edges(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    workflow_id: str = Path(..., description="Workflow ID"),
    node_id: str = Path(..., description="Node ID"),
    service = Depends(get_edge_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Get incoming edges to a node.
    
    Requires: Workspace access
    """
    result = service.get_incoming_edges(
        workflow_id=workflow_id,
        node_id=node_id
    )
    
    response_data = IncomingEdgesResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump()
    )


# ============================================================================
# UPDATE EDGE ENDPOINTS
# ============================================================================

@router.put("/{workspace_id}/workflows/{workflow_id}/edges/{edge_id}", response_model_exclude_none=True)
async def update_edge(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    workflow_id: str = Path(..., description="Workflow ID"),
    edge_id: str = Path(..., description="Edge ID"),
    edge_data: UpdateEdgeRequest = ...,
    service = Depends(get_edge_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Update edge (change node connections).
    
    Requires: Workspace access
    Note: Self-loops are not allowed.
    """
    result = service.update_edge(
        edge_id=edge_id,
        from_node_id=edge_data.from_node_id,
        to_node_id=edge_data.to_node_id
    )
    
    response_data = EdgeResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Edge updated successfully."
    )


# ============================================================================
# DELETE EDGE ENDPOINTS
# ============================================================================

@router.delete("/{workspace_id}/workflows/{workflow_id}/edges/{edge_id}", response_model_exclude_none=True)
async def delete_edge(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    workflow_id: str = Path(..., description="Workflow ID"),
    edge_id: str = Path(..., description="Edge ID"),
    service = Depends(get_edge_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Delete edge.
    
    Requires: Workspace access
    """
    result = service.delete_edge(
        edge_id=edge_id
    )
    
    response_data = DeleteEdgeResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Edge deleted successfully."
    )

