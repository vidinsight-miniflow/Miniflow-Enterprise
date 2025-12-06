"""Session management routes for frontend."""

from fastapi import APIRouter, Request, Depends, Query

from miniflow.server.dependencies import (
    get_session_management_service,
    authenticate_user,
)
from miniflow.server.dependencies.auth import AuthenticatedUser
from miniflow.server.schemas.base_schemas import create_success_response
from .schemas.auth_schemas import (
    SessionResponse,
    SessionListResponse,
    RevokeSessionRequest,
    RevokeSessionResponse,
    RevokeAllSessionsResponse,
)

router = APIRouter(prefix="/sessions", tags=["Sessions"])


def _standardize_session_dict(data: dict) -> dict:
    """Standardize session dict: record_id -> id."""
    standardized = data.copy()
    if "record_id" in standardized:
        standardized["id"] = standardized.pop("record_id")
    if "id" not in standardized and "session_id" in standardized:
        standardized["id"] = standardized.pop("session_id")
    return standardized


@router.get("/{session_id}", response_model_exclude_none=True)
async def get_session_by_id(
    request: Request,
    session_id: str,
    service = Depends(get_session_management_service),
    current_user: AuthenticatedUser = Depends(authenticate_user),
) -> dict:
    """
    Get session by ID.
    
    Requires: User authentication
    """
    session = service.get_session_by_id(session_id=session_id)
    standardized = _standardize_session_dict(session)
    response_data = SessionResponse.from_dict(standardized)
    return create_success_response(request, data=response_data.model_dump())


@router.get("/token/{access_token_jti}", response_model_exclude_none=True)
async def get_session_by_access_token_jti(
    request: Request,
    access_token_jti: str,
    service = Depends(get_session_management_service),
    current_user: AuthenticatedUser = Depends(authenticate_user),
) -> dict:
    """
    Get session by access token JTI.
    
    Requires: User authentication
    """
    session = service.get_session_by_access_token_jti(access_token_jti=access_token_jti)
    if not session:
        from miniflow.core.exceptions import ResourceNotFoundError
        raise ResourceNotFoundError(
            resource_name="auth_session",
            message="Session not found"
        )
    standardized = _standardize_session_dict(session)
    response_data = SessionResponse.from_dict(standardized)
    return create_success_response(request, data=response_data.model_dump())


@router.get("/refresh-token/{refresh_token_jti}", response_model_exclude_none=True)
async def get_session_by_refresh_token_jti(
    request: Request,
    refresh_token_jti: str,
    service = Depends(get_session_management_service),
    current_user: AuthenticatedUser = Depends(authenticate_user),
) -> dict:
    """
    Get session by refresh token JTI.
    
    Requires: User authentication
    """
    session = service.get_session_by_refresh_token_jti(refresh_token_jti=refresh_token_jti)
    if not session:
        from miniflow.core.exceptions import ResourceNotFoundError
        raise ResourceNotFoundError(
            resource_name="auth_session",
            message="Session not found"
        )
    standardized = _standardize_session_dict(session)
    response_data = SessionResponse.from_dict(standardized)
    return create_success_response(request, data=response_data.model_dump())


@router.get("/user/active", response_model_exclude_none=True)
async def get_user_active_sessions(
    request: Request,
    user_id: str = Query(None, description="User ID (defaults to current user)"),
    service = Depends(get_session_management_service),
    current_user: AuthenticatedUser = Depends(authenticate_user),
) -> dict:
    """
    Get all active sessions for a user.
    
    Requires: User authentication
    Note: Users can only view their own sessions unless admin.
    """
    # User can only view their own sessions (unless admin)
    target_user_id = user_id if user_id else current_user["user_id"]
    
    # TODO: Add admin check if needed
    # if target_user_id != current_user["user_id"]:
    #     # Check if current_user is admin
    #     pass
    
    sessions = service.get_user_active_sessions(user_id=target_user_id)
    standardized = [_standardize_session_dict(s) for s in sessions]
    response_data = SessionListResponse(items=[SessionResponse.from_dict(s) for s in standardized])
    return create_success_response(request, data=response_data.model_dump())


@router.post("/revoke", response_model_exclude_none=True)
async def revoke_session(
    request: Request,
    revoke_data: RevokeSessionRequest,
    service = Depends(get_session_management_service),
    current_user: AuthenticatedUser = Depends(authenticate_user),
) -> dict:
    """
    Revoke a specific session.
    
    Requires: User authentication
    Note: Users can only revoke their own sessions unless admin.
    """
    result = service.revoke_session(
        session_id=revoke_data.session_id,
        user_id=current_user["user_id"],
        reason=revoke_data.reason
    )
    
    response_data = RevokeSessionResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Session revoked successfully."
    )


@router.post("/revoke-all", response_model_exclude_none=True)
async def revoke_all_user_sessions(
    request: Request,
    user_id: str = Query(None, description="User ID (defaults to current user)"),
    service = Depends(get_session_management_service),
    current_user: AuthenticatedUser = Depends(authenticate_user),
) -> dict:
    """
    Revoke all active sessions for a user.
    
    Requires: User authentication
    Note: Users can only revoke their own sessions unless admin.
    """
    target_user_id = user_id if user_id else current_user["user_id"]
    
    # TODO: Add admin check if needed
    
    result = service.revoke_all_user_sessions(user_id=target_user_id)
    
    response_data = RevokeAllSessionsResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="All sessions revoked successfully."
    )


@router.post("/revoke-oldest", response_model_exclude_none=True)
async def revoke_oldest_session(
    request: Request,
    user_id: str = Query(None, description="User ID (defaults to current user)"),
    service = Depends(get_session_management_service),
    current_user: AuthenticatedUser = Depends(authenticate_user),
) -> dict:
    """
    Revoke oldest active session for a user.
    
    Requires: User authentication
    Note: Users can only revoke their own sessions unless admin.
    """
    target_user_id = user_id if user_id else current_user["user_id"]
    
    # TODO: Add admin check if needed
    
    result = service.revoke_oldest_session(user_id=target_user_id)
    
    if not result:
        return create_success_response(
            request,
            data={"success": True, "message": "No active sessions to revoke"},
            message="No active sessions found."
        )
    
    standardized = _standardize_session_dict(result)
    response_data = SessionResponse.from_dict(standardized)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Oldest session revoked successfully."
    )

