"""User management service schemas for frontend routes."""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


# ============================================================================
# USER DETAILS SCHEMAS
# ============================================================================

class UserDetailsResponse(BaseModel):
    """Response schema for user details."""
    id: str = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    name: Optional[str] = Field(None, description="First name")
    surname: Optional[str] = Field(None, description="Last name")
    avatar_url: Optional[str] = Field(None, description="Avatar URL")
    country_code: Optional[str] = Field(None, description="Country code")
    phone_number: Optional[str] = Field(None, description="Phone number")
    phone_verified: bool = Field(False, description="Is phone verified?")
    is_verified: bool = Field(False, description="Is email verified?")
    is_active: bool = Field(True, description="Is account active?")
    is_locked: bool = Field(False, description="Is account locked?")
    locked_until: Optional[datetime] = Field(None, description="Account locked until")
    marketing_consent: bool = Field(False, description="Marketing consent")
    marketing_consent_at: Optional[datetime] = Field(None, description="Marketing consent date")
    created_at: datetime = Field(..., description="Account creation date")
    updated_at: datetime = Field(..., description="Last update date")
    last_login_at: Optional[datetime] = Field(None, description="Last login date")
    deletion_requested_at: Optional[datetime] = Field(None, description="Deletion request date")
    deletion_scheduled_for: Optional[datetime] = Field(None, description="Scheduled deletion date")

    @classmethod
    def from_dict(cls, data: dict):
        """Standardize dict keys (record_id -> id)."""
        if 'record_id' in data:
            data['id'] = data.pop('record_id')
        return cls(**data)


# ============================================================================
# USER PREFERENCES SCHEMAS
# ============================================================================

class UserPreferenceItem(BaseModel):
    """Schema for a single user preference."""
    id: str = Field(..., description="Preference ID")
    key: str = Field(..., description="Preference key")
    value: Any = Field(..., description="Preference value")
    category: Optional[str] = Field(None, description="Preference category")
    description: Optional[str] = Field(None, description="Preference description")


class UserPreferencesResponse(BaseModel):
    """Response schema for all user preferences."""
    user_id: str = Field(..., description="User ID")
    preferences: List[UserPreferenceItem] = Field(..., description="List of preferences")


class UserPreferenceResponse(BaseModel):
    """Response schema for a single user preference."""
    id: str = Field(..., description="Preference ID")
    user_id: str = Field(..., description="User ID")
    key: str = Field(..., description="Preference key")
    value: Any = Field(..., description="Preference value")
    category: Optional[str] = Field(None, description="Preference category")
    description: Optional[str] = Field(None, description="Preference description")


class UserPreferencesByCategoryResponse(BaseModel):
    """Response schema for preferences by category."""
    user_id: str = Field(..., description="User ID")
    category: str = Field(..., description="Category name")
    preferences: List[UserPreferenceItem] = Field(..., description="List of preferences in category")


class SetUserPreferenceRequest(BaseModel):
    """Request schema for setting user preference."""
    key: str = Field(..., description="Preference key")
    value: Any = Field(..., description="Preference value (string, number, boolean, object, array)")
    category: Optional[str] = Field(None, description="Preference category")
    description: Optional[str] = Field(None, description="Preference description")


class DeleteUserPreferenceResponse(BaseModel):
    """Response schema for deleting user preference."""
    success: bool = Field(..., description="Success status")
    deleted_key: str = Field(..., description="Deleted preference key")


# ============================================================================
# ACCOUNT DELETION SCHEMAS
# ============================================================================

class RequestAccountDeletionRequest(BaseModel):
    """Request schema for account deletion."""
    reason: Optional[str] = Field(None, description="Deletion reason")


class RequestAccountDeletionResponse(BaseModel):
    """Response schema for account deletion request."""
    user_id: str = Field(..., description="User ID")
    deletion_requested_at: str = Field(..., description="Deletion request timestamp (ISO format)")
    deletion_scheduled_for: str = Field(..., description="Scheduled deletion timestamp (ISO format)")
    deletion_reason: Optional[str] = Field(None, description="Deletion reason")
    grace_period_days: int = Field(..., description="Grace period in days")


class CancelAccountDeletionResponse(BaseModel):
    """Response schema for canceling account deletion."""
    success: bool = Field(..., description="Success status")
    message: str = Field(..., description="Response message")


class DeletionStatusResponse(BaseModel):
    """Response schema for deletion status."""
    has_pending_deletion: bool = Field(..., description="Has pending deletion request?")
    deletion_requested_at: Optional[str] = Field(None, description="Deletion request timestamp (ISO format)")
    deletion_scheduled_for: Optional[str] = Field(None, description="Scheduled deletion timestamp (ISO format)")
    days_remaining: Optional[int] = Field(None, description="Days remaining until deletion")


# ============================================================================
# MARKETING CONSENT SCHEMAS
# ============================================================================

class UpdateMarketingConsentRequest(BaseModel):
    """Request schema for updating marketing consent."""
    consent: bool = Field(..., description="Marketing consent (True/False)")


class UpdateMarketingConsentResponse(BaseModel):
    """Response schema for updating marketing consent."""
    success: bool = Field(..., description="Success status")
    marketing_consent: bool = Field(..., description="Marketing consent status")
    marketing_consent_at: Optional[str] = Field(None, description="Marketing consent timestamp (ISO format)")

