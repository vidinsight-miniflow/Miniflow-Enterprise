"""Script testing routes for frontend."""

from fastapi import APIRouter, Request, Depends, Path

from miniflow.server.dependencies import (
    get_script_testing_service,
    authenticate_user,
    authenticate_admin,
    require_workspace_access,
)
from miniflow.server.dependencies.auth import AuthenticatedUser
from miniflow.server.schemas.base_schemas import create_success_response
from .schemas.script_testing_schemas import (
    MarkTestPassedRequest,
    MarkTestPassedResponse,
    MarkTestFailedRequest,
    MarkTestFailedResponse,
    MarkTestSkippedRequest,
    MarkTestSkippedResponse,
    ResetTestStatusResponse,
    TestStatusResponse,
    UntestedScriptsResponse,
    FailedScriptsResponse,
    UpdateTestResultsRequest,
    UpdateTestResultsResponse,
    UpdateTestCoverageRequest,
    UpdateTestCoverageResponse,
)

router = APIRouter(prefix="/workspaces", tags=["Script Testing"])


# ============================================================================
# MARK TEST STATUS ENDPOINTS
# ============================================================================

@router.post("/{workspace_id}/scripts/{script_id}/test/passed", response_model_exclude_none=True)
async def mark_test_passed(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    script_id: str = Path(..., description="Script ID"),
    test_data: MarkTestPassedRequest = ...,
    service = Depends(get_script_testing_service),
    current_user: AuthenticatedUser = Depends(authenticate_admin),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Mark script test as passed.
    
    Requires: Admin authentication + Workspace access
    Note: Usually called by test executor/worker.
    """
    result = service.mark_test_passed(
        script_id=script_id,
        test_results=test_data.test_results,
        test_coverage=test_data.test_coverage
    )
    
    response_data = MarkTestPassedResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Test marked as passed."
    )


@router.post("/{workspace_id}/scripts/{script_id}/test/failed", response_model_exclude_none=True)
async def mark_test_failed(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    script_id: str = Path(..., description="Script ID"),
    test_data: MarkTestFailedRequest = ...,
    service = Depends(get_script_testing_service),
    current_user: AuthenticatedUser = Depends(authenticate_admin),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Mark script test as failed.
    
    Requires: Admin authentication + Workspace access
    Note: Test results with error details are required.
    """
    result = service.mark_test_failed(
        script_id=script_id,
        test_results=test_data.test_results,
        test_coverage=test_data.test_coverage
    )
    
    response_data = MarkTestFailedResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Test marked as failed."
    )


@router.post("/{workspace_id}/scripts/{script_id}/test/skipped", response_model_exclude_none=True)
async def mark_test_skipped(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    script_id: str = Path(..., description="Script ID"),
    test_data: MarkTestSkippedRequest = ...,
    service = Depends(get_script_testing_service),
    current_user: AuthenticatedUser = Depends(authenticate_admin),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Mark script test as skipped.
    
    Requires: Admin authentication + Workspace access
    """
    result = service.mark_test_skipped(
        script_id=script_id,
        reason=test_data.reason
    )
    
    response_data = MarkTestSkippedResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Test marked as skipped."
    )


@router.post("/{workspace_id}/scripts/{script_id}/test/reset", response_model_exclude_none=True)
async def reset_test_status(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    script_id: str = Path(..., description="Script ID"),
    service = Depends(get_script_testing_service),
    current_user: AuthenticatedUser = Depends(authenticate_admin),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Reset test status to UNTESTED.
    
    Requires: Admin authentication + Workspace access
    """
    result = service.reset_test_status(
        script_id=script_id
    )
    
    response_data = ResetTestStatusResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Test status reset to UNTESTED."
    )


# ============================================================================
# GET TEST INFO ENDPOINTS
# ============================================================================

@router.get("/{workspace_id}/scripts/{script_id}/test/status", response_model_exclude_none=True)
async def get_test_status(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    script_id: str = Path(..., description="Script ID"),
    service = Depends(get_script_testing_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Get script test status.
    
    Requires: Workspace access
    """
    result = service.get_test_status(
        script_id=script_id
    )
    
    response_data = TestStatusResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump()
    )


@router.get("/{workspace_id}/scripts/untested", response_model_exclude_none=True)
async def get_untested_scripts(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    service = Depends(get_script_testing_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Get untested scripts.
    
    Requires: Workspace access
    """
    result = service.get_untested_scripts(
        workspace_id=workspace_id
    )
    
    response_data = UntestedScriptsResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump()
    )


@router.get("/{workspace_id}/scripts/failed", response_model_exclude_none=True)
async def get_failed_scripts(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    service = Depends(get_script_testing_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Get failed scripts.
    
    Requires: Workspace access
    """
    result = service.get_failed_scripts(
        workspace_id=workspace_id
    )
    
    response_data = FailedScriptsResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump()
    )


# ============================================================================
# UPDATE TEST RESULTS ENDPOINTS
# ============================================================================

@router.put("/{workspace_id}/scripts/{script_id}/test/results", response_model_exclude_none=True)
async def update_test_results(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    script_id: str = Path(..., description="Script ID"),
    test_data: UpdateTestResultsRequest = ...,
    service = Depends(get_script_testing_service),
    current_user: AuthenticatedUser = Depends(authenticate_admin),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Update test results (without changing status).
    
    Requires: Admin authentication + Workspace access
    """
    result = service.update_test_results(
        script_id=script_id,
        test_results=test_data.test_results
    )
    
    response_data = UpdateTestResultsResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Test results updated successfully."
    )


@router.put("/{workspace_id}/scripts/{script_id}/test/coverage", response_model_exclude_none=True)
async def update_test_coverage(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    script_id: str = Path(..., description="Script ID"),
    test_data: UpdateTestCoverageRequest = ...,
    service = Depends(get_script_testing_service),
    current_user: AuthenticatedUser = Depends(authenticate_admin),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Update test coverage.
    
    Requires: Admin authentication + Workspace access
    Note: Coverage must be between 0 and 100.
    """
    result = service.update_test_coverage(
        script_id=script_id,
        test_coverage=test_data.test_coverage
    )
    
    response_data = UpdateTestCoverageResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Test coverage updated successfully."
    )

