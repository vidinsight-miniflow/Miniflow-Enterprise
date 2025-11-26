"""
Credential request schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from src.miniflow.database.models.enums import CredentialProvider


class CreateApiKeyCredentialRequest(BaseModel):
    """Request schema for creating an API key credential."""
    name: str = Field(..., description="Credential name", min_length=1)
    api_key: str = Field(..., description="API key value", min_length=1)
    credential_provider: CredentialProvider = Field(..., description="Credential provider (e.g., GOOGLE, MICROSOFT, GITHUB)")
    description: Optional[str] = Field(None, description="Optional credential description")
    tags: Optional[List[str]] = Field(None, description="Optional tags")
    expires_at: Optional[datetime] = Field(None, description="Optional expiration date")
    is_active: bool = Field(True, description="Whether the credential is active")

