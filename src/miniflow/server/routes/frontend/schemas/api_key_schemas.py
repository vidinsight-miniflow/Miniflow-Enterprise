"""API key service schemas for frontend routes."""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


# ============================================================================
# VALIDATE API KEY SCHEMAS
# ============================================================================

class ValidateApiKeyRequest(BaseModel):
    """Request schema for validating API key."""
    full_api_key: str = Field(..., description="Full API key string")
    client_ip: Optional[str] = Field(None, description="Client IP address (for IP whitelist check)")


class ValidateApiKeyResponse(BaseModel):
    """Response schema for API key validation."""
    valid: bool = Field(..., description="Is API key valid?")
    workspace_id: str = Field(..., description="Workspace ID")
    api_key_id: str = Field(..., description="API key ID")
    permissions: Dict[str, Any] = Field(..., description="API key permissions")
    workspace_plan_id: Optional[str] = Field(None, description="Workspace plan ID")


# ============================================================================
# CREATE API KEY SCHEMAS
# ============================================================================

class CreateApiKeyRequest(BaseModel):
    """Request schema for creating API key."""
    name: str = Field(..., min_length=1, description="API key name (unique within workspace)")
    description: Optional[str] = Field(None, max_length=500, description="API key description")
    permissions: Optional[Dict[str, Any]] = Field(None, description="Permissions dictionary")
    expires_at: Optional[str] = Field(None, description="Expiration date (ISO format)")
    tags: Optional[List[str]] = Field(None, description="Tags")
    allowed_ips: Optional[List[str]] = Field(None, description="Allowed IP addresses")
    key_prefix: str = Field(default="sk_live_", description="Key prefix")


class CreateApiKeyResponse(BaseModel):
    """Response schema for creating API key."""
    id: str = Field(..., description="API key ID")
    api_key: str = Field(..., description="Full API key (only shown once!)")


# ============================================================================
# API KEY DETAILS SCHEMAS
# ============================================================================

class ApiKeyItem(BaseModel):
    """Schema for a single API key in list."""
    id: str = Field(..., description="API key ID")
    name: str = Field(..., description="API key name")
    api_key_masked: str = Field(..., description="Masked API key (prefix + ****)")
    description: Optional[str] = Field(None, description="Description")
    is_active: bool = Field(True, description="Is API key active?")
    expires_at: Optional[str] = Field(None, description="Expiration date (ISO format)")
    last_used_at: Optional[str] = Field(None, description="Last used timestamp (ISO format)")
    usage_count: int = Field(0, description="Usage count")


class ApiKeyResponse(BaseModel):
    """Response schema for API key details."""
    id: str = Field(..., description="API key ID")
    workspace_id: str = Field(..., description="Workspace ID")
    owner_id: str = Field(..., description="Owner user ID")
    name: str = Field(..., description="API key name")
    api_key_masked: str = Field(..., description="Masked API key (prefix + ****)")
    description: Optional[str] = Field(None, description="Description")
    permissions: Dict[str, Any] = Field(..., description="Permissions dictionary")
    is_active: bool = Field(True, description="Is API key active?")
    expires_at: Optional[str] = Field(None, description="Expiration date (ISO format)")
    last_used_at: Optional[str] = Field(None, description="Last used timestamp (ISO format)")
    usage_count: int = Field(0, description="Usage count")
    allowed_ips: Optional[List[str]] = Field(None, description="Allowed IP addresses")
    tags: Optional[List[str]] = Field(None, description="Tags")
    created_at: Optional[str] = Field(None, description="Creation timestamp (ISO format)")


class WorkspaceApiKeysResponse(BaseModel):
    """Response schema for workspace API keys list."""
    workspace_id: str = Field(..., description="Workspace ID")
    api_keys: List[ApiKeyItem] = Field(..., description="List of API keys")
    count: int = Field(..., description="Total API key count")


# ============================================================================
# UPDATE API KEY SCHEMAS
# ============================================================================

class UpdateApiKeyRequest(BaseModel):
    """Request schema for updating API key."""
    name: Optional[str] = Field(None, min_length=1, description="New API key name")
    description: Optional[str] = Field(None, max_length=500, description="New description")
    permissions: Optional[Dict[str, Any]] = Field(None, description="New permissions")
    tags: Optional[List[str]] = Field(None, description="New tags")
    allowed_ips: Optional[List[str]] = Field(None, description="New allowed IP addresses")
    expires_at: Optional[str] = Field(None, description="New expiration date (ISO format)")


# ============================================================================
# ACTIVATE/DEACTIVATE API KEY SCHEMAS
# ============================================================================

class ActivateApiKeyResponse(BaseModel):
    """Response schema for activating API key."""
    success: bool = Field(..., description="Success status")
    is_active: bool = Field(True, description="Is API key active?")


class DeactivateApiKeyResponse(BaseModel):
    """Response schema for deactivating API key."""
    success: bool = Field(..., description="Success status")
    is_active: bool = Field(False, description="Is API key active?")


# ============================================================================
# DELETE API KEY SCHEMAS
# ============================================================================

class DeleteApiKeyResponse(BaseModel):
    """Response schema for deleting API key."""
    success: bool = Field(..., description="Success status")
    deleted_id: str = Field(..., description="Deleted API key ID")

