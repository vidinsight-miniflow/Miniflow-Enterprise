"""Workspace plan service schemas for frontend routes."""

from typing import Optional, List, Dict
from datetime import datetime
from pydantic import BaseModel, Field


# ============================================================================
# OUTPUT SCHEMAS
# ============================================================================

class WorkspacePlanResponse(BaseModel):
    """Response schema for workspace plan data."""
    id: str = Field(..., description="Plan ID")
    name: str = Field(..., description="Plan name")
    description: Optional[str] = Field(None, description="Plan description")
    display_order: int = Field(default=0, description="Display order")
    max_members_per_workspace: Optional[int] = Field(None, description="Max members per workspace")
    max_workflows_per_workspace: Optional[int] = Field(None, description="Max workflows per workspace")
    max_custom_scripts_per_workspace: Optional[int] = Field(None, description="Max custom scripts per workspace")
    storage_limit_mb_per_workspace: Optional[int] = Field(None, description="Storage limit in MB")
    max_file_size_mb_per_workspace: Optional[int] = Field(None, description="Max file size in MB")
    monthly_execution_limit: Optional[int] = Field(None, description="Monthly execution limit")
    max_concurrent_executions: Optional[int] = Field(None, description="Max concurrent executions")
    can_use_custom_scripts: bool = Field(default=False, description="Can use custom scripts")
    can_use_api_access: bool = Field(default=False, description="Can use API access")
    can_use_webhooks: bool = Field(default=False, description="Can use webhooks")
    can_use_scheduling: bool = Field(default=False, description="Can use scheduling")
    can_export_data: bool = Field(default=False, description="Can export data")
    max_api_keys_per_workspace: Optional[int] = Field(None, description="Max API keys per workspace")
    api_rate_limit_per_minute: Optional[int] = Field(None, description="API rate limit per minute")
    api_rate_limit_per_hour: Optional[int] = Field(None, description="API rate limit per hour")
    api_rate_limit_per_day: Optional[int] = Field(None, description="API rate limit per day")
    monthly_price_usd: Optional[float] = Field(None, description="Monthly price in USD")
    yearly_price_usd: Optional[float] = Field(None, description="Yearly price in USD")
    price_per_extra_member_usd: Optional[float] = Field(None, description="Price per extra member in USD")
    price_per_extra_workflow_usd: Optional[float] = Field(None, description="Price per extra workflow in USD")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    @classmethod
    def from_dict(cls, data: dict) -> "WorkspacePlanResponse":
        """Create from service dict output."""
        standardized = data.copy()
        if "record_id" in standardized:
            standardized["id"] = standardized.pop("record_id")
        if "id" not in standardized and "plan_id" in standardized:
            standardized["id"] = standardized.pop("plan_id")
        return cls(**standardized)


class WorkspacePlanListResponse(BaseModel):
    """Response schema for workspace plan list."""
    items: List[WorkspacePlanResponse] = Field(..., description="List of workspace plans")


class WorkspaceLimitsResponse(BaseModel):
    """Response schema for workspace limits."""
    plan_id: str = Field(..., description="Plan ID")
    max_members_per_workspace: Optional[int] = Field(None, description="Max members per workspace")
    max_workflows_per_workspace: Optional[int] = Field(None, description="Max workflows per workspace")
    max_custom_scripts_per_workspace: Optional[int] = Field(None, description="Max custom scripts per workspace")
    storage_limit_mb_per_workspace: Optional[int] = Field(None, description="Storage limit in MB")
    max_file_size_mb_per_workspace: Optional[int] = Field(None, description="Max file size in MB")


class MonthlyLimitsResponse(BaseModel):
    """Response schema for monthly limits."""
    plan_id: str = Field(..., description="Plan ID")
    monthly_execution_limit: Optional[int] = Field(None, description="Monthly execution limit")
    max_concurrent_executions: Optional[int] = Field(None, description="Max concurrent executions")


class FeatureFlagsResponse(BaseModel):
    """Response schema for feature flags."""
    plan_id: str = Field(..., description="Plan ID")
    can_use_custom_scripts: bool = Field(default=False, description="Can use custom scripts")
    can_use_api_access: bool = Field(default=False, description="Can use API access")
    can_use_webhooks: bool = Field(default=False, description="Can use webhooks")
    can_use_scheduling: bool = Field(default=False, description="Can use scheduling")
    can_export_data: bool = Field(default=False, description="Can export data")


class ApiLimitsResponse(BaseModel):
    """Response schema for API limits."""
    plan_id: str = Field(..., description="Plan ID")
    max_api_keys_per_workspace: Optional[int] = Field(None, description="Max API keys per workspace")
    api_rate_limit_per_minute: Optional[int] = Field(None, description="API rate limit per minute")
    api_rate_limit_per_hour: Optional[int] = Field(None, description="API rate limit per hour")
    api_rate_limit_per_day: Optional[int] = Field(None, description="API rate limit per day")


class PricingResponse(BaseModel):
    """Response schema for pricing information."""
    plan_id: str = Field(..., description="Plan ID")
    monthly_price_usd: Optional[float] = Field(None, description="Monthly price in USD")
    yearly_price_usd: Optional[float] = Field(None, description="Yearly price in USD")
    price_per_extra_member_usd: Optional[float] = Field(None, description="Price per extra member in USD")
    price_per_extra_workflow_usd: Optional[float] = Field(None, description="Price per extra workflow in USD")


class AllApiRateLimitsResponse(BaseModel):
    """Response schema for all API rate limits."""
    limits: Dict[str, Dict[str, int]] = Field(..., description="Plan ID to rate limits mapping")

