"""User password routes for frontend."""

from fastapi import APIRouter, Request, Depends, Query

from miniflow.server.dependencies import (
    get_user_password_service,
    authenticate_user,
)
from miniflow.server.dependencies.auth import AuthenticatedUser
from miniflow.server.schemas.base_schemas import create_success_response
from .schemas.user_password_schemas import (
    ChangePasswordRequest,
    ChangePasswordResponse,
    SendPasswordResetEmailRequest,
    SendPasswordResetEmailResponse,
    ValidatePasswordResetTokenRequest,
    ValidatePasswordResetTokenResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
    PasswordHistoryResponse,
)

router = APIRouter(prefix="/users", tags=["User Password"])


def _get_client_info(request: Request) -> tuple[str | None, str | None]:
    """Extract IP address and user agent from request."""
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    return ip_address, user_agent


# ============================================================================
# CHANGE PASSWORD ENDPOINTS
# ============================================================================

@router.put("/{user_id}/password/change", response_model_exclude_none=True)
async def change_password(
    request: Request,
    user_id: str,
    password_data: ChangePasswordRequest,
    service = Depends(get_user_password_service),
    current_user: AuthenticatedUser = Depends(authenticate_user),
) -> dict:
    """
    Change password (requires old password).
    
    Requires: User authentication
    Security: Users can only change their own password
    """
    # Security: Users can only change their own password
    if current_user["user_id"] != user_id:
        from miniflow.core.exceptions import PermissionDeniedError
        raise PermissionDeniedError(
            message="You can only change your own password"
        )
    
    ip_address, user_agent = _get_client_info(request)
    
    result = service.change_password(
        user_id=user_id,
        old_password=password_data.old_password,
        new_password=password_data.new_password,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    response_data = ChangePasswordResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump()
    )


# ============================================================================
# PASSWORD RESET ENDPOINTS (Public)
# ============================================================================

@router.post("/password/reset/request", response_model_exclude_none=True)
async def send_password_reset_email(
    request: Request,
    reset_data: SendPasswordResetEmailRequest,
    service = Depends(get_user_password_service),
) -> dict:
    """
    Send password reset email.
    
    Public endpoint - no authentication required.
    Security: Returns same response whether email exists or not.
    """
    result = service.send_password_reset_email(
        email=reset_data.email
    )
    
    response_data = SendPasswordResetEmailResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump()
    )


@router.post("/password/reset/validate", response_model_exclude_none=True)
async def validate_password_reset_token(
    request: Request,
    token_data: ValidatePasswordResetTokenRequest,
    service = Depends(get_user_password_service),
) -> dict:
    """
    Validate password reset token.
    
    Public endpoint - no authentication required.
    """
    result = service.validate_password_reset_token(
        token=token_data.token
    )
    
    response_data = ValidatePasswordResetTokenResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump()
    )


@router.post("/password/reset", response_model_exclude_none=True)
async def reset_password(
    request: Request,
    reset_data: ResetPasswordRequest,
    service = Depends(get_user_password_service),
) -> dict:
    """
    Reset password using reset token.
    
    Public endpoint - no authentication required.
    Note: All active sessions will be revoked for security.
    """
    ip_address, user_agent = _get_client_info(request)
    
    result = service.reset_password(
        token=reset_data.token,
        new_password=reset_data.new_password,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    response_data = ResetPasswordResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump()
    )


# ============================================================================
# PASSWORD HISTORY ENDPOINTS
# ============================================================================

@router.get("/{user_id}/password/history", response_model_exclude_none=True)
async def get_password_history(
    request: Request,
    user_id: str,
    limit: int = Query(default=10, ge=1, le=50, description="Maximum number of records"),
    service = Depends(get_user_password_service),
    current_user: AuthenticatedUser = Depends(authenticate_user),
) -> dict:
    """
    Get password change history.
    
    Requires: User authentication
    Security: Users can only view their own password history
    """
    # Security: Users can only view their own password history
    if current_user["user_id"] != user_id:
        from miniflow.core.exceptions import PermissionDeniedError
        raise PermissionDeniedError(
            message="You can only view your own password history"
        )
    
    result = service.get_password_history(
        user_id=user_id,
        limit=limit
    )
    
    response_data = PasswordHistoryResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump()
    )

