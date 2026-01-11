"""Workspace plan routes for frontend."""

from fastapi import APIRouter, Request, Depends

from miniflow.server.dependencies import (
    get_workspace_plan_service,
)
from miniflow.server.schemas.base_schemas import create_success_response
from .schemas.workspace_plan_schemas import (
    WorkspacePlanResponse,
    WorkspacePlanListResponse,
    WorkspaceLimitsResponse,
    MonthlyLimitsResponse,
    FeatureFlagsResponse,
    ApiLimitsResponse,
    PricingResponse,
    AllApiRateLimitsResponse,
)

router = APIRouter(prefix="/workspace-plans", tags=["Workspace Plans"])


def _standardize_plan_dict(data: dict) -> dict:
    """Standardize plan dict: record_id -> id."""
    standardized = data.copy()
    if "record_id" in standardized:
        standardized["id"] = standardized.pop("record_id")
    if "id" not in standardized and "plan_id" in standardized:
        standardized["id"] = standardized.pop("plan_id")
    return standardized


@router.get("", response_model_exclude_none=True)
async def get_all_workspace_plans(
    request: Request,
    service = Depends(get_workspace_plan_service),
) -> dict:
    """
    Get all workspace plans.
    
    Public endpoint - no authentication required.
    """
    plans = service.get_all_workspace_plans()
    standardized = [_standardize_plan_dict(plan) for plan in plans]
    response_data = WorkspacePlanListResponse(items=[WorkspacePlanResponse.from_dict(plan) for plan in standardized])
    return create_success_response(request, data=response_data.model_dump())


@router.get("/{plan_id}", response_model_exclude_none=True)
async def get_workspace_plan_by_id(
    request: Request,
    plan_id: str,
    service = Depends(get_workspace_plan_service),
) -> dict:
    """
    Get workspace plan by ID.
    
    Public endpoint - no authentication required.
    """
    plan = service.get_workspace_plan_by_id(plan_id=plan_id)
    standardized = _standardize_plan_dict(plan)
    response_data = WorkspacePlanResponse.from_dict(standardized)
    return create_success_response(request, data=response_data.model_dump())


@router.get("/name/{plan_name}", response_model_exclude_none=True)
async def get_workspace_plan_by_name(
    request: Request,
    plan_name: str,
    service = Depends(get_workspace_plan_service),
) -> dict:
    """
    Get workspace plan by name.
    
    Public endpoint - no authentication required.
    """
    plan = service.get_workspace_plan_by_name(plan_name=plan_name)
    standardized = _standardize_plan_dict(plan)
    response_data = WorkspacePlanResponse.from_dict(standardized)
    return create_success_response(request, data=response_data.model_dump())


@router.get("/{plan_id}/limits", response_model_exclude_none=True)
async def get_workspace_limits(
    request: Request,
    plan_id: str,
    service = Depends(get_workspace_plan_service),
) -> dict:
    """
    Get workspace limits for a plan.
    
    Public endpoint - no authentication required.
    """
    limits = service.get_workspace_limits(plan_id=plan_id)
    response_data = WorkspaceLimitsResponse(plan_id=plan_id, **limits)
    return create_success_response(request, data=response_data.model_dump())


@router.get("/{plan_id}/monthly-limits", response_model_exclude_none=True)
async def get_monthly_limits(
    request: Request,
    plan_id: str,
    service = Depends(get_workspace_plan_service),
) -> dict:
    """
    Get monthly execution limits for a plan.
    
    Public endpoint - no authentication required.
    """
    limits = service.get_monthly_limits(plan_id=plan_id)
    response_data = MonthlyLimitsResponse(plan_id=plan_id, **limits)
    return create_success_response(request, data=response_data.model_dump())


@router.get("/{plan_id}/features", response_model_exclude_none=True)
async def get_feature_flags(
    request: Request,
    plan_id: str,
    service = Depends(get_workspace_plan_service),
) -> dict:
    """
    Get feature flags for a plan.
    
    Public endpoint - no authentication required.
    """
    features = service.get_feature_flags(plan_id=plan_id)
    response_data = FeatureFlagsResponse(plan_id=plan_id, **features)
    return create_success_response(request, data=response_data.model_dump())


@router.get("/{plan_id}/api-limits", response_model_exclude_none=True)
async def get_api_limits(
    request: Request,
    plan_id: str,
    service = Depends(get_workspace_plan_service),
) -> dict:
    """
    Get API rate limits for a plan.
    
    Public endpoint - no authentication required.
    """
    limits = service.get_api_limits(plan_id=plan_id)
    response_data = ApiLimitsResponse(plan_id=plan_id, **limits)
    return create_success_response(request, data=response_data.model_dump())


@router.get("/{plan_id}/pricing", response_model_exclude_none=True)
async def get_pricing(
    request: Request,
    plan_id: str,
    service = Depends(get_workspace_plan_service),
) -> dict:
    """
    Get pricing information for a plan.
    
    Public endpoint - no authentication required.
    """
    pricing = service.get_pricing(plan_id=plan_id)
    response_data = PricingResponse(plan_id=plan_id, **pricing)
    return create_success_response(request, data=response_data.model_dump())


@router.get("/api-rate-limits/all", response_model_exclude_none=True)
async def get_all_api_rate_limits(
    request: Request,
    service = Depends(get_workspace_plan_service),
) -> dict:
    """
    Get all API rate limits for all plans.
    
    Public endpoint - no authentication required.
    """
    limits = service.get_all_api_rate_limits()
    response_data = AllApiRateLimitsResponse(limits=limits)
    return create_success_response(request, data=response_data.model_dump())

