"""Custom script schemas for frontend."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# ============================================================================
# CREATE REQUEST/RESPONSE
# ============================================================================

class CreateCustomScriptRequest(BaseModel):
    """Request schema for creating a custom script."""
    name: str = Field(..., description="Script name (unique within workspace)")
    content: str = Field(..., description="Script content (Python code)")
    description: Optional[str] = Field(None, description="Script description")
    category: Optional[str] = Field(None, description="Script category")
    subcategory: Optional[str] = Field(None, description="Script subcategory")
    required_packages: Optional[List[str]] = Field(None, description="Required Python packages")
    input_schema: Optional[Dict[str, Any]] = Field(None, description="Input schema (JSON)")
    output_schema: Optional[Dict[str, Any]] = Field(None, description="Output schema (JSON)")
    tags: Optional[List[str]] = Field(None, description="Tags")
    documentation_url: Optional[str] = Field(None, description="Documentation URL")


class CreateCustomScriptResponse(BaseModel):
    """Response schema for creating a custom script."""
    id: str = Field(..., description="Script ID")


# ============================================================================
# SCRIPT ITEM (for lists)
# ============================================================================

class CustomScriptItem(BaseModel):
    """Schema for script item in lists."""
    id: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    file_size: Optional[int] = None
    approval_status: Optional[str] = None
    test_status: Optional[str] = None
    is_dangerous: bool = False
    tags: Optional[List[str]] = None
    created_at: Optional[str] = None


# ============================================================================
# SCRIPT RESPONSE
# ============================================================================

class CustomScriptResponse(BaseModel):
    """Response schema for script details."""
    id: str
    workspace_id: str
    uploaded_by: str
    name: str
    description: Optional[str] = None
    file_extension: Optional[str] = None
    file_size: Optional[int] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    required_packages: Optional[List[str]] = None
    input_schema: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    documentation_url: Optional[str] = None
    approval_status: Optional[str] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[str] = None
    review_notes: Optional[str] = None
    test_status: Optional[str] = None
    test_coverage: Optional[float] = None
    is_dangerous: bool = False
    created_at: Optional[str] = None


# ============================================================================
# SCRIPT CONTENT RESPONSE
# ============================================================================

class ScriptContentResponse(BaseModel):
    """Response schema for script content."""
    content: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]


# ============================================================================
# WORKSPACE SCRIPTS RESPONSE
# ============================================================================

class WorkspaceScriptsResponse(BaseModel):
    """Response schema for workspace scripts list."""
    workspace_id: str
    scripts: List[CustomScriptItem]
    count: int


# ============================================================================
# UPDATE REQUEST/RESPONSE
# ============================================================================

class UpdateCustomScriptRequest(BaseModel):
    """Request schema for updating script metadata."""
    description: Optional[str] = Field(None, description="New description")
    tags: Optional[List[str]] = Field(None, description="New tags")
    documentation_url: Optional[str] = Field(None, description="New documentation URL")


# ============================================================================
# APPROVAL REQUEST/RESPONSE
# ============================================================================

class ApproveScriptRequest(BaseModel):
    """Request schema for approving a script."""
    review_notes: Optional[str] = Field(None, description="Review notes")


class ApproveScriptResponse(BaseModel):
    """Response schema for approving a script."""
    success: bool
    approval_status: str


class RejectScriptRequest(BaseModel):
    """Request schema for rejecting a script."""
    review_notes: str = Field(..., description="Rejection reason (required)")


class RejectScriptResponse(BaseModel):
    """Response schema for rejecting a script."""
    success: bool
    approval_status: str


class ResetApprovalStatusResponse(BaseModel):
    """Response schema for resetting approval status."""
    success: bool
    approval_status: str


# ============================================================================
# DANGEROUS FLAG RESPONSE
# ============================================================================

class MarkDangerousResponse(BaseModel):
    """Response schema for marking script as dangerous."""
    success: bool
    is_dangerous: bool


class UnmarkDangerousResponse(BaseModel):
    """Response schema for unmarking script as dangerous."""
    success: bool
    is_dangerous: bool


# ============================================================================
# DELETE RESPONSE
# ============================================================================

class DeleteCustomScriptResponse(BaseModel):
    """Response schema for deleting a script."""
    success: bool
    deleted_id: str

