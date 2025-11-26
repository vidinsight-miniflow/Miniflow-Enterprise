"""
Authentication routes.

Handles user registration, login, logout, email verification, and token refresh.
"""
from fastapi import APIRouter, Depends, Request, status, Header
from typing import Dict, Any, Optional

from src.miniflow.server.dependencies import get_auth_service
from src.miniflow.services import AuthenticationService
from src.miniflow.server.helpers import authenticate_user, AuthUser
from src.miniflow.server.schemas.base_schema import create_success_response
from src.miniflow.server.schemas.routes.auth_schemas import (
    RegisterUserRequest,
    SendVerificationEmailRequest,
    VerifyEmailRequest,
    LoginRequest,
    RefreshTokenRequest,
)

router = APIRouter(prefix="/auth", tags=["authentication"])


# ============================================================================
# REGISTER USER
# ============================================================================

@router.post(
    "/register",
    summary="Register a new user",
    description="Create a new user account with email verification",
    status_code=status.HTTP_201_CREATED,
)
async def register_user(
    request: Request,
    body: RegisterUserRequest,
    auth_service: AuthenticationService = Depends(get_auth_service),
    ip_address: Optional[str] = Header(None, alias="X-Forwarded-For"),
    user_agent: Optional[str] = Header(None, alias="User-Agent"),
) -> Dict[str, Any]:
    """
    Register a new user account.
    
    - **username**: Username (3-50 characters)
    - **email**: Email address
    - **password**: Password (minimum 8 characters)
    - **name**: First name
    - **surname**: Last name
    - **marketing_consent**: Marketing consent (optional, default: false)
    - **terms_accepted_version**: Terms of service version ID
    - **privacy_policy_accepted_version**: Privacy policy version ID
    
    Returns user information and sends verification email.
    """
    # Extract IP from X-Forwarded-For header (first IP if multiple)
    ip = ip_address.split(",")[0].strip() if ip_address else None
    
    result = auth_service.register_user(
        username=body.username,
        email=body.email,
        password=body.password,
        name=body.name,
        surname=body.surname,
        marketing_consent=body.marketing_consent,
        terms_accepted_version=body.terms_accepted_version,
        privacy_policy_accepted_version=body.privacy_policy_accepted_version,
        ip_address=ip,
        user_agent=user_agent,
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="User registered successfully. Please check your email for verification.",
        code=status.HTTP_201_CREATED,
    ).model_dump()


# ============================================================================
# SEND VERIFICATION EMAIL
# ============================================================================

@router.post(
    "/send-verification-email",
    summary="Send verification email",
    description="Send email verification link to user",
    status_code=status.HTTP_200_OK,
)
async def send_verification_email(
    request: Request,
    body: SendVerificationEmailRequest,
    auth_service: AuthenticationService = Depends(get_auth_service),
) -> Dict[str, Any]:
    """
    Send verification email to user.
    
    - **user_id**: User ID
    - **email**: Email address to send verification to
    
    Sends a new verification email if the previous one expired.
    """
    result = auth_service.send_verification_email(
        user_id=body.user_id,
        email=body.email,
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="Verification email sent successfully. Please check your inbox.",
        code=status.HTTP_200_OK,
    ).model_dump()


# ============================================================================
# VERIFY EMAIL
# ============================================================================

@router.post(
    "/verify-email",
    summary="Verify email address",
    description="Verify user email address using verification token",
    status_code=status.HTTP_200_OK,
)
async def verify_email(
    request: Request,
    body: VerifyEmailRequest,
    auth_service: AuthenticationService = Depends(get_auth_service),
) -> Dict[str, Any]:
    """
    Verify user email address.
    
    - **verification_token**: Email verification token from email link
    
    Verifies the email address and sends welcome email.
    """
    result = auth_service.verify_email(
        verification_token=body.verification_token,
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="Email verified successfully. Welcome!",
        code=status.HTTP_200_OK,
    ).model_dump()


# ============================================================================
# LOGIN
# ============================================================================

@router.post(
    "/login",
    summary="User login",
    description="Authenticate user and get access/refresh tokens",
    status_code=status.HTTP_200_OK,
)
async def login(
    request: Request,
    body: LoginRequest,
    auth_service: AuthenticationService = Depends(get_auth_service),
    ip_address: Optional[str] = Header(None, alias="X-Forwarded-For"),
    user_agent: Optional[str] = Header(None, alias="User-Agent"),
) -> Dict[str, Any]:
    """
    User login with email/username and password.
    
    - **email_or_username**: Email address or username
    - **password**: Password
    
    Returns access token and refresh token on successful authentication.
    """
    # Extract IP from X-Forwarded-For header (first IP if multiple)
    ip = ip_address.split(",")[0].strip() if ip_address else None
    
    result = auth_service.login(
        email_or_username=body.email_or_username,
        password=body.password,
        ip_address=ip,
        user_agent=user_agent,
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="Login successful",
        code=status.HTTP_200_OK,
    ).model_dump()


# ============================================================================
# LOGOUT
# ============================================================================

@router.post(
    "/logout",
    summary="User logout",
    description="Logout current session and revoke access token",
    status_code=status.HTTP_200_OK,
)
async def logout(
    request: Request,
    current_user: AuthUser = Depends(authenticate_user),
    auth_service: AuthenticationService = Depends(get_auth_service),
) -> Dict[str, Any]:
    """
    Logout current session.
    
    Requires authentication via Bearer token.
    Revokes the current access token.
    """
    result = auth_service.logout(
        access_token=current_user["access_token"],
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="Logged out successfully",
        code=status.HTTP_200_OK,
    ).model_dump()


# ============================================================================
# LOGOUT ALL
# ============================================================================

@router.post(
    "/logout-all",
    summary="Logout all sessions",
    description="Logout from all active sessions and revoke all tokens",
    status_code=status.HTTP_200_OK,
)
async def logout_all(
    request: Request,
    current_user: AuthUser = Depends(authenticate_user),
    auth_service: AuthenticationService = Depends(get_auth_service),
) -> Dict[str, Any]:
    """
    Logout from all active sessions.
    
    Requires authentication via Bearer token.
    Revokes all access tokens for the user.
    """
    result = auth_service.logout_all(
        access_token=current_user["access_token"],
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="Logged out from all sessions successfully",
        code=status.HTTP_200_OK,
    ).model_dump()


# ============================================================================
# REFRESH TOKEN
# ============================================================================

@router.post(
    "/refresh",
    summary="Refresh access token",
    description="Get new access and refresh tokens using refresh token",
    status_code=status.HTTP_200_OK,
)
async def refresh_token(
    request: Request,
    body: RefreshTokenRequest,
    auth_service: AuthenticationService = Depends(get_auth_service),
) -> Dict[str, Any]:
    """
    Refresh access token.
    
    - **refresh_token**: JWT refresh token
    
    Returns new access token and refresh token.
    """
    result = auth_service.refresh_token(
        refresh_token=body.refresh_token,
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="Token refreshed successfully",
        code=status.HTTP_200_OK,
    ).model_dump()

