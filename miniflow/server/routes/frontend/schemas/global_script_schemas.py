"""Global script schemas for frontend."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# ============================================================================
# CREATE REQUEST/RESPONSE
# ============================================================================

class CreateGlobalScriptRequest(BaseModel):
    """Request schema for creating a global script."""
    name: str = Field(..., description="Script name (globally unique)")
    category: str = Field(..., description="Script category (required)")
    content: str = Field(..., description="Script content (Python code)")
    description: Optional[str] = Field(None, description="Script description")
    subcategory: Optional[str] = Field(None, description="Script subcategory")
    script_metadata: Optional[Dict[str, Any]] = Field(None, description="Script metadata")
    required_packages: Optional[List[str]] = Field(None, description="Required Python packages")
    input_schema: Optional[Dict[str, Any]] = Field(None, description="Input schema (JSON)")
    output_schema: Optional[Dict[str, Any]] = Field(None, description="Output schema (JSON)")
    tags: Optional[List[str]] = Field(None, description="Tags")
    documentation_url: Optional[str] = Field(None, description="Documentation URL")


class CreateGlobalScriptResponse(BaseModel):
    """Response schema for creating a global script."""
    id: str = Field(..., description="Script ID")


# ============================================================================
# SCRIPT ITEM (for lists)
# ============================================================================

class GlobalScriptItem(BaseModel):
    """Schema for script item in lists."""
    id: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    file_size: Optional[int] = None
    required_packages: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    created_at: Optional[str] = None


# ============================================================================
# SCRIPT RESPONSE
# ============================================================================

class GlobalScriptResponse(BaseModel):
    """Response schema for script details."""
    id: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    file_extension: Optional[str] = None
    file_size: Optional[int] = None
    script_metadata: Optional[Dict[str, Any]] = None
    required_packages: Optional[List[str]] = None
    input_schema: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    documentation_url: Optional[str] = None
    created_at: Optional[str] = None


# ============================================================================
# SCRIPT BY NAME RESPONSE
# ============================================================================

class GlobalScriptByNameResponse(BaseModel):
    """Response schema for script by name."""
    id: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    file_extension: Optional[str] = None
    file_size: Optional[int] = None
    required_packages: Optional[List[str]] = None
    tags: Optional[List[str]] = None


# ============================================================================
# SCRIPT CONTENT RESPONSE
# ============================================================================

class GlobalScriptContentResponse(BaseModel):
    """Response schema for script content."""
    content: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]


# ============================================================================
# ALL SCRIPTS RESPONSE
# ============================================================================

class AllGlobalScriptsResponse(BaseModel):
    """Response schema for all scripts list."""
    scripts: List[GlobalScriptItem]
    count: int


# ============================================================================
# CATEGORIES RESPONSE
# ============================================================================

class CategoriesResponse(BaseModel):
    """Response schema for categories list."""
    categories: List[str]


# ============================================================================
# UPDATE REQUEST/RESPONSE
# ============================================================================

class UpdateGlobalScriptRequest(BaseModel):
    """Request schema for updating script metadata."""
    description: Optional[str] = Field(None, description="New description")
    tags: Optional[List[str]] = Field(None, description="New tags")
    documentation_url: Optional[str] = Field(None, description="New documentation URL")


# ============================================================================
# DELETE RESPONSE
# ============================================================================

class DeleteGlobalScriptResponse(BaseModel):
    """Response schema for deleting a script."""
    success: bool
    deleted_id: str


# ============================================================================
# SEED REQUEST/RESPONSE
# ============================================================================

class SeedScriptsRequest(BaseModel):
    """Request schema for seeding scripts."""
    scripts_data: List[Dict[str, Any]] = Field(..., description="List of script data")


class SeedScriptsResponse(BaseModel):
    """Response schema for seeding scripts."""
    created: int
    skipped: int

