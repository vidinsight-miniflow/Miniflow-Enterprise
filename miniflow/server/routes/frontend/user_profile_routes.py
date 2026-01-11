"""User profile routes for frontend."""

from fastapi import APIRouter, Request, Depends

from miniflow.server.dependencies import (
    get_user_profile_service,
    authenticate_user,
)
from miniflow.server.dependencies.auth import AuthenticatedUser
from miniflow.server.schemas.base_schemas import create_success_response
from .schemas.user_profile_schemas import (
    UpdateProfileRequest,
    UpdateProfileResponse,
    ChangeUsernameRequest,
    ChangeUsernameResponse,
    ChangeEmailRequest,
    ChangeEmailResponse,
    ChangePhoneRequest,
    ChangePhoneResponse,
    VerifyPhoneRequest,
    VerifyPhoneResponse,
)

router = APIRouter(prefix="/users", tags=["User Profile"])


# ============================================================================
# PROFILE UPDATE ENDPOINTS
# ============================================================================

@router.put("/{user_id}/profile", response_model_exclude_none=True)
async def update_profile(
    request: Request,
    user_id: str,
    profile_data: UpdateProfileRequest,
    service = Depends(get_user_profile_service),
    current_user: AuthenticatedUser = Depends(authenticate_user),
) -> dict:
    """
    Update user profile information.
    
    Requires: User authentication
    Security: Users can only update their own profile
    """
    # Security: Users can only update their own profile
    if current_user["user_id"] != user_id:
        from miniflow.core.exceptions import PermissionDeniedError
        raise PermissionDeniedError(
            message="You can only update your own profile"
        )
    
    result = service.update_profile(
        user_id=user_id,
        name=profile_data.name,
        surname=profile_data.surname,
        avatar_url=profile_data.avatar_url,
        country_code=profile_data.country_code,
        phone_number=profile_data.phone_number
    )
    
    response_data = UpdateProfileResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Profile updated successfully."
    )


# ============================================================================
# USERNAME CHANGE ENDPOINTS
# ============================================================================

@router.put("/{user_id}/username", response_model_exclude_none=True)
async def change_username(
    request: Request,
    user_id: str,
    username_data: ChangeUsernameRequest,
    service = Depends(get_user_profile_service),
    current_user: AuthenticatedUser = Depends(authenticate_user),
) -> dict:
    """
    Change username.
    
    Requires: User authentication
    Security: Users can only change their own username
    """
    # Security: Users can only change their own username
    if current_user["user_id"] != user_id:
        from miniflow.core.exceptions import PermissionDeniedError
        raise PermissionDeniedError(
            message="You can only change your own username"
        )
    
    result = service.change_username(
        user_id=user_id,
        new_username=username_data.new_username
    )
    
    response_data = ChangeUsernameResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Username changed successfully."
    )


# ============================================================================
# EMAIL CHANGE ENDPOINTS
# ============================================================================

@router.put("/{user_id}/email", response_model_exclude_none=True)
async def change_email(
    request: Request,
    user_id: str,
    email_data: ChangeEmailRequest,
    service = Depends(get_user_profile_service),
    current_user: AuthenticatedUser = Depends(authenticate_user),
) -> dict:
    """
    Change email address.
    
    Requires: User authentication
    Security: Users can only change their own email
    Note: All active sessions will be revoked for security.
    """
    # Security: Users can only change their own email
    if current_user["user_id"] != user_id:
        from miniflow.core.exceptions import PermissionDeniedError
        raise PermissionDeniedError(
            message="You can only change your own email"
        )
    
    result = service.change_email(
        user_id=user_id,
        new_email=email_data.new_email
    )
    
    response_data = ChangeEmailResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump()
    )


# ============================================================================
# PHONE CHANGE ENDPOINTS
# ============================================================================

@router.put("/{user_id}/phone", response_model_exclude_none=True)
async def change_phone(
    request: Request,
    user_id: str,
    phone_data: ChangePhoneRequest,
    service = Depends(get_user_profile_service),
    current_user: AuthenticatedUser = Depends(authenticate_user),
) -> dict:
    """
    Change phone number.
    
    Requires: User authentication
    Security: Users can only change their own phone number
    """
    # Security: Users can only change their own phone number
    if current_user["user_id"] != user_id:
        from miniflow.core.exceptions import PermissionDeniedError
        raise PermissionDeniedError(
            message="You can only change your own phone number"
        )
    
    result = service.change_phone(
        user_id=user_id,
        country_code=phone_data.country_code,
        phone_number=phone_data.phone_number
    )
    
    response_data = ChangePhoneResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Phone number updated. Please verify with the code sent to your phone."
    )


@router.post("/{user_id}/phone/verify", response_model_exclude_none=True)
async def verify_phone(
    request: Request,
    user_id: str,
    verify_data: VerifyPhoneRequest,
    service = Depends(get_user_profile_service),
    current_user: AuthenticatedUser = Depends(authenticate_user),
) -> dict:
    """
    Verify phone number with SMS code.
    
    Requires: User authentication
    Security: Users can only verify their own phone number
    """
    # Security: Users can only verify their own phone number
    if current_user["user_id"] != user_id:
        from miniflow.core.exceptions import PermissionDeniedError
        raise PermissionDeniedError(
            message="You can only verify your own phone number"
        )
    
    result = service.verify_phone(
        user_id=user_id,
        verification_code=verify_data.verification_code
    )
    
    response_data = VerifyPhoneResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Phone number verified successfully."
    )

