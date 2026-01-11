"""Authentication routes for frontend (Login + Register)."""

from fastapi import APIRouter, Request, Depends
from typing import Optional

from miniflow.server.dependencies import (
    get_register_service,
    get_login_service,
    authenticate_user,
    authenticate_admin,
)
from miniflow.server.dependencies.auth import AuthenticatedUser
from miniflow.server.schemas.base_schemas import create_success_response
from .schemas.auth_schemas import (
    RegisterRequest,
    RegisterResponse,
    VerifyEmailRequest,
    VerifyEmailResponse,
    ResendVerificationEmailRequest,
    ResendVerificationEmailResponse,
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    LogoutResponse,
    LogoutAllResponse,
    ValidateTokenRequest,
    ValidateTokenResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    LockAccountRequest,
    LockAccountResponse,
    UnlockAccountRequest,
    UnlockAccountResponse,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _get_client_info(request: Request) -> tuple[Optional[str], Optional[str]]:
    """Extract IP address and user agent from request."""
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    return ip_address, user_agent


# ============================================================================
# REGISTRATION ENDPOINTS
# ============================================================================

@router.post("/register", response_model_exclude_none=True)
async def register_user(
    request: Request,
    register_data: RegisterRequest,
    service = Depends(get_register_service),
) -> dict:
    """
    Register a new user.
    
    Public endpoint - no authentication required.
    """
    ip_address, user_agent = _get_client_info(request)
    
    user = service.register_user(
        username=register_data.username,
        email=register_data.email,
        password=register_data.password,
        name=register_data.name,
        surname=register_data.surname,
        marketing_consent=register_data.marketing_consent,
        terms_accepted_version_id=register_data.terms_accepted_version_id,
        privacy_policy_accepted_version_id=register_data.privacy_policy_accepted_version_id,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    response_data = RegisterResponse(**user)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="User registered successfully. Please check your email for verification."
    )


@router.post("/verify-email", response_model_exclude_none=True)
async def verify_email(
    request: Request,
    verify_data: VerifyEmailRequest,
    service = Depends(get_register_service),
) -> dict:
    """
    Verify user email with verification token.
    
    Public endpoint - no authentication required.
    """
    user = service.verify_email(verification_token=verify_data.verification_token)
    
    response_data = VerifyEmailResponse(**user)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Email verified successfully."
    )


@router.post("/resend-verification", response_model_exclude_none=True)
async def resend_verification_email(
    request: Request,
    resend_data: ResendVerificationEmailRequest,
    service = Depends(get_register_service),
) -> dict:
    """
    Resend verification email.
    
    Public endpoint - no authentication required.
    Security: Returns same response whether user exists or not.
    """
    result = service.resend_verification_email(email=resend_data.email)
    
    response_data = ResendVerificationEmailResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="If an account exists, a verification email has been sent."
    )


# ============================================================================
# LOGIN ENDPOINTS
# ============================================================================

@router.post("/login", response_model_exclude_none=True)
async def login(
    request: Request,
    login_data: LoginRequest,
    service = Depends(get_login_service),
) -> dict:
    """
    User login.
    
    Public endpoint - no authentication required.
    """
    ip_address, user_agent = _get_client_info(request)
    
    result = service.login(
        email_or_username=login_data.email_or_username,
        password=login_data.password,
        ip_address=ip_address,
        user_agent=user_agent,
        device_type=login_data.device_type
    )
    
    response_data = LoginResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Login successful."
    )


@router.post("/logout", response_model_exclude_none=True)
async def logout(
    request: Request,
    logout_data: LogoutRequest,
    service = Depends(get_login_service),
) -> dict:
    """
    Logout current session.
    
    Requires: Access token in request body
    """
    result = service.logout(access_token=logout_data.access_token)
    
    response_data = LogoutResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump()
    )


@router.post("/logout-all", response_model_exclude_none=True)
async def logout_all(
    request: Request,
    service = Depends(get_login_service),
    current_user: AuthenticatedUser = Depends(authenticate_user),
) -> dict:
    """
    Logout all sessions for current user.
    
    Requires: User authentication
    """
    result = service.logout_all(user_id=current_user["user_id"])
    
    response_data = LogoutAllResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="All sessions logged out successfully."
    )


@router.post("/validate-token", response_model_exclude_none=True)
async def validate_token(
    request: Request,
    token_data: ValidateTokenRequest,
    service = Depends(get_login_service),
) -> dict:
    """
    Validate access token.
    
    Public endpoint - used for token validation.
    """
    result = service.validate_access_token(access_token=token_data.access_token)
    
    response_data = ValidateTokenResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump()
    )


@router.post("/refresh-token", response_model_exclude_none=True)
async def refresh_token(
    request: Request,
    refresh_data: RefreshTokenRequest,
    service = Depends(get_login_service),
) -> dict:
    """
    Refresh access and refresh tokens.
    
    Public endpoint - requires valid refresh token.
    """
    result = service.refresh_tokens(refresh_token=refresh_data.refresh_token)
    
    response_data = RefreshTokenResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Tokens refreshed successfully."
    )


# ============================================================================
# ACCOUNT MANAGEMENT ENDPOINTS (Admin)
# ============================================================================

@router.post("/lock-account", response_model_exclude_none=True)
async def lock_account(
    request: Request,
    lock_data: LockAccountRequest,
    service = Depends(get_login_service),
    current_user: AuthenticatedUser = Depends(authenticate_admin),
) -> dict:
    """
    Lock user account.
    
    Requires: Admin authentication
    """
    result = service.lock_account(
        user_id=lock_data.user_id,
        reason=lock_data.reason,
        duration_minutes=lock_data.duration_minutes
    )
    
    response_data = LockAccountResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Account locked successfully."
    )


@router.post("/unlock-account", response_model_exclude_none=True)
async def unlock_account(
    request: Request,
    unlock_data: UnlockAccountRequest,
    service = Depends(get_login_service),
    current_user: AuthenticatedUser = Depends(authenticate_admin),
) -> dict:
    """
    Unlock user account.
    
    Requires: Admin authentication
    """
    result = service.unlock_account(user_id=unlock_data.user_id)
    
    response_data = UnlockAccountResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Account unlocked successfully."
    )

