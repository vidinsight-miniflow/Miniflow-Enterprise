"""User profile service schemas for frontend routes."""

from typing import Optional
from pydantic import BaseModel, Field, EmailStr


# ============================================================================
# PROFILE UPDATE SCHEMAS
# ============================================================================

class UpdateProfileRequest(BaseModel):
    """Request schema for updating user profile."""
    name: Optional[str] = Field(None, max_length=100, description="First name")
    surname: Optional[str] = Field(None, max_length=100, description="Last name")
    avatar_url: Optional[str] = Field(None, description="Avatar URL")
    country_code: Optional[str] = Field(None, description="Country code (ISO format)")
    phone_number: Optional[str] = Field(None, description="Phone number")


class UpdateProfileResponse(BaseModel):
    """Response schema for updating user profile."""
    user_id: str = Field(..., description="User ID")
    name: Optional[str] = Field(None, description="First name")
    surname: Optional[str] = Field(None, description="Last name")
    avatar_url: Optional[str] = Field(None, description="Avatar URL")
    country_code: Optional[str] = Field(None, description="Country code")
    phone_number: Optional[str] = Field(None, description="Phone number")
    phone_verified: bool = Field(False, description="Is phone verified?")


# ============================================================================
# USERNAME CHANGE SCHEMAS
# ============================================================================

class ChangeUsernameRequest(BaseModel):
    """Request schema for changing username."""
    new_username: str = Field(..., min_length=3, max_length=50, description="New username")


class ChangeUsernameResponse(BaseModel):
    """Response schema for changing username."""
    success: bool = Field(..., description="Success status")
    old_username: str = Field(..., description="Old username")
    username: str = Field(..., description="New username")


# ============================================================================
# EMAIL CHANGE SCHEMAS
# ============================================================================

class ChangeEmailRequest(BaseModel):
    """Request schema for changing email."""
    new_email: EmailStr = Field(..., description="New email address")


class ChangeEmailResponse(BaseModel):
    """Response schema for changing email."""
    success: bool = Field(..., description="Success status")
    old_email: str = Field(..., description="Old email address")
    email: str = Field(..., description="New email address")
    is_verified: bool = Field(False, description="Is email verified?")
    sessions_revoked: int = Field(..., description="Number of sessions revoked")
    message: str = Field(..., description="Response message")


# ============================================================================
# PHONE CHANGE SCHEMAS
# ============================================================================

class ChangePhoneRequest(BaseModel):
    """Request schema for changing phone number."""
    country_code: str = Field(..., description="ISO country code (e.g., 'TR', 'US')")
    phone_number: str = Field(..., description="Phone number in E.164 format")


class ChangePhoneResponse(BaseModel):
    """Response schema for changing phone number."""
    success: bool = Field(..., description="Success status")
    country_code: str = Field(..., description="Country code")
    phone_number: str = Field(..., description="Phone number")
    phone_verified: bool = Field(False, description="Is phone verified?")


class VerifyPhoneRequest(BaseModel):
    """Request schema for verifying phone number."""
    verification_code: str = Field(..., description="SMS verification code")


class VerifyPhoneResponse(BaseModel):
    """Response schema for verifying phone number."""
    success: bool = Field(..., description="Success status")
    phone_verified: bool = Field(..., description="Is phone verified?")
    phone_verified_at: str = Field(..., description="Phone verification timestamp (ISO format)")

