from typing import TypedDict, Dict, Any, Optional
import ipaddress
from fastapi import Depends, HTTPException, Request, Header, status

from miniflow.services import ApiKeyService
from ..service_providers import get_api_key_service
from .rate_limiters import WorkspaceRateLimiter
from miniflow.core.exceptions import (
    ApiKeyMinuteRateLimitExceededError,
    ApiKeyHourRateLimitExceededError,
    ApiKeyDayRateLimitExceededError,
    BusinessRuleViolationError,
)


class ApiKeyCredentials(TypedDict):
    """API Key authentication result."""
    workspace_id: str
    api_key_id: str
    permissions: Dict[str, Any]


def _extract_client_ip(request: Request) -> str:
    """
    Extract client IP with proxy support.
    
    Priority:
    1. X-Forwarded-For (first IP)
    2. X-Real-IP
    3. request.client.host
    4. "unknown" fallback
    """
    # Try X-Forwarded-For first (load balancer/proxy)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # First IP in the chain is the original client
        ip = forwarded_for.split(",")[0].strip()
        if _is_valid_ip(ip):
            return ip
    
    # Try X-Real-IP (nginx)
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        ip = real_ip.strip()
        if _is_valid_ip(ip):
            return ip
    
    # Fall back to direct connection
    if request.client and request.client.host:
        ip = request.client.host
        if _is_valid_ip(ip):
            return ip
    
    return "unknown"


def _is_valid_ip(ip: str) -> bool:
    """Validate IP address format."""
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


async def authenticate_api_key(
    request: Request,
    api_key: str = Header(..., alias="X-API-KEY", description="API Key for authentication"),
    api_key_service: ApiKeyService = Depends(get_api_key_service),
) -> ApiKeyCredentials:
    """
    Authenticate API key and validate access.
    
    Validates:
    - API key exists and is valid (hash verification)
    - API key is active
    - API key is not expired
    - IP address is allowed (if allowed_ips is set)
    - Workspace is active and not suspended
    - Rate limits are not exceeded
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is required",
            headers={"WWW-Authenticate": "X-API-KEY"}
        )

    # Extract client IP for whitelist validation
    client_ip = _extract_client_ip(request)

    try:
        # Validate API key (includes IP check if allowed_ips is set)
        result = api_key_service.validate_api_key(full_api_key=api_key, client_ip=client_ip)

        if not result or not result.get("valid"):
            error_msg = result.get("error", "Invalid API key") if result else "Invalid API key"
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=error_msg,
                headers={"WWW-Authenticate": "X-API-KEY"}
            )

        workspace_id = result.get("workspace_id")
        api_key_id = result.get("api_key_id")
        permissions = result.get("permissions", {})
        plan_id = result.get("workspace_plan_id")

        if not workspace_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key: workspace not found",
                headers={"WWW-Authenticate": "X-API-KEY"}
            )
            
    except HTTPException:
        raise
    except BusinessRuleViolationError as e:
        # Convert BusinessRuleViolationError to HTTPException
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message,
            headers={"WWW-Authenticate": "X-API-KEY"}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"API key validation failed: {str(e)}",
            headers={"WWW-Authenticate": "X-API-KEY"}
        )
    
    # Apply workspace rate limiting
    if plan_id:
        if not _check_workspace_rate_limit(workspace_id, plan_id):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Workspace rate limit exceeded",
                headers={"Retry-After": "60"},
            )
    
    # Set request state
    request.state.workspace_id = workspace_id
    request.state.api_key_id = api_key_id
    request.state.auth_type = "api_key"
    request.state.permissions = permissions

    return ApiKeyCredentials(
        workspace_id=workspace_id,
        api_key_id=api_key_id,
        permissions=permissions,
    )


def _check_workspace_rate_limit(workspace_id: str, plan_id: str) -> bool:
    """
    Check workspace rate limit based on plan.
    
    Returns True if within limit, False if exceeded.
    """
    try:
        limiter = WorkspaceRateLimiter()
        limiter.check_limit(workspace_id, plan_id)
        return True
    except (
        ApiKeyMinuteRateLimitExceededError,
        ApiKeyHourRateLimitExceededError,
        ApiKeyDayRateLimitExceededError,
    ):
        # Rate limit exceeded
        return False
    except Exception:
        # Redis error or other issue - fail open
        return True