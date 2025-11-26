"""
User management routes.

Handles user profile, sessions, password management, and account operations.
"""
from fastapi import APIRouter, Depends, Request, status, Header, Query, Path
from typing import Dict, Any, Optional

from src.miniflow.server.dependencies import get_user_service, get_workspace_member_service
from src.miniflow.services import UserService, WorkspaceMemberService
from src.miniflow.server.helpers import authenticate_user, AuthUser
from src.miniflow.server.schemas.base_schema import create_success_response
from src.miniflow.server.schemas.routes.user_schemas import (
    UpdateUsernameRequest,
    UpdateEmailRequest,
    UpdateUserInfoRequest,
    RequestUserDeletionRequest,
    ChangePasswordRequest,
    SendPasswordResetEmailRequest,
    ValidatePasswordResetTokenRequest,
    ResetPasswordRequest,
)

router = APIRouter(prefix="/users", tags=["users"])


# ============================================================================
# GET USER
# ============================================================================

@router.get(
    "/{user_id}",
    summary="Get user profile",
    description="Get user profile information by user ID",
    status_code=status.HTTP_200_OK,
)
async def get_user(
    request: Request,
    user_id: str = Path(..., description="User ID"),
    current_user: AuthUser = Depends(authenticate_user),
    user_service: UserService = Depends(get_user_service),
) -> Dict[str, Any]:
    """
    Get user profile information.
    
    - **user_id**: User ID (path parameter)
    
    Requires authentication. Users can only view their own profile.
    """
    # Security: Users can only view their own profile
    if current_user["user_id"] != user_id:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own profile"
        )
    
    result = user_service.get_user(user_id=user_id)
    
    return create_success_response(
        request=request,
        data=result,
        message="User profile retrieved successfully",
        code=status.HTTP_200_OK,
    ).model_dump()


# ============================================================================
# GET ACTIVE SESSIONS
# ============================================================================

@router.get(
    "/{user_id}/sessions",
    summary="Get active user sessions",
    description="Get all active sessions for a user",
    status_code=status.HTTP_200_OK,
)
async def get_active_user_sessions(
    request: Request,
    user_id: str = Path(..., description="User ID"),
    current_user: AuthUser = Depends(authenticate_user),
    user_service: UserService = Depends(get_user_service),
) -> Dict[str, Any]:
    """
    Get all active sessions for a user.
    
    - **user_id**: User ID (path parameter)
    
    Requires authentication. Users can only view their own sessions.
    """
    # Security: Users can only view their own sessions
    if current_user["user_id"] != user_id:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own sessions"
        )
    
    result = user_service.get_active_user_sessions(user_id=user_id)
    
    return create_success_response(
        request=request,
        data=result,
        message="Active sessions retrieved successfully",
        code=status.HTTP_200_OK,
    ).model_dump()


# ============================================================================
# REVOKE SPECIFIC SESSION
# ============================================================================

@router.delete(
    "/{user_id}/sessions/{session_id}",
    summary="Revoke specific session",
    description="Revoke a specific user session by session ID",
    status_code=status.HTTP_200_OK,
)
async def revoke_specific_session(
    request: Request,
    user_id: str = Path(..., description="User ID"),
    session_id: str = Path(..., description="Session ID"),
    current_user: AuthUser = Depends(authenticate_user),
    user_service: UserService = Depends(get_user_service),
) -> Dict[str, Any]:
    """
    Revoke a specific user session.
    
    - **user_id**: User ID (path parameter)
    - **session_id**: Session ID to revoke (path parameter)
    
    Requires authentication. Users can only revoke their own sessions.
    """
    # Security: Users can only revoke their own sessions
    if current_user["user_id"] != user_id:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only revoke your own sessions"
        )
    
    result = user_service.revoke_specific_session(
        user_id=user_id,
        session_id=session_id,
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="Session revoked successfully",
        code=status.HTTP_200_OK,
    ).model_dump()


# ============================================================================
# GET LOGIN HISTORY
# ============================================================================

