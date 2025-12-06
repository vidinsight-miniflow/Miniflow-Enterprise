"""Workspace plan management service schemas for frontend routes."""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


# ============================================================================
# PLAN INFO SCHEMAS
# ============================================================================

class PlanItem(BaseModel):
    """Schema for a single plan."""
    id: str = Field(..., description="Plan ID")
    name: str = Field(..., description="Plan name")
    display_name: Optional[str] = Field(None, description="Display name")
    description: Optional[str] = Field(None, description="Plan description")
    is_popular: bool = Field(False, description="Is popular plan?")
    monthly_price_usd: Optional[float] = Field(None, description="Monthly price in USD")
    yearly_price_usd: Optional[float] = Field(None, description="Yearly price in USD")
    features: Optional[List[str]] = Field(None, description="Feature list")


class AvailablePlansResponse(BaseModel):
    """Response schema for available plans."""
    plans: List[PlanItem] = Field(..., description="List of available plans")
    count: int = Field(..., description="Total plan count")


class PlanDetailsResponse(BaseModel):
    """Response schema for plan details."""
    id: str = Field(..., description="Plan ID")
    name: str = Field(..., description="Plan name")
    display_name: Optional[str] = Field(None, description="Display name")
    description: Optional[str] = Field(None, description="Plan description")
    is_popular: bool = Field(False, description="Is popular plan?")
    limits: Dict[str, Optional[int]] = Field(..., description="Plan limits")
    features: Dict[str, bool] = Field(..., description="Feature flags")
    api_limits: Dict[str, Optional[int]] = Field(..., description="API rate limits")
    pricing: Dict[str, Optional[float]] = Field(..., description="Pricing information")
    feature_list: Optional[List[str]] = Field(None, description="Feature list")


class WorkspaceCurrentPlanResponse(BaseModel):
    """Response schema for workspace current plan."""
    workspace_id: str = Field(..., description="Workspace ID")
    plan: Dict[str, str] = Field(..., description="Current plan info")
    usage: Dict[str, Dict[str, Any]] = Field(..., description="Usage statistics")
    billing: Dict[str, Optional[str]] = Field(..., description="Billing information")


# ============================================================================
# COMPARE PLANS SCHEMAS
# ============================================================================

class ComparePlansRequest(BaseModel):
    """Request schema for comparing plans."""
    plan_id_1: str = Field(..., description="First plan ID")
    plan_id_2: str = Field(..., description="Second plan ID")


class ComparePlansResponse(BaseModel):
    """Response schema for comparing plans."""
    plans: Dict[str, Dict[str, str]] = Field(..., description="Plan information")
    comparison: Dict[str, Dict[str, Any]] = Field(..., description="Comparison details")
    features: Dict[str, Dict[str, bool]] = Field(..., description="Feature comparison")


# ============================================================================
# UPGRADE/DOWNGRADE ELIGIBILITY SCHEMAS
# ============================================================================

class CheckUpgradeEligibilityRequest(BaseModel):
    """Request schema for checking upgrade eligibility."""
    target_plan_id: str = Field(..., description="Target plan ID")


class CheckUpgradeEligibilityResponse(BaseModel):
    """Response schema for upgrade eligibility."""
    eligible: bool = Field(..., description="Is upgrade eligible?")
    is_upgrade: bool = Field(..., description="Is this an upgrade?")
    current_plan: Dict[str, Any] = Field(..., description="Current plan info")
    target_plan: Dict[str, Any] = Field(..., description="Target plan info")
    price_difference_monthly: float = Field(..., description="Monthly price difference")
    issues: Optional[List[str]] = Field(None, description="Blocking issues")


class CheckDowngradeEligibilityRequest(BaseModel):
    """Request schema for checking downgrade eligibility."""
    target_plan_id: str = Field(..., description="Target plan ID")


