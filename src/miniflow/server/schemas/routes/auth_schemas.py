"""
Authentication route schemas.

Request and Response models for authentication endpoints.
"""
from typing import Optional
from pydantic import BaseModel, Field, EmailStr


# ============================================================================
# REGISTER USER
# ============================================================================

class RegisterUserRequest(BaseModel):
    """User registration request schema"""
    username: str = Field(..., min_length=3, max_length=50, description="Username (3-50 characters)")
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., min_length=8, description="Password (minimum 8 characters)")
    name: str = Field(..., min_length=1, max_length=100, description="First name")
    surname: str = Field(..., min_length=1, max_length=100, description="Last name")
    marketing_consent: bool = Field(False, description="Marketing consent")
    terms_accepted_version: str = Field(..., description="Terms of service version ID")
    privacy_policy_accepted_version: str = Field(..., description="Privacy policy version ID")


class RegisterUserResponse(BaseModel):
    """User registration response schema"""
    user_id: str = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    is_verified: bool = Field(..., description="Email verification status")


# ============================================================================
# SEND VERIFICATION EMAIL
# ============================================================================

class SendVerificationEmailRequest(BaseModel):
    """Send verification email request schema"""
    user_id: str = Field(..., description="User ID")
    email: EmailStr = Field(..., description="Email address to send verification to")


class SendVerificationEmailResponse(BaseModel):
    """Send verification email response schema"""
    user_id: str = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    is_verified: bool = Field(..., description="Email verification status")


# ============================================================================
# VERIFY EMAIL
# ============================================================================

class VerifyEmailRequest(BaseModel):
    """Email verification request schema"""
    verification_token: str = Field(..., description="Email verification token")


class VerifyEmailResponse(BaseModel):
    """Email verification response schema"""
    user_id: str = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    is_verified: bool = Field(..., description="Email verification status")


# ============================================================================
# LOGIN
# ============================================================================

class LoginRequest(BaseModel):
    """User login request schema"""
    email_or_username: str = Field(..., description="Email address or username")
    password: str = Field(..., description="Password")


class LoginResponse(BaseModel):
    """User login response schema"""
    user_id: str = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")


# ============================================================================
# LOGOUT
# ============================================================================

class LogoutResponse(BaseModel):
    """User logout response schema"""
    success: bool = Field(..., description="Logout success status")
    message: str = Field(..., description="Logout message")


# ============================================================================
# LOGOUT ALL
# ============================================================================

class LogoutAllResponse(BaseModel):
    """User logout all sessions response schema"""
    success: bool = Field(..., description="Logout success status")
    sessions_revoked: int = Field(..., description="Number of sessions revoked")


# ============================================================================
# REFRESH TOKEN
# ============================================================================

class RefreshTokenRequest(BaseModel):
    """Refresh token request schema"""
    refresh_token: str = Field(..., description="JWT refresh token")


class RefreshTokenResponse(BaseModel):
    """Refresh token response schema"""
    user_id: str = Field(..., description="User ID")
    access_token: str = Field(..., description="New JWT access token")
    refresh_token: str = Field(..., description="New JWT refresh token")