@router.get(
    "/{user_id}/login-history",
    summary="Get login history",
    description="Get user login history with pagination",
    status_code=status.HTTP_200_OK,
)
async def get_login_history(
    request: Request,
    user_id: str = Path(..., description="User ID"),
    limit: int = Query(20, ge=1, le=100, description="Number of records to return (1-100)"),
    current_user: AuthUser = Depends(authenticate_user),
    user_service: UserService = Depends(get_user_service),
) -> Dict[str, Any]:
    """
    Get user login history.
    
    - **user_id**: User ID (path parameter)
    - **limit**: Number of records to return (query parameter, default: 20, max: 100)
    
    Requires authentication. Users can only view their own login history.
    """
    # Security: Users can only view their own login history
    if current_user["user_id"] != user_id:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own login history"
        )
    
    result = user_service.get_login_history(
        user_id=user_id,
        limit=limit,
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="Login history retrieved successfully",
        code=status.HTTP_200_OK,
    ).model_dump()


# ============================================================================
# GET PASSWORD HISTORY
# ============================================================================

@router.get(
    "/{user_id}/password-history",
    summary="Get password history",
    description="Get user password change history",
    status_code=status.HTTP_200_OK,
)
async def get_password_history(
    request: Request,
    user_id: str = Path(..., description="User ID"),
    limit: int = Query(10, ge=1, le=50, description="Number of records to return (1-50)"),
    current_user: AuthUser = Depends(authenticate_user),
    user_service: UserService = Depends(get_user_service),
) -> Dict[str, Any]:
    """
    Get user password change history.
    
    - **user_id**: User ID (path parameter)
    - **limit**: Number of records to return (query parameter, default: 10, max: 50)
    
    Requires authentication. Users can only view their own password history.
    """
    # Security: Users can only view their own password history
    if current_user["user_id"] != user_id:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own password history"
        )
    
    result = user_service.get_password_history(
        user_id=user_id,
        limit=limit,
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="Password history retrieved successfully",
        code=status.HTTP_200_OK,
    ).model_dump()


# ============================================================================
# UPDATE USERNAME
# ============================================================================

@router.put(
    "/{user_id}/username",
    summary="Update username",
    description="Update user username",
    status_code=status.HTTP_200_OK,
)
async def update_username(
    request: Request,
    user_id: str = Path(..., description="User ID"),
    body: UpdateUsernameRequest = ...,
    current_user: AuthUser = Depends(authenticate_user),
    user_service: UserService = Depends(get_user_service),
) -> Dict[str, Any]:
    """
    Update user username.
    
    - **user_id**: User ID (path parameter)
    - **new_user_name**: New username (3-50 characters)
    
    Requires authentication. Users can only update their own username.
    """
    # Security: Users can only update their own username
    if current_user["user_id"] != user_id:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own username"
        )
    
    result = user_service.update_username(
        user_id=user_id,
        new_user_name=body.new_user_name,
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="Username updated successfully",
        code=status.HTTP_200_OK,
    ).model_dump()


# ============================================================================
# UPDATE EMAIL
# ============================================================================

@router.put(
    "/{user_id}/email",
    summary="Update email",
    description="Update user email address (requires verification)",
    status_code=status.HTTP_200_OK,
)
async def update_email(
    request: Request,
    user_id: str = Path(..., description="User ID"),
    body: UpdateEmailRequest = ...,
    current_user: AuthUser = Depends(authenticate_user),
    user_service: UserService = Depends(get_user_service),
) -> Dict[str, Any]:
    """
    Update user email address.
    
    - **user_id**: User ID (path parameter)
    - **new_email**: New email address
    
    Requires authentication. Users can only update their own email.
    Sends verification email to the new address.
    """
    # Security: Users can only update their own email
    if current_user["user_id"] != user_id:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own email"
        )
    
    result = user_service.update_email(
        user_id=user_id,
        new_email=body.new_email,
    )
    
    return create_success_response(
        request=request,
        data=result,
        message=result.get("message", "Email updated successfully. Please verify your new email address."),
        code=status.HTTP_200_OK,
    ).model_dump()


# ============================================================================
# UPDATE USER INFO
# ============================================================================

