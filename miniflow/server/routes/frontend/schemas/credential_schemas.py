"""Credential service schemas for frontend routes."""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


# ============================================================================
# CREATE API KEY CREDENTIAL SCHEMAS
# ============================================================================

class CreateApiKeyCredentialRequest(BaseModel):
    """Request schema for creating API key credential."""
    name: str = Field(..., min_length=1, description="Credential name (unique within workspace)")
    api_key: str = Field(..., description="API key value")
    provider: str = Field(..., description="Provider name (e.g., OPENAI, GOOGLE, SENDGRID)")
    description: Optional[str] = Field(None, max_length=500, description="Credential description")
    tags: Optional[List[str]] = Field(None, description="Tags")
    expires_at: Optional[str] = Field(None, description="Expiration date (ISO format)")


class CreateSlackCredentialRequest(BaseModel):
    """Request schema for creating Slack credential."""
    name: str = Field(..., min_length=1, description="Credential name (unique within workspace)")
    bot_token: str = Field(..., description="Slack Bot Token (xoxb-...)")
    signing_secret: Optional[str] = Field(None, description="Signing Secret")
    app_token: Optional[str] = Field(None, description="App-Level Token (xapp-...)")
    description: Optional[str] = Field(None, max_length=500, description="Credential description")
    tags: Optional[List[str]] = Field(None, description="Tags")
    expires_at: Optional[str] = Field(None, description="Expiration date (ISO format)")


class CreateCredentialResponse(BaseModel):
    """Response schema for creating credential."""
    id: str = Field(..., description="Credential ID")


# ============================================================================
# CREDENTIAL DETAILS SCHEMAS
# ============================================================================

class CredentialItem(BaseModel):
    """Schema for a single credential in list."""
    id: str = Field(..., description="Credential ID")
    name: str = Field(..., description="Credential name")
    credential_type: Optional[str] = Field(None, description="Credential type")
    credential_provider: Optional[str] = Field(None, description="Provider name")
    description: Optional[str] = Field(None, description="Description")
    is_active: bool = Field(True, description="Is credential active?")
    expires_at: Optional[str] = Field(None, description="Expiration date (ISO format)")
    last_used_at: Optional[str] = Field(None, description="Last used timestamp (ISO format)")
    tags: Optional[List[str]] = Field(None, description="Tags")


class CredentialResponse(BaseModel):
    """Response schema for credential details."""
    id: str = Field(..., description="Credential ID")
    workspace_id: str = Field(..., description="Workspace ID")
    owner_id: str = Field(..., description="Owner user ID")
    name: str = Field(..., description="Credential name")
    credential_type: Optional[str] = Field(None, description="Credential type")
    credential_provider: Optional[str] = Field(None, description="Provider name")
    description: Optional[str] = Field(None, description="Description")
    is_active: bool = Field(True, description="Is credential active?")
    expires_at: Optional[str] = Field(None, description="Expiration date (ISO format)")
    last_used_at: Optional[str] = Field(None, description="Last used timestamp (ISO format)")
    tags: Optional[List[str]] = Field(None, description="Tags")
    created_at: Optional[str] = Field(None, description="Creation timestamp (ISO format)")
    credential_data: Optional[Dict[str, Any]] = Field(None, description="Credential data (only if include_secret=True)")


class WorkspaceCredentialsResponse(BaseModel):
    """Response schema for workspace credentials list."""
    workspace_id: str = Field(..., description="Workspace ID")
    credentials: List[CredentialItem] = Field(..., description="List of credentials")
    count: int = Field(..., description="Total credential count")


# ============================================================================
# UPDATE CREDENTIAL SCHEMAS
# ============================================================================

class UpdateCredentialRequest(BaseModel):
    """Request schema for updating credential."""
    name: Optional[str] = Field(None, min_length=1, description="New credential name")
    description: Optional[str] = Field(None, max_length=500, description="New description")
    tags: Optional[List[str]] = Field(None, description="New tags")


# ============================================================================
# ACTIVATE/DEACTIVATE CREDENTIAL SCHEMAS
# ============================================================================

class ActivateCredentialResponse(BaseModel):
    """Response schema for activating credential."""
    success: bool = Field(..., description="Success status")
    is_active: bool = Field(True, description="Is credential active?")


class DeactivateCredentialResponse(BaseModel):
    """Response schema for deactivating credential."""
    success: bool = Field(..., description="Success status")
    is_active: bool = Field(False, description="Is credential active?")


# ============================================================================
# DELETE CREDENTIAL SCHEMAS
# ============================================================================

class DeleteCredentialResponse(BaseModel):
    """Response schema for deleting credential."""
    success: bool = Field(..., description="Success status")
    deleted_id: str = Field(..., description="Deleted credential ID")

