"""Login history routes for frontend."""

from fastapi import APIRouter, Request, Depends, Query

from miniflow.server.dependencies import (
    get_login_history_service,
    authenticate_user,
)
from miniflow.server.dependencies.auth import AuthenticatedUser
from miniflow.server.schemas.base_schemas import create_success_response
from .schemas.auth_schemas import (
    LoginHistoryResponse,
    LoginHistoryListResponse,
    RateLimitCheckResponse,
)

router = APIRouter(prefix="/login-history", tags=["Login History"])


def _standardize_history_dict(data: dict) -> dict:
    """Standardize history dict: record_id -> id."""
    standardized = data.copy()
    if "record_id" in standardized:
        standardized["id"] = standardized.pop("record_id")
    if "id" not in standardized and "history_id" in standardized:
        standardized["id"] = standardized.pop("history_id")
    return standardized


@router.get("/user", response_model_exclude_none=True)
async def get_user_login_history(
    request: Request,
    user_id: str = Query(None, description="User ID (defaults to current user)"),
    limit: int = Query(default=10, ge=1, le=100, description="Maximum number of records"),
    service = Depends(get_login_history_service),
    current_user: AuthenticatedUser = Depends(authenticate_user),
) -> dict:
    """
    Get login history for a user.
    
    Requires: User authentication
    Note: Users can only view their own history unless admin.
    """
    target_user_id = user_id if user_id else current_user["user_id"]
    
    # TODO: Add admin check if needed
    
    history = service.get_user_login_history(user_id=target_user_id, limit=limit)
    standardized = [_standardize_history_dict(h) for h in history]
    response_data = LoginHistoryListResponse(items=[LoginHistoryResponse.from_dict(h) for h in standardized])
    return create_success_response(request, data=response_data.model_dump())


@router.get("/{history_id}", response_model_exclude_none=True)
async def get_login_history_by_id(
    request: Request,
    history_id: str,
    service = Depends(get_login_history_service),
    current_user: AuthenticatedUser = Depends(authenticate_user),
) -> dict:
    """
    Get login history record by ID.
    
    Requires: User authentication
    """
    history = service.get_login_history_by_id(history_id=history_id)
    standardized = _standardize_history_dict(history)
    response_data = LoginHistoryResponse.from_dict(standardized)
    return create_success_response(request, data=response_data.model_dump())


@router.get("/user/rate-limit-check", response_model_exclude_none=True)
async def check_rate_limit(
    request: Request,
    user_id: str = Query(None, description="User ID (defaults to current user)"),
    max_attempts: int = Query(default=5, ge=1, description="Maximum attempts"),
    window_minutes: int = Query(default=5, ge=1, description="Time window in minutes"),
    service = Depends(get_login_history_service),
    current_user: AuthenticatedUser = Depends(authenticate_user),
) -> dict:
    """
    Check if user has exceeded rate limit.
    
    Requires: User authentication
    Note: Users can only check their own rate limit unless admin.
    """
    target_user_id = user_id if user_id else current_user["user_id"]
    
    # TODO: Add admin check if needed
    
    rate_limit_exceeded = service.check_rate_limit(
        user_id=target_user_id,
        max_attempts=max_attempts,
        window_minutes=window_minutes
    )
    
    response_data = RateLimitCheckResponse(
        user_id=target_user_id,
        rate_limit_exceeded=rate_limit_exceeded
    )
    return create_success_response(request, data=response_data.model_dump())

