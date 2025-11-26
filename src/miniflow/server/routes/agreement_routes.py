"""
Agreement routes.

Handles agreement version information (terms of service, privacy policy).
"""
from fastapi import APIRouter, Depends, Request, status, Query
from typing import Dict, Any

from src.miniflow.server.dependencies import get_agreement_service
from src.miniflow.services import AgreementService
from src.miniflow.server.schemas.base_schema import create_success_response

router = APIRouter(prefix="/agreements", tags=["agreements"])


# ============================================================================
# GET ACTIVE AGREEMENT
# ============================================================================

@router.get(
    "/active",
    summary="Get active agreement",
    description="Get the active version of an agreement (terms of service or privacy policy)",
    status_code=status.HTTP_200_OK,
)
async def get_active_agreement(
    request: Request,
    agreement_type: str = Query(..., description="Agreement type (e.g., 'terms', 'privacy_policy')"),
    locale: str = Query("tr-TR", description="Locale code (default: tr-TR)"),
    agreement_service: AgreementService = Depends(get_agreement_service),
) -> Dict[str, Any]:
    """
    Get the active version of an agreement.
    
    - **agreement_type**: Agreement type (query parameter)
        - "terms" - Terms of Service
        - "privacy_policy" - Privacy Policy
    - **locale**: Locale code (query parameter, optional, default: "tr-TR")
    
    Public endpoint - no authentication required.
    Used during registration to get the latest agreement version.
    """
    result = agreement_service.get_active_agreement(
        agreement_type=agreement_type,
        locale=locale,
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="Active agreement retrieved successfully",
        code=status.HTTP_200_OK,
    ).model_dump()

