"""Agreement routes for frontend."""

from typing import List
from fastapi import APIRouter, Request, Depends, Query
from datetime import datetime

from miniflow.server.dependencies import (
    get_agreement_service,
    authenticate_admin,
)
from miniflow.server.dependencies.auth import AuthenticatedUser
from miniflow.server.schemas.base_schemas import create_success_response
from .schemas.agreement_schemas import (
    AgreementCreateRequest,
    AgreementResponse,
    AgreementListResponse,
)

router = APIRouter(prefix="/agreements", tags=["Agreements"])


def _standardize_agreement_dict(data: dict) -> dict:
    """Standardize agreement dict: record_id -> id."""
    standardized = data.copy()
    if "record_id" in standardized:
        standardized["id"] = standardized.pop("record_id")
    if "id" not in standardized and "agreement_id" in standardized:
        standardized["id"] = standardized.pop("agreement_id")
    return standardized


@router.get("", response_model_exclude_none=True)
async def get_all_agreements(
    request: Request,
    service = Depends(get_agreement_service),
) -> dict:
    """
    Get all agreement versions.
    
    Public endpoint - no authentication required.
    """
    agreements = service.get_all_agreements()
    standardized = [_standardize_agreement_dict(agr) for agr in agreements]
    response_data = AgreementListResponse(items=[AgreementResponse.from_dict(agr) for agr in standardized])
    return create_success_response(request, data=response_data.model_dump())


@router.get("/active", response_model_exclude_none=True)
async def get_active_agreements(
    request: Request,
    locale: str = Query(default="tr-TR", description="Locale code"),
    service = Depends(get_agreement_service),
) -> dict:
    """
    Get all active agreements (one per type).
    
    Public endpoint - no authentication required.
    Used for registration and public display of terms/privacy policy.
    """
    agreements = service.get_active_agreements(locale=locale)
    standardized = [_standardize_agreement_dict(agr) for agr in agreements]
    response_data = AgreementListResponse(items=[AgreementResponse.from_dict(agr) for agr in standardized])
    return create_success_response(request, data=response_data.model_dump())


@router.get("/{agreement_id}", response_model_exclude_none=True)
async def get_agreement_by_id(
    request: Request,
    agreement_id: str,
    service = Depends(get_agreement_service),
) -> dict:
    """
    Get agreement by ID.
    
    Public endpoint - no authentication required.
    """
    agreement = service.get_agreement_by_id(agreement_id=agreement_id)
    standardized = _standardize_agreement_dict(agreement)
    response_data = AgreementResponse.from_dict(standardized)
    return create_success_response(request, data=response_data.model_dump())


@router.get("/type/{agreement_type}/active", response_model_exclude_none=True)
async def get_active_agreement_by_type(
    request: Request,
    agreement_type: str,
    locale: str = Query(default="tr-TR", description="Locale code"),
    service = Depends(get_agreement_service),
) -> dict:
    """
    Get active agreement by type.
    
    Public endpoint - no authentication required.
    Used for registration and public display of specific agreement type.
    """
    agreement = service.get_active_agreement_by_type(agreement_type=agreement_type, locale=locale)
    standardized = _standardize_agreement_dict(agreement)
    response_data = AgreementResponse.from_dict(standardized)
    return create_success_response(request, data=response_data.model_dump())


@router.get("/type/{agreement_type}/version/{version}", response_model_exclude_none=True)
async def get_agreement_by_type_and_version(
    request: Request,
    agreement_type: str,
    version: str,
    locale: str = Query(default="tr-TR", description="Locale code"),
    service = Depends(get_agreement_service),
) -> dict:
    """
    Get agreement by type, version and locale.
    
    Public endpoint - no authentication required.
    """
    agreement = service.get_agreement_by_type_and_version(
        agreement_type=agreement_type,
        version=version,
        locale=locale
    )
    standardized = _standardize_agreement_dict(agreement)
    response_data = AgreementResponse.from_dict(standardized)
    return create_success_response(request, data=response_data.model_dump())


@router.get("/type/{agreement_type}/versions", response_model_exclude_none=True)
async def get_all_versions_by_type(
    request: Request,
    agreement_type: str,
    locale: str = Query(default=None, description="Locale code (optional)"),
    service = Depends(get_agreement_service),
) -> dict:
    """
    Get all versions for a specific agreement type.
    
    Public endpoint - no authentication required.
    """
    agreements = service.get_all_versions_by_type(agreement_type=agreement_type, locale=locale)
    standardized = [_standardize_agreement_dict(agr) for agr in agreements]
    response_data = AgreementListResponse(items=[AgreementResponse.from_dict(agr) for agr in standardized])
    return create_success_response(request, data=response_data.model_dump())


@router.post("", response_model_exclude_none=True)
async def create_agreement_version(
    request: Request,
    agreement_data: AgreementCreateRequest,
    service = Depends(get_agreement_service),
    current_user: AuthenticatedUser = Depends(authenticate_admin),
) -> dict:
    """
    Create a new agreement version.
    
    Requires: Admin authentication
    """
    agreement = service.create_agreement_version(
        agreement_type=agreement_data.agreement_type,
        version=agreement_data.version,
        content=agreement_data.content,
        effective_date=agreement_data.effective_date,
        locale=agreement_data.locale,
        is_active=agreement_data.is_active,
        created_by=current_user.get("user_id"),
        notes=agreement_data.notes
    )
    standardized = _standardize_agreement_dict(agreement)
    response_data = AgreementResponse.from_dict(standardized)
    return create_success_response(request, data=response_data.model_dump())


@router.put("/{agreement_id}/activate", response_model_exclude_none=True)
async def activate_agreement(
    request: Request,
    agreement_id: str,
    service = Depends(get_agreement_service),
    current_user: AuthenticatedUser = Depends(authenticate_admin),
) -> dict:
    """
    Activate an agreement version.
    
    Requires: Admin authentication
    """
    agreement = service.activate_agreement(agreement_id=agreement_id)
    standardized = _standardize_agreement_dict(agreement)
    response_data = AgreementResponse.from_dict(standardized)
    return create_success_response(request, data=response_data.model_dump())


@router.put("/{agreement_id}/deactivate", response_model_exclude_none=True)
async def deactivate_agreement(
    request: Request,
    agreement_id: str,
    service = Depends(get_agreement_service),
    current_user: AuthenticatedUser = Depends(authenticate_admin),
) -> dict:
    """
    Deactivate an agreement version.
    
    Requires: Admin authentication
    """
    agreement = service.deactivate_agreement(agreement_id=agreement_id)
    standardized = _standardize_agreement_dict(agreement)
    response_data = AgreementResponse.from_dict(standardized)
    return create_success_response(request, data=response_data.model_dump())


@router.delete("/{agreement_id}", response_model_exclude_none=True)
async def delete_agreement(
    request: Request,
    agreement_id: str,
    service = Depends(get_agreement_service),
    current_user: AuthenticatedUser = Depends(authenticate_admin),
) -> dict:
    """
    Delete (soft-delete) an agreement version.
    
    Requires: Admin authentication
    """
    service.delete_agreement(agreement_id=agreement_id)
    return create_success_response(request, data={"deleted": True}, message="Agreement deleted successfully")