class CheckDowngradeEligibilityResponse(BaseModel):
    """Response schema for downgrade eligibility."""
    eligible: bool = Field(..., description="Is downgrade eligible?")
    blocking_issues: Optional[List[str]] = Field(None, description="Blocking issues")
    current_plan: Dict[str, Any] = Field(..., description="Current plan info")
    target_plan: Dict[str, Any] = Field(..., description="Target plan info")
    monthly_savings: float = Field(..., description="Monthly savings")


# ============================================================================
# UPGRADE/DOWNGRADE SCHEMAS
# ============================================================================

class UpgradePlanRequest(BaseModel):
    """Request schema for upgrading plan."""
    target_plan_id: str = Field(..., description="Target plan ID")
    stripe_subscription_id: Optional[str] = Field(None, description="Stripe subscription ID")


class UpgradePlanResponse(BaseModel):
    """Response schema for upgrading plan."""
    success: bool = Field(..., description="Success status")
    workspace_id: str = Field(..., description="Workspace ID")
    new_plan_id: str = Field(..., description="New plan ID")
    new_plan_name: str = Field(..., description="New plan name")
    upgraded_at: str = Field(..., description="Upgrade timestamp (ISO format)")


class DowngradePlanRequest(BaseModel):
    """Request schema for downgrading plan."""
    target_plan_id: str = Field(..., description="Target plan ID")


class DowngradePlanResponse(BaseModel):
    """Response schema for downgrading plan."""
    success: bool = Field(..., description="Success status")
    workspace_id: str = Field(..., description="Workspace ID")
    new_plan_id: str = Field(..., description="New plan ID")
    new_plan_name: str = Field(..., description="New plan name")
    downgraded_at: str = Field(..., description="Downgrade timestamp (ISO format)")


# ============================================================================
# BILLING SCHEMAS
# ============================================================================

class UpdateBillingInfoRequest(BaseModel):
    """Request schema for updating billing info."""
    stripe_customer_id: Optional[str] = Field(None, description="Stripe customer ID")
    stripe_subscription_id: Optional[str] = Field(None, description="Stripe subscription ID")
    billing_email: Optional[str] = Field(None, description="Billing email")
    billing_currency: Optional[str] = Field(None, description="Billing currency")


class UpdateBillingInfoResponse(BaseModel):
    """Response schema for updating billing info."""
    workspace_id: str = Field(..., description="Workspace ID")
    stripe_customer_id: Optional[str] = Field(None, description="Stripe customer ID")
    stripe_subscription_id: Optional[str] = Field(None, description="Stripe subscription ID")
    billing_email: Optional[str] = Field(None, description="Billing email")
    billing_currency: Optional[str] = Field(None, description="Billing currency")


class UpdateBillingPeriodRequest(BaseModel):
    """Request schema for updating billing period."""
    period_start: str = Field(..., description="Period start (ISO format)")
    period_end: str = Field(..., description="Period end (ISO format)")


class UpdateBillingPeriodResponse(BaseModel):
    """Response schema for updating billing period."""
    success: bool = Field(..., description="Success status")
    workspace_id: str = Field(..., description="Workspace ID")
    period_start: str = Field(..., description="Period start (ISO format)")
    period_end: str = Field(..., description="Period end (ISO format)")


# ============================================================================
# LIMIT CHECK SCHEMAS
# ============================================================================

class CheckLimitRequest(BaseModel):
    """Request schema for checking limit."""
    limit_type: str = Field(..., description="Limit type (members, workflows, storage, executions, api_keys, scripts)")
    increment: int = Field(default=1, ge=1, description="Increment amount")


class CheckLimitResponse(BaseModel):
    """Response schema for limit check."""
    allowed: bool = Field(..., description="Is operation allowed?")
    current: int = Field(..., description="Current usage")
    limit: int = Field(..., description="Limit value")
    after_increment: int = Field(..., description="Value after increment")
    would_exceed_by: Optional[int] = Field(None, description="Amount that would exceed limit")

