"""Agreement service schemas for frontend routes."""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


# ============================================================================
# INPUT SCHEMAS
# ============================================================================

class AgreementCreateRequest(BaseModel):
    """Request schema for creating a new agreement version."""
    agreement_type: str = Field(..., description="Agreement type (e.g., 'terms', 'privacy_policy')")
    version: str = Field(..., description="Version number")
    content: str = Field(..., description="Agreement content (Markdown)")
    effective_date: datetime = Field(..., description="Effective date")
    locale: str = Field(default="tr-TR", description="Locale code")
    is_active: bool = Field(default=False, description="Is this version active?")
    notes: Optional[str] = Field(None, description="Version notes")


# ============================================================================
# OUTPUT SCHEMAS
# ============================================================================

class AgreementResponse(BaseModel):
    """Response schema for agreement data."""
    id: str = Field(..., description="Agreement ID")
    agreement_type: str = Field(..., description="Agreement type")
    version: str = Field(..., description="Version number")
    content: str = Field(..., description="Agreement content")
    content_hash: str = Field(..., description="Content hash")
    effective_date: datetime = Field(..., description="Effective date")
    locale: str = Field(..., description="Locale code")
    is_active: bool = Field(..., description="Is active?")
    created_by: Optional[str] = Field(None, description="Created by user ID")
    notes: Optional[str] = Field(None, description="Version notes")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    @classmethod
    def from_dict(cls, data: dict) -> "AgreementResponse":
        """Create from service dict output."""
        # Standardize field names: record_id -> id, user_id -> id (if applicable)
        standardized = data.copy()
        if "record_id" in standardized:
            standardized["id"] = standardized.pop("record_id")
        if "id" not in standardized and "agreement_id" in standardized:
            standardized["id"] = standardized.pop("agreement_id")
        return cls(**standardized)


class AgreementListResponse(BaseModel):
    """Response schema for agreement list."""
    items: List[AgreementResponse] = Field(..., description="List of agreements")

