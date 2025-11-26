"""
API Key request schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class CreateApiKeyRequest(BaseModel):
    """Request schema for creating an API key."""
    name: str = Field(..., description="API key name", min_length=1)
    key_prefix: Optional[str] = Field("sk_live_", description="API key prefix (default: sk_live_)")
    description: Optional[str] = Field(None, description="Optional API key description")
    permissions: Optional[Dict[str, Any]] = Field(None, description="Optional custom permissions")
    expires_at: Optional[datetime] = Field(None, description="Optional expiration date")
    tags: Optional[List[str]] = Field(None, description="Optional tags")
    allowed_ips: Optional[List[str]] = Field(None, description="Optional allowed IP addresses")


class UpdateApiKeyRequest(BaseModel):
    """Request schema for updating an API key."""
    name: Optional[str] = Field(None, description="API key name", min_length=1)
    description: Optional[str] = Field(None, description="API key description")
    permissions: Optional[Dict[str, Any]] = Field(None, description="Custom permissions")
    tags: Optional[List[str]] = Field(None, description="Tags")
    allowed_ips: Optional[List[str]] = Field(None, description="Allowed IP addresses")
    is_active: Optional[bool] = Field(None, description="Whether the API key is active")
    expires_at: Optional[datetime] = Field(None, description="Expiration date")

