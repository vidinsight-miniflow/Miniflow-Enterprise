"""Script testing schemas for frontend."""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


# ============================================================================
# MARK TEST PASSED REQUEST/RESPONSE
# ============================================================================

class MarkTestPassedRequest(BaseModel):
    """Request schema for marking test as passed."""
    test_results: Optional[Dict[str, Any]] = Field(None, description="Test results")
    test_coverage: Optional[float] = Field(None, ge=0, le=100, description="Test coverage percentage (0-100)")


class MarkTestPassedResponse(BaseModel):
    """Response schema for marking test as passed."""
    success: bool
    test_status: str
    test_coverage: Optional[float] = None


# ============================================================================
# MARK TEST FAILED REQUEST/RESPONSE
# ============================================================================

class MarkTestFailedRequest(BaseModel):
    """Request schema for marking test as failed."""
    test_results: Dict[str, Any] = Field(..., description="Test results with error details")
    test_coverage: Optional[float] = Field(None, ge=0, le=100, description="Test coverage percentage (0-100)")


class MarkTestFailedResponse(BaseModel):
    """Response schema for marking test as failed."""
    success: bool
    test_status: str


# ============================================================================
# MARK TEST SKIPPED REQUEST/RESPONSE
# ============================================================================

class MarkTestSkippedRequest(BaseModel):
    """Request schema for marking test as skipped."""
    reason: Optional[str] = Field(None, description="Skip reason")


class MarkTestSkippedResponse(BaseModel):
    """Response schema for marking test as skipped."""
    success: bool
    test_status: str
    reason: Optional[str] = None


# ============================================================================
# RESET TEST STATUS RESPONSE
# ============================================================================

class ResetTestStatusResponse(BaseModel):
    """Response schema for resetting test status."""
    success: bool
    test_status: str


# ============================================================================
# TEST STATUS RESPONSE
# ============================================================================

class TestStatusResponse(BaseModel):
    """Response schema for test status."""
    script_id: str
    script_name: str
    test_status: Optional[str] = None
    test_coverage: Optional[float] = None
    test_results: Optional[Dict[str, Any]] = None
    is_dangerous: bool = False


# ============================================================================
# UNTESTED SCRIPTS RESPONSE
# ============================================================================

class UntestedScriptItem(BaseModel):
    """Schema for untested script item."""
    id: str
    name: str
    category: Optional[str] = None
    approval_status: Optional[str] = None
    is_dangerous: bool = False
    created_at: Optional[str] = None


class UntestedScriptsResponse(BaseModel):
    """Response schema for untested scripts list."""
    workspace_id: str
    scripts: List[UntestedScriptItem]
    count: int


# ============================================================================
# FAILED SCRIPTS RESPONSE
# ============================================================================

class FailedScriptItem(BaseModel):
    """Schema for failed script item."""
    id: str
    name: str
    category: Optional[str] = None
    test_results: Optional[Dict[str, Any]] = None
    is_dangerous: bool = False
    created_at: Optional[str] = None


class FailedScriptsResponse(BaseModel):
    """Response schema for failed scripts list."""
    workspace_id: str
    scripts: List[FailedScriptItem]
    count: int


# ============================================================================
# UPDATE TEST RESULTS REQUEST/RESPONSE
# ============================================================================

class UpdateTestResultsRequest(BaseModel):
    """Request schema for updating test results."""
    test_results: Dict[str, Any] = Field(..., description="Test results")


class UpdateTestResultsResponse(BaseModel):
    """Response schema for updating test results."""
    success: bool


# ============================================================================
# UPDATE TEST COVERAGE REQUEST/RESPONSE
# ============================================================================

class UpdateTestCoverageRequest(BaseModel):
    """Request schema for updating test coverage."""
    test_coverage: float = Field(..., ge=0, le=100, description="Test coverage percentage (0-100)")


class UpdateTestCoverageResponse(BaseModel):
    """Response schema for updating test coverage."""
    success: bool
    test_coverage: float