@router.patch(
    "/{user_id}",
    summary="Update user info",
    description="Update user profile information (avatar, name, surname, country, phone)",
    status_code=status.HTTP_200_OK,
)
async def update_user_info(
    request: Request,
    user_id: str = Path(..., description="User ID"),
    body: UpdateUserInfoRequest = ...,
    current_user: AuthUser = Depends(authenticate_user),
    user_service: UserService = Depends(get_user_service),
) -> Dict[str, Any]:
    """
    Update user profile information.
    
    - **user_id**: User ID (path parameter)
    - **avatar_url**: Avatar URL (optional)
    - **name**: First name (optional)
    - **surname**: Last name (optional)
    - **country_code**: Country code (optional, ISO 3166-1 alpha-2)
    - **phone_number**: Phone number (optional)
    
    Requires authentication. Users can only update their own profile.
    """
    # Security: Users can only update their own profile
    if current_user["user_id"] != user_id:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own profile"
        )
    
    result = user_service.update_user_info(
        user_id=user_id,
        avatar_url=body.avatar_url,
        name=body.name,
        surname=body.surname,
        country_code=body.country_code,
        phone_number=body.phone_number,
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="User info updated successfully",
        code=status.HTTP_200_OK,
    ).model_dump()


# ============================================================================
# REQUEST USER DELETION
# ============================================================================

@router.post(
    "/{user_id}/deletion-request",
    summary="Request user account deletion",
    description="Request account deletion (30 day grace period)",
    status_code=status.HTTP_200_OK,
)
async def request_user_deletion(
    request: Request,
    user_id: str = Path(..., description="User ID"),
    body: RequestUserDeletionRequest = ...,
    current_user: AuthUser = Depends(authenticate_user),
    user_service: UserService = Depends(get_user_service),
) -> Dict[str, Any]:
    """
    Request user account deletion.
    
    - **user_id**: User ID (path parameter)
    - **reason**: Reason for account deletion (1-500 characters)
    
    Requires authentication. Users can only request deletion of their own account.
    Account will be deleted after 30 days unless cancelled.
    """
    # Security: Users can only request deletion of their own account
    if current_user["user_id"] != user_id:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only request deletion of your own account"
        )
    
    result = user_service.request_user_deletion(
        user_id=user_id,
        reason=body.reason,
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="Account deletion requested successfully. Your account will be deleted in 30 days unless cancelled.",
        code=status.HTTP_200_OK,
    ).model_dump()


# ============================================================================
# CANCEL USER DELETION
# ============================================================================

@router.delete(
    "/{user_id}/deletion-request",
    summary="Cancel user account deletion",
    description="Cancel pending account deletion request",
    status_code=status.HTTP_200_OK,
)
async def cancel_user_deletion(
    request: Request,
    user_id: str = Path(..., description="User ID"),
    current_user: AuthUser = Depends(authenticate_user),
    user_service: UserService = Depends(get_user_service),
) -> Dict[str, Any]:
    """
    Cancel pending account deletion request.
    
    - **user_id**: User ID (path parameter)
    
    Requires authentication. Users can only cancel deletion of their own account.
    """
    # Security: Users can only cancel deletion of their own account
    if current_user["user_id"] != user_id:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only cancel deletion of your own account"
        )
    
    result = user_service.cancel_user_deletion(user_id=user_id)
    
    return create_success_response(
        request=request,
        data=result,
        message="Account deletion request cancelled successfully",
        code=status.HTTP_200_OK,
    ).model_dump()


# ============================================================================
# CHANGE PASSWORD
# ============================================================================

@router.put(
    "/{user_id}/password",
    summary="Change password",
    description="Change user password (requires old password)",
    status_code=status.HTTP_200_OK,
)
async def change_password(
    request: Request,
    user_id: str = Path(..., description="User ID"),
    body: ChangePasswordRequest = ...,
    current_user: AuthUser = Depends(authenticate_user),
    user_service: UserService = Depends(get_user_service),
    ip_address: Optional[str] = Header(None, alias="X-Forwarded-For"),
    user_agent: Optional[str] = Header(None, alias="User-Agent"),
) -> Dict[str, Any]:
    """
    Change user password.
    
    - **user_id**: User ID (path parameter)
    - **old_password**: Current password
    - **new_password**: New password (minimum 8 characters)
    
    Requires authentication. Users can only change their own password.
    """
    # Security: Users can only change their own password
    if current_user["user_id"] != user_id:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only change your own password"
        )
    
    # Extract IP from X-Forwarded-For header (first IP if multiple)
    ip = ip_address.split(",")[0].strip() if ip_address else None
    
    result = user_service.change_password(
        user_id=user_id,
        old_password=body.old_password,
        new_password=body.new_password,
        ip_address=ip,
        user_agent=user_agent,
    )
    
    return create_success_response(
        request=request,
        data=result,
        message=result.get("message", "Password changed successfully"),
        code=status.HTTP_200_OK,
    ).model_dump()


