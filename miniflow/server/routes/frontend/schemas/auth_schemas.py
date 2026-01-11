"""Auth service schemas for frontend routes."""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr


# ============================================================================
# REGISTER SCHEMAS
# ============================================================================

class RegisterRequest(BaseModel):
    """Request schema for user registration."""
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., min_length=8, description="Password")
    name: Optional[str] = Field(None, max_length=100, description="First name")
    surname: Optional[str] = Field(None, max_length=100, description="Last name")
    marketing_consent: bool = Field(default=False, description="Marketing consent")
    terms_accepted_version_id: str = Field(..., description="Terms of service version ID")
    privacy_policy_accepted_version_id: str = Field(..., description="Privacy policy version ID")


class RegisterResponse(BaseModel):
    """Response schema for user registration."""
    id: str = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    is_verified: bool = Field(..., description="Is email verified?")


class VerifyEmailRequest(BaseModel):
    """Request schema for email verification."""
    verification_token: str = Field(..., description="Email verification token")


class VerifyEmailResponse(BaseModel):
    """Response schema for email verification."""
    id: str = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    is_verified: bool = Field(..., description="Is email verified?")


class ResendVerificationEmailRequest(BaseModel):
    """Request schema for resending verification email."""
    email: EmailStr = Field(..., description="Email address")


class ResendVerificationEmailResponse(BaseModel):
    """Response schema for resending verification email."""
    email: str = Field(..., description="Email address")
    message: str = Field(..., description="Response message")


# ============================================================================
# LOGIN SCHEMAS
# ============================================================================

class LoginRequest(BaseModel):
    """Request schema for user login."""
    email_or_username: str = Field(..., description="Email or username")
    password: str = Field(..., description="Password")
    device_type: Optional[str] = Field(None, description="Device type")


class LoginResponse(BaseModel):
    """Response schema for user login."""
    id: str = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    access_token: str = Field(..., description="Access token")
    refresh_token: str = Field(..., description="Refresh token")


class LogoutRequest(BaseModel):
    """Request schema for logout."""
    access_token: str = Field(..., description="Access token")


class LogoutResponse(BaseModel):
    """Response schema for logout."""
    success: bool = Field(..., description="Success status")
    message: str = Field(..., description="Response message")


class LogoutAllResponse(BaseModel):
    """Response schema for logout all sessions."""
    success: bool = Field(..., description="Success status")
    sessions_revoked: int = Field(..., description="Number of sessions revoked")


class ValidateTokenRequest(BaseModel):
    """Request schema for token validation."""
    access_token: str = Field(..., description="Access token")


class ValidateTokenResponse(BaseModel):
    """Response schema for token validation."""
    valid: bool = Field(..., description="Is token valid?")
    user_id: Optional[str] = Field(None, description="User ID (if valid)")
    error: Optional[str] = Field(None, description="Error message (if invalid)")


class RefreshTokenRequest(BaseModel):
    """Request schema for token refresh."""
    refresh_token: str = Field(..., description="Refresh token")


class RefreshTokenResponse(BaseModel):
    """Response schema for token refresh."""
    id: str = Field(..., description="User ID")
    access_token: str = Field(..., description="New access token")
    refresh_token: str = Field(..., description="New refresh token")


class LockAccountRequest(BaseModel):
    """Request schema for locking account."""
    user_id: str = Field(..., description="User ID")
    reason: Optional[str] = Field(None, description="Lock reason")
    duration_minutes: Optional[int] = Field(None, description="Lock duration in minutes")


class LockAccountResponse(BaseModel):
    """Response schema for locking account."""
    success: bool = Field(..., description="Success status")
    locked_until: Optional[datetime] = Field(None, description="Lock expiry time")


class UnlockAccountRequest(BaseModel):
    """Request schema for unlocking account."""
    user_id: str = Field(..., description="User ID")


class UnlockAccountResponse(BaseModel):
    """Response schema for unlocking account."""
    success: bool = Field(..., description="Success status")


# ============================================================================
# SESSION SCHEMAS
# ============================================================================

class SessionResponse(BaseModel):
    """Response schema for session data."""
    id: str = Field(..., description="Session ID")
    user_id: str = Field(..., description="User ID")
    access_token_jti: str = Field(..., description="Access token JTI")
    access_token_expires_at: datetime = Field(..., description="Access token expiry")
    refresh_token_jti: str = Field(..., description="Refresh token JTI")
    refresh_token_expires_at: datetime = Field(..., description="Refresh token expiry")
    device_type: Optional[str] = Field(None, description="Device type")
    user_agent: Optional[str] = Field(None, description="User agent")
    ip_address: Optional[str] = Field(None, description="IP address")
    is_revoked: bool = Field(default=False, description="Is session revoked?")
    revoked_at: Optional[datetime] = Field(None, description="Revocation time")
    revocation_reason: Optional[str] = Field(None, description="Revocation reason")
    last_activity_at: Optional[datetime] = Field(None, description="Last activity time")
    refresh_token_last_used_at: Optional[datetime] = Field(None, description="Refresh token last used time")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    @classmethod
    def from_dict(cls, data: dict) -> "SessionResponse":
        """Create from service dict output."""
        standardized = data.copy()
        if "record_id" in standardized:
            standardized["id"] = standardized.pop("record_id")
        if "id" not in standardized and "session_id" in standardized:
            standardized["id"] = standardized.pop("session_id")
        return cls(**standardized)


class SessionListResponse(BaseModel):
    """Response schema for session list."""
    items: list[SessionResponse] = Field(..., description="List of sessions")


class RevokeSessionRequest(BaseModel):
    """Request schema for revoking session."""
    session_id: str = Field(..., description="Session ID")
    reason: Optional[str] = Field(None, description="Revocation reason")


class RevokeSessionResponse(BaseModel):
    """Response schema for revoking session."""
    success: bool = Field(..., description="Success status")
    session_id: str = Field(..., description="Revoked session ID")


class RevokeAllSessionsResponse(BaseModel):
    """Response schema for revoking all sessions."""
    success: bool = Field(..., description="Success status")
    sessions_revoked: int = Field(..., description="Number of sessions revoked")


# ============================================================================
# LOGIN HISTORY SCHEMAS
# ============================================================================

class LoginHistoryResponse(BaseModel):
    """Response schema for login history record."""
    id: str = Field(..., description="History record ID")
    user_id: str = Field(..., description="User ID")
    status: str = Field(..., description="Login status")
    login_method: Optional[str] = Field(None, description="Login method")
    failure_reason: Optional[str] = Field(None, description="Failure reason")
    ip_address: Optional[str] = Field(None, description="IP address")
    user_agent: Optional[str] = Field(None, description="User agent")
    created_at: datetime = Field(..., description="Creation timestamp")

    @classmethod
    def from_dict(cls, data: dict) -> "LoginHistoryResponse":
        """Create from service dict output."""
        standardized = data.copy()
        if "record_id" in standardized:
            standardized["id"] = standardized.pop("record_id")
        if "id" not in standardized and "history_id" in standardized:
            standardized["id"] = standardized.pop("history_id")
        return cls(**standardized)


class LoginHistoryListResponse(BaseModel):
    """Response schema for login history list."""
    items: list[LoginHistoryResponse] = Field(..., description="List of login history records")


class RateLimitCheckResponse(BaseModel):
    """Response schema for rate limit check."""
    user_id: str = Field(..., description="User ID")
    rate_limit_exceeded: bool = Field(..., description="Is rate limit exceeded?")

