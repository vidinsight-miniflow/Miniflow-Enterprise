"""
User route schemas.

Request and Response models for user management endpoints.
"""
from typing import Optional
from pydantic import BaseModel, Field, EmailStr


# ============================================================================
# GET USER
# ============================================================================

# Response is dict from service, no specific schema needed


# ============================================================================
# GET ACTIVE SESSIONS
# ============================================================================

# Response is dict from service, no specific schema needed


# ============================================================================
# REVOKE SESSION
# ============================================================================

# Response is dict from service, no specific schema needed


# ============================================================================
# GET LOGIN HISTORY
# ============================================================================

class GetLoginHistoryQuery(BaseModel):
    """Login history query parameters"""
    limit: int = Field(20, ge=1, le=100, description="Number of records to return (1-100)")


# ============================================================================
# GET PASSWORD HISTORY
# ============================================================================

class GetPasswordHistoryQuery(BaseModel):
    """Password history query parameters"""
    limit: int = Field(10, ge=1, le=50, description="Number of records to return (1-50)")


# ============================================================================
# UPDATE USERNAME
# ============================================================================

class UpdateUsernameRequest(BaseModel):
    """Update username request schema"""
    new_user_name: str = Field(..., min_length=3, max_length=50, description="New username (3-50 characters)")


# ============================================================================
# UPDATE EMAIL
# ============================================================================

class UpdateEmailRequest(BaseModel):
    """Update email request schema"""
    new_email: EmailStr = Field(..., description="New email address")


# ============================================================================
# UPDATE USER INFO
# ============================================================================

class UpdateUserInfoRequest(BaseModel):
    """Update user info request schema"""
    avatar_url: Optional[str] = Field(None, description="Avatar URL")
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="First name")
    surname: Optional[str] = Field(None, min_length=1, max_length=100, description="Last name")
    country_code: Optional[str] = Field(None, max_length=2, description="Country code (ISO 3166-1 alpha-2)")
    phone_number: Optional[str] = Field(None, max_length=20, description="Phone number")


# ============================================================================
# REQUEST USER DELETION
# ============================================================================

class RequestUserDeletionRequest(BaseModel):
    """Request user deletion request schema"""
    reason: str = Field(..., min_length=1, max_length=500, description="Reason for account deletion")


# ============================================================================
# CANCEL USER DELETION
# ============================================================================

# No request body needed


# ============================================================================
# CHANGE PASSWORD
# ============================================================================

class ChangePasswordRequest(BaseModel):
    """Change password request schema"""
    old_password: str = Field(..., min_length=1, description="Current password")
    new_password: str = Field(..., min_length=8, description="New password (minimum 8 characters)")


# ============================================================================
# SEND PASSWORD RESET EMAIL
# ============================================================================

class SendPasswordResetEmailRequest(BaseModel):
    """Send password reset email request schema"""
    email: EmailStr = Field(..., description="Email address to send password reset link")


# ============================================================================
# VALIDATE PASSWORD RESET TOKEN
# ============================================================================

class ValidatePasswordResetTokenRequest(BaseModel):
    """Validate password reset token request schema"""
    password_reset_token: str = Field(..., description="Password reset token")


# ============================================================================
# RESET PASSWORD
# ============================================================================

class ResetPasswordRequest(BaseModel):
    """Reset password request schema"""
    password_reset_token: str = Field(..., description="Password reset token")
    password: str = Field(..., min_length=8, description="New password (minimum 8 characters)")

