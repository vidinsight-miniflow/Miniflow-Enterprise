"""Workspace plan management routes for frontend."""

from fastapi import APIRouter, Request, Depends, Path, Query

from miniflow.server.dependencies import (
    get_workspace_plan_management_service,
    authenticate_user,
    require_workspace_access,
    require_workspace_owner,
)
from miniflow.server.dependencies.auth import AuthenticatedUser
from miniflow.server.schemas.base_schemas import create_success_response
from .schemas.workspace_plan_management_schemas import (
    AvailablePlansResponse,
    PlanDetailsResponse,
    WorkspaceCurrentPlanResponse,
    ComparePlansRequest,
    ComparePlansResponse,
    CheckUpgradeEligibilityRequest,
    CheckUpgradeEligibilityResponse,
    CheckDowngradeEligibilityRequest,
    CheckDowngradeEligibilityResponse,
    UpgradePlanRequest,
    UpgradePlanResponse,
    DowngradePlanRequest,
    DowngradePlanResponse,
    UpdateBillingInfoRequest,
    UpdateBillingInfoResponse,
    UpdateBillingPeriodRequest,
    UpdateBillingPeriodResponse,
    CheckLimitRequest,
    CheckLimitResponse,
)

router = APIRouter(prefix="/workspaces", tags=["Workspace Plans"])


# ============================================================================
# PLAN INFO ENDPOINTS
# ============================================================================

@router.get("/plans", response_model_exclude_none=True)
async def get_available_plans(
    request: Request,
    service = Depends(get_workspace_plan_management_service),
) -> dict:
    """
    Get all available plans.
    
    Public endpoint - no authentication required.
    """
    result = service.get_available_plans()
    
    response_data = AvailablePlansResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump()
    )


@router.get("/plans/{plan_id}", response_model_exclude_none=True)
async def get_plan_details(
    request: Request,
    plan_id: str = Path(..., description="Plan ID"),
    service = Depends(get_workspace_plan_management_service),
) -> dict:
    """
    Get plan details.
    
    Public endpoint - no authentication required.
    """
    result = service.get_plan_details(plan_id=plan_id)
    
    response_data = PlanDetailsResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump()
    )


