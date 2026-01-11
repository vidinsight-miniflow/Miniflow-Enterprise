"""User management routes for frontend."""

from fastapi import APIRouter, Request, Depends, Query
from typing import Optional

from miniflow.server.dependencies import (
    get_user_management_service,
    authenticate_user,
    authenticate_admin,
)
from miniflow.server.dependencies.auth import AuthenticatedUser
from miniflow.server.schemas.base_schemas import create_success_response
from .schemas.user_management_schemas import (
    UserDetailsResponse,
    UserPreferencesResponse,
    UserPreferenceResponse,
    UserPreferencesByCategoryResponse,
    SetUserPreferenceRequest,
    DeleteUserPreferenceResponse,
    RequestAccountDeletionRequest,
    RequestAccountDeletionResponse,
    CancelAccountDeletionResponse,
    DeletionStatusResponse,
    UpdateMarketingConsentRequest,
    UpdateMarketingConsentResponse,
)

router = APIRouter(prefix="/users", tags=["User Management"])


def _standardize_user_dict(data: dict) -> dict:
    """Standardize user dict keys (record_id -> id)."""
    if 'record_id' in data:
        data['id'] = data.pop('record_id')
    return data


# ============================================================================
# USER DETAILS ENDPOINTS
# ============================================================================

@router.get("/{user_id}", response_model_exclude_none=True)
async def get_user_details(
    request: Request,
    user_id: str,
    service = Depends(get_user_management_service),
    current_user: AuthenticatedUser = Depends(authenticate_user),
) -> dict:
    """
    Get user details by ID.
    
    Requires: User authentication
    Security: Users can only view their own details (unless admin)
    """
    # Security: Users can only view their own details
    if current_user["user_id"] != user_id and not current_user.get("is_admin", False):
        from miniflow.core.exceptions import PermissionDeniedError
        raise PermissionDeniedError(
            message="You can only view your own user details"
        )
    
    user = service.get_user_details(user_id=user_id)
    standardized_user = _standardize_user_dict(user)
    
    response_data = UserDetailsResponse.from_dict(standardized_user)
    return create_success_response(
        request,
        data=response_data.model_dump()
    )


@router.get("/by-email/{email}", response_model_exclude_none=True)
async def get_user_by_email(
    request: Request,
    email: str,
    service = Depends(get_user_management_service),
    current_user: AuthenticatedUser = Depends(authenticate_admin),
) -> dict:
    """
    Get user details by email.
    
    Requires: Admin authentication
    """
    user = service.get_user_by_email(email=email)
    standardized_user = _standardize_user_dict(user)
    
    response_data = UserDetailsResponse.from_dict(standardized_user)
    return create_success_response(
        request,
        data=response_data.model_dump()
    )


@router.get("/by-username/{username}", response_model_exclude_none=True)
async def get_user_by_username(
    request: Request,
    username: str,
    service = Depends(get_user_management_service),
    current_user: AuthenticatedUser = Depends(authenticate_admin),
) -> dict:
    """
    Get user details by username.
    
    Requires: Admin authentication
    """
    user = service.get_user_by_username(username=username)
    standardized_user = _standardize_user_dict(user)
    
    response_data = UserDetailsResponse.from_dict(standardized_user)
    return create_success_response(
        request,
        data=response_data.model_dump()
    )


# ============================================================================
# USER PREFERENCES ENDPOINTS
# ============================================================================

@router.get("/{user_id}/preferences", response_model_exclude_none=True)
async def get_all_user_preferences(
    request: Request,
    user_id: str,
    service = Depends(get_user_management_service),
    current_user: AuthenticatedUser = Depends(authenticate_user),
) -> dict:
    """
    Get all user preferences.
    
    Requires: User authentication
    Security: Users can only view their own preferences
    """
    # Security: Users can only view their own preferences
    if current_user["user_id"] != user_id:
        from miniflow.core.exceptions import PermissionDeniedError
        raise PermissionDeniedError(
            message="You can only view your own preferences"
        )
    
    result = service.get_all_user_preferences(user_id=user_id)
    
    response_data = UserPreferencesResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump()
    )


@router.get("/{user_id}/preferences/{preference_key}", response_model_exclude_none=True)
async def get_user_preference(
    request: Request,
    user_id: str,
    preference_key: str,
    service = Depends(get_user_management_service),
    current_user: AuthenticatedUser = Depends(authenticate_user),
) -> dict:
    """
    Get a specific user preference.
    
    Requires: User authentication
    Security: Users can only view their own preferences
    """
    # Security: Users can only view their own preferences
    if current_user["user_id"] != user_id:
        from miniflow.core.exceptions import PermissionDeniedError
        raise PermissionDeniedError(
            message="You can only view your own preferences"
        )
    
    preference = service.get_user_preference(
        user_id=user_id,
        preference_key=preference_key
    )
    
    response_data = UserPreferenceResponse(**preference)
    return create_success_response(
        request,
        data=response_data.model_dump()
    )


@router.get("/{user_id}/preferences/category/{category}", response_model_exclude_none=True)
async def get_user_preferences_by_category(
    request: Request,
    user_id: str,
    category: str,
    service = Depends(get_user_management_service),
    current_user: AuthenticatedUser = Depends(authenticate_user),
) -> dict:
    """
    Get user preferences by category.
    
    Requires: User authentication
    Security: Users can only view their own preferences
    """
    # Security: Users can only view their own preferences
    if current_user["user_id"] != user_id:
        from miniflow.core.exceptions import PermissionDeniedError
        raise PermissionDeniedError(
            message="You can only view your own preferences"
        )
    
    result = service.get_user_preferences_by_category(
        user_id=user_id,
        category=category
    )
    
    response_data = UserPreferencesByCategoryResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump()
    )


