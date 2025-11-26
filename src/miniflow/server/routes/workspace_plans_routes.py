"""
Workspace Plans routes.

Handles workspace plan information and API limits.
"""
from fastapi import APIRouter, Depends, Request, status
from typing import Dict, Any

from src.miniflow.server.dependencies import get_workspace_plans_service
from src.miniflow.services import WorkspacePlansService
from src.miniflow.server.schemas.base_schema import create_success_response

router = APIRouter(prefix="/workspace-plans", tags=["workspace-plans"])


# ============================================================================
# GET API LIMITS
# ============================================================================

@router.get(
    "/api-limits",
    summary="Get API rate limits for all plans",
    description="Get API rate limits (per minute, hour, day) for all workspace plans",
    status_code=status.HTTP_200_OK,
)
async def get_api_limits(
    request: Request,
    workspace_plans_service: WorkspacePlansService = Depends(get_workspace_plans_service),
) -> Dict[str, Any]:
    """
    Get API rate limits for all workspace plans.
    
    Returns a dictionary mapping plan_id to their API rate limits.
    Public endpoint - no authentication required.
    
    Response format:
    {
        "plan_id": {
            "limits": {
                "minute": int,
                "hour": int,
                "day": int
            }
        }
    }
    """
    result = workspace_plans_service.get_api_limits()
    
    return create_success_response(
        request=request,
        data=result,
        message="API limits retrieved successfully",
        code=status.HTTP_200_OK,
    ).model_dump()

