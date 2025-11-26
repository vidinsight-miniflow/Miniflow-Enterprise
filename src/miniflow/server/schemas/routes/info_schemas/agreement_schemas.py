"""
Agreement route schemas.

Request and Response models for agreement endpoints.
"""
from typing import Optional
from pydantic import BaseModel, Field


# ============================================================================
# GET ACTIVE AGREEMENT
# ============================================================================

class GetActiveAgreementQuery(BaseModel):
    """Get active agreement query parameters"""
    agreement_type: str = Field(..., description="Agreement type (e.g., 'terms', 'privacy_policy')")
    locale: str = Field("tr-TR", description="Locale code (default: tr-TR)")


# Response is dict from service, no specific schema needed