@router.put("/{user_id}/preferences", response_model_exclude_none=True)
async def set_user_preference(
    request: Request,
    user_id: str,
    preference_data: SetUserPreferenceRequest,
    service = Depends(get_user_management_service),
    current_user: AuthenticatedUser = Depends(authenticate_user),
) -> dict:
    """
    Set or update user preference.
    
    Requires: User authentication
    Security: Users can only update their own preferences
    """
    # Security: Users can only update their own preferences
    if current_user["user_id"] != user_id:
        from miniflow.core.exceptions import PermissionDeniedError
        raise PermissionDeniedError(
            message="You can only update your own preferences"
        )
    
    preference = service.set_user_preference(
        user_id=user_id,
        key=preference_data.key,
        value=preference_data.value,
        category=preference_data.category,
        description=preference_data.description
    )
    
    response_data = UserPreferenceResponse(**preference)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Preference updated successfully."
    )


@router.delete("/{user_id}/preferences/{preference_key}", response_model_exclude_none=True)
async def delete_user_preference(
    request: Request,
    user_id: str,
    preference_key: str,
    service = Depends(get_user_management_service),
    current_user: AuthenticatedUser = Depends(authenticate_user),
) -> dict:
    """
    Delete user preference.
    
    Requires: User authentication
    Security: Users can only delete their own preferences
    """
    # Security: Users can only delete their own preferences
    if current_user["user_id"] != user_id:
        from miniflow.core.exceptions import PermissionDeniedError
        raise PermissionDeniedError(
            message="You can only delete your own preferences"
        )
    
    result = service.delete_user_preference(
        user_id=user_id,
        preference_key=preference_key
    )
    
    response_data = DeleteUserPreferenceResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Preference deleted successfully."
    )


# ============================================================================
# ACCOUNT DELETION ENDPOINTS
# ============================================================================

@router.post("/{user_id}/deletion/request", response_model_exclude_none=True)
async def request_account_deletion(
    request: Request,
    user_id: str,
    deletion_data: RequestAccountDeletionRequest,
    service = Depends(get_user_management_service),
    current_user: AuthenticatedUser = Depends(authenticate_user),
) -> dict:
    """
    Request account deletion.
    
    Requires: User authentication
    Security: Users can only request deletion for their own account
    """
    # Security: Users can only request deletion for their own account
    if current_user["user_id"] != user_id:
        from miniflow.core.exceptions import PermissionDeniedError
        raise PermissionDeniedError(
            message="You can only request deletion for your own account"
        )
    
    result = service.request_account_deletion(
        user_id=user_id,
        reason=deletion_data.reason
    )
    
    response_data = RequestAccountDeletionResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Account deletion requested. You have 30 days to cancel."
    )


@router.post("/{user_id}/deletion/cancel", response_model_exclude_none=True)
async def cancel_account_deletion(
    request: Request,
    user_id: str,
    service = Depends(get_user_management_service),
    current_user: AuthenticatedUser = Depends(authenticate_user),
) -> dict:
    """
    Cancel account deletion request.
    
    Requires: User authentication
    Security: Users can only cancel deletion for their own account
    """
    # Security: Users can only cancel deletion for their own account
    if current_user["user_id"] != user_id:
        from miniflow.core.exceptions import PermissionDeniedError
        raise PermissionDeniedError(
            message="You can only cancel deletion for your own account"
        )
    
    result = service.cancel_account_deletion(user_id=user_id)
    
    response_data = CancelAccountDeletionResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump()
    )


@router.get("/{user_id}/deletion/status", response_model_exclude_none=True)
async def get_deletion_status(
    request: Request,
    user_id: str,
    service = Depends(get_user_management_service),
    current_user: AuthenticatedUser = Depends(authenticate_user),
) -> dict:
    """
    Get account deletion status.
    
    Requires: User authentication
    Security: Users can only view deletion status for their own account
    """
    # Security: Users can only view deletion status for their own account
    if current_user["user_id"] != user_id:
        from miniflow.core.exceptions import PermissionDeniedError
        raise PermissionDeniedError(
            message="You can only view deletion status for your own account"
        )
    
    result = service.get_deletion_status(user_id=user_id)
    
    response_data = DeletionStatusResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump()
    )


# ============================================================================
# MARKETING CONSENT ENDPOINTS
# ============================================================================

@router.put("/{user_id}/marketing-consent", response_model_exclude_none=True)
async def update_marketing_consent(
    request: Request,
    user_id: str,
    consent_data: UpdateMarketingConsentRequest,
    service = Depends(get_user_management_service),
    current_user: AuthenticatedUser = Depends(authenticate_user),
) -> dict:
    """
    Update marketing consent.
    
    Requires: User authentication
    Security: Users can only update their own marketing consent
    """
    # Security: Users can only update their own marketing consent
    if current_user["user_id"] != user_id:
        from miniflow.core.exceptions import PermissionDeniedError
        raise PermissionDeniedError(
            message="You can only update your own marketing consent"
        )
    
    result = service.update_marketing_consent(
        user_id=user_id,
        consent=consent_data.consent
    )
    
    response_data = UpdateMarketingConsentResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Marketing consent updated successfully."
    )