# ============================================================================
# SEND PASSWORD RESET EMAIL (PUBLIC)
# ============================================================================

@router.post(
    "/password-reset/request",
    summary="Request password reset",
    description="Send password reset email (public endpoint)",
    status_code=status.HTTP_200_OK,
)
async def send_password_reset_email(
    request: Request,
    body: SendPasswordResetEmailRequest = ...,
    user_service: UserService = Depends(get_user_service),
) -> Dict[str, Any]:
    """
    Request password reset email.
    
    - **email**: Email address to send password reset link
    
    Public endpoint. Does not reveal if email exists in system.
    """
    result = user_service.send_password_reset_email(email=body.email)
    
    return create_success_response(
        request=request,
        data=result,
        message=result.get("message", "If an account with that email exists, a password reset link has been sent."),
        code=status.HTTP_200_OK,
    ).model_dump()


# ============================================================================
# VALIDATE PASSWORD RESET TOKEN (PUBLIC)
# ============================================================================

@router.post(
    "/password-reset/validate",
    summary="Validate password reset token",
    description="Validate password reset token before resetting password (public endpoint)",
    status_code=status.HTTP_200_OK,
)
async def validate_password_reset_token(
    request: Request,
    body: ValidatePasswordResetTokenRequest = ...,
    user_service: UserService = Depends(get_user_service),
) -> Dict[str, Any]:
    """
    Validate password reset token.
    
    - **password_reset_token**: Password reset token from email link
    
    Public endpoint. Validates token before allowing password reset.
    """
    result = user_service.validate_password_reset_token(
        password_reset_token=body.password_reset_token,
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="Password reset token is valid",
        code=status.HTTP_200_OK,
    ).model_dump()


# ============================================================================
# RESET PASSWORD (PUBLIC)
# ============================================================================

@router.post(
    "/password-reset/reset",
    summary="Reset password",
    description="Reset password using reset token (public endpoint)",
    status_code=status.HTTP_200_OK,
)
async def reset_password(
    request: Request,
    body: ResetPasswordRequest = ...,
    user_service: UserService = Depends(get_user_service),
    ip_address: Optional[str] = Header(None, alias="X-Forwarded-For"),
    user_agent: Optional[str] = Header(None, alias="User-Agent"),
) -> Dict[str, Any]:
    """
    Reset password using reset token.
    
    - **password_reset_token**: Password reset token from email link
    - **password**: New password (minimum 8 characters)
    
    Public endpoint. Resets password without requiring authentication.
    """
    # Extract IP from X-Forwarded-For header (first IP if multiple)
    ip = ip_address.split(",")[0].strip() if ip_address else None
    
    result = user_service.reset_password(
        password_reset_token=body.password_reset_token,
        password=body.password,
        ip_address=ip,
        user_agent=user_agent,
    )
    
    return create_success_response(
        request=request,
        data=result,
        message=result.get("message", "Password reset successfully"),
        code=status.HTTP_200_OK,
    ).model_dump()


# ============================================================================
# GET USER WORKSPACES
# ============================================================================

@router.get(
    "/{user_id}/workspaces",
    summary="Get user workspaces",
    description="Get all workspaces owned by or where user is a member",
    status_code=status.HTTP_200_OK,
)
async def get_user_workspaces(
    request: Request,
    user_id: str = Path(..., description="User ID"),
    current_user: AuthUser = Depends(authenticate_user),
    workspace_member_service: WorkspaceMemberService = Depends(get_workspace_member_service),
) -> Dict[str, Any]:
    """
    Get all workspaces for a user.
    
    - **user_id**: User ID (path parameter)
    
    Requires authentication. Users can only view their own workspaces.
    Returns both owned workspaces and memberships.
    """
    # Security: Users can only view their own workspaces
    if current_user["user_id"] != user_id:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own workspaces"
        )
    
    result = workspace_member_service.get_user_workspaces(user_id=user_id)
    
    return create_success_response(
        request=request,
        data=result,
        message="User workspaces retrieved successfully",
        code=status.HTTP_200_OK,
    ).model_dump()