@router.get("/{workspace_id}/plan", response_model_exclude_none=True)
async def get_workspace_current_plan(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    service = Depends(get_workspace_plan_management_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Get workspace current plan and usage.
    
    Requires: Workspace access
    """
    result = service.get_workspace_current_plan(workspace_id=workspace_id)
    
    response_data = WorkspaceCurrentPlanResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump()
    )


# ============================================================================
# COMPARE PLANS ENDPOINTS
# ============================================================================

@router.post("/plans/compare", response_model_exclude_none=True)
async def compare_plans(
    request: Request,
    compare_data: ComparePlansRequest,
    service = Depends(get_workspace_plan_management_service),
) -> dict:
    """
    Compare two plans.
    
    Public endpoint - no authentication required.
    """
    result = service.compare_plans(
        plan_id_1=compare_data.plan_id_1,
        plan_id_2=compare_data.plan_id_2
    )
    
    response_data = ComparePlansResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump()
    )


# ============================================================================
# UPGRADE/DOWNGRADE ELIGIBILITY ENDPOINTS
# ============================================================================

@router.post("/{workspace_id}/plan/check-upgrade", response_model_exclude_none=True)
async def check_upgrade_eligibility(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    eligibility_data: CheckUpgradeEligibilityRequest = ...,
    service = Depends(get_workspace_plan_management_service),
    _: str = Depends(require_workspace_owner),
) -> dict:
    """
    Check if workspace can upgrade to target plan.
    
    Requires: Workspace owner
    """
    result = service.check_upgrade_eligibility(
        workspace_id=workspace_id,
        target_plan_id=eligibility_data.target_plan_id
    )
    
    response_data = CheckUpgradeEligibilityResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump()
    )


@router.post("/{workspace_id}/plan/check-downgrade", response_model_exclude_none=True)
async def check_downgrade_eligibility(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    eligibility_data: CheckDowngradeEligibilityRequest = ...,
    service = Depends(get_workspace_plan_management_service),
    _: str = Depends(require_workspace_owner),
) -> dict:
    """
    Check if workspace can downgrade to target plan.
    
    Requires: Workspace owner
    """
    result = service.check_downgrade_eligibility(
        workspace_id=workspace_id,
        target_plan_id=eligibility_data.target_plan_id
    )
    
    response_data = CheckDowngradeEligibilityResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump()
    )


# ============================================================================
# UPGRADE/DOWNGRADE ENDPOINTS
# ============================================================================

@router.post("/{workspace_id}/plan/upgrade", response_model_exclude_none=True)
async def upgrade_plan(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    upgrade_data: UpgradePlanRequest = ...,
    service = Depends(get_workspace_plan_management_service),
    _: str = Depends(require_workspace_owner),
) -> dict:
    """
    Upgrade workspace plan.
    
    Requires: Workspace owner
    Note: Actual payment is handled via Stripe webhook.
    """
    result = service.upgrade_plan(
        workspace_id=workspace_id,
        target_plan_id=upgrade_data.target_plan_id,
        stripe_subscription_id=upgrade_data.stripe_subscription_id
    )
    
    response_data = UpgradePlanResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Plan upgraded successfully."
    )


@router.post("/{workspace_id}/plan/downgrade", response_model_exclude_none=True)
async def downgrade_plan(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    downgrade_data: DowngradePlanRequest = ...,
    service = Depends(get_workspace_plan_management_service),
    _: str = Depends(require_workspace_owner),
) -> dict:
    """
    Downgrade workspace plan.
    
    Requires: Workspace owner
    Note: Downgrade is usually applied at the end of billing period.
    """
    result = service.downgrade_plan(
        workspace_id=workspace_id,
        target_plan_id=downgrade_data.target_plan_id
    )
    
    response_data = DowngradePlanResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Plan downgrade scheduled."
    )


# ============================================================================
# BILLING ENDPOINTS
# ============================================================================

@router.put("/{workspace_id}/billing", response_model_exclude_none=True)
async def update_billing_info(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    billing_data: UpdateBillingInfoRequest = ...,
    service = Depends(get_workspace_plan_management_service),
    _: str = Depends(require_workspace_owner),
) -> dict:
    """
    Update workspace billing information.
    
    Requires: Workspace owner
    """
    from datetime import datetime
    result = service.update_billing_info(
        workspace_id=workspace_id,
        stripe_customer_id=billing_data.stripe_customer_id,
        stripe_subscription_id=billing_data.stripe_subscription_id,
        billing_email=billing_data.billing_email,
        billing_currency=billing_data.billing_currency
    )
    
    response_data = UpdateBillingInfoResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Billing information updated successfully."
    )


@router.post("/{workspace_id}/billing/period", response_model_exclude_none=True)
async def update_billing_period(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    period_data: UpdateBillingPeriodRequest = ...,
    service = Depends(get_workspace_plan_management_service),
    current_user: AuthenticatedUser = Depends(authenticate_user),
) -> dict:
    """
    Update billing period and reset monthly counters.
    
    Requires: Admin authentication (TODO: Add admin check)
    Note: Usually called by Stripe webhook.
    """
    from datetime import datetime
    result = service.update_billing_period(
        workspace_id=workspace_id,
        period_start=datetime.fromisoformat(period_data.period_start.replace('Z', '+00:00')),
        period_end=datetime.fromisoformat(period_data.period_end.replace('Z', '+00:00'))
    )
    
    response_data = UpdateBillingPeriodResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Billing period updated successfully."
    )


# ============================================================================
# LIMIT CHECK ENDPOINTS
# ============================================================================

@router.post("/{workspace_id}/limits/check", response_model_exclude_none=True)
async def check_limit(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    limit_data: CheckLimitRequest = ...,
    service = Depends(get_workspace_plan_management_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Check if a limit would be exceeded.
    
    Requires: Workspace access
    """
    result = service.check_limit(
        workspace_id=workspace_id,
        limit_type=limit_data.limit_type,
        increment=limit_data.increment
    )
    
    response_data = CheckLimitResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump()
    )

