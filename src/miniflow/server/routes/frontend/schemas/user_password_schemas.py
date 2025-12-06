"""User password service schemas for frontend routes."""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr


# ============================================================================
# CHANGE PASSWORD SCHEMAS
# ============================================================================

class ChangePasswordRequest(BaseModel):
    """Request schema for changing password."""
    old_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")


class ChangePasswordResponse(BaseModel):
    """Response schema for changing password."""
    success: bool = Field(..., description="Success status")
    message: str = Field(..., description="Response message")


# ============================================================================
# PASSWORD RESET SCHEMAS
# ============================================================================

class SendPasswordResetEmailRequest(BaseModel):
    """Request schema for sending password reset email."""
    email: EmailStr = Field(..., description="Email address")


class SendPasswordResetEmailResponse(BaseModel):
    """Response schema for sending password reset email."""
    success: bool = Field(..., description="Success status")
    message: str = Field(..., description="Response message")


class ValidatePasswordResetTokenRequest(BaseModel):
    """Request schema for validating password reset token."""
    token: str = Field(..., description="Password reset token")


class ValidatePasswordResetTokenResponse(BaseModel):
    """Response schema for validating password reset token."""
    valid: bool = Field(..., description="Is token valid?")


class ResetPasswordRequest(BaseModel):
    """Request schema for resetting password."""
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, description="New password")


class ResetPasswordResponse(BaseModel):
    """Response schema for resetting password."""
    success: bool = Field(..., description="Success status")
    message: str = Field(..., description="Response message")


# ============================================================================
# PASSWORD HISTORY SCHEMAS
# ============================================================================

class PasswordHistoryItem(BaseModel):
    """Schema for a single password history record."""
    id: str = Field(..., description="History record ID")
    change_reason: str = Field(..., description="Reason for password change (VOLUNTARY, RESET)")
    changed_from_ip: Optional[str] = Field(None, description="IP address where change was made")
    changed_from_device: Optional[str] = Field(None, description="Device where change was made")
    created_at: Optional[str] = Field(None, description="Change timestamp (ISO format)")


class PasswordHistoryResponse(BaseModel):
    """Response schema for password history."""
    user_id: str = Field(..., description="User ID")
    total_records: int = Field(..., description="Total number of history records")
    history: List[PasswordHistoryItem] = Field(..., description="List of password history records")

