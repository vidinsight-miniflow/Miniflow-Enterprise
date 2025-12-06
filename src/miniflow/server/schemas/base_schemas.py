from typing import Any, List, Optional, TypeVar, Generic
from pydantic import BaseModel, Field, model_serializer
from datetime import datetime, timezone
from fastapi import Request, status


T = TypeVar("T")


class BaseResponse(BaseModel, Generic[T]):
    """Base response model for all API responses."""
    status: str = Field(..., description="success or error")
    code: int = Field(..., description="HTTP status code (200, 400, 500, etc.)")
    message: Optional[str] = Field(None, description="Success message")
    traceId: str = Field(..., description="Request ID (for debugging and tracing)")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        description="Response creation timestamp"
    )

class SuccessResponse(BaseResponse[T]):
    """Success response model."""
    data: Optional[T] = Field(None, description="Response data")

class FailuresResponse(BaseResponse):
    """Error response model."""
    error_message: Optional[str] = Field(None, description="Error message")
    error_code: Optional[str] = Field(None, description="Error code (RESOURCE_NOT_FOUND, VALIDATION_ERROR, etc.)")

def get_trace_id(request: Request) -> str:
    """Extract trace ID from request state."""
    return getattr(request.state, 'request_id', 'unknown')


def create_success_response(
    request: Request,
    data: Any,
    message: Optional[str] = None,
    code: int = status.HTTP_200_OK
) -> dict:
    """Create a success response and return as dict."""
    response = SuccessResponse(
        status="success",
        code=code,
        message=message,
        traceId=get_trace_id(request),
        data=data
    )
    return response.model_dump()


def create_error_response(
    request: Request,
    error_message: str,
    error_code: str,
    code: int = status.HTTP_400_BAD_REQUEST
) -> dict:
    """Create an error response and return as dict."""
    response = FailuresResponse(
        status="error",
        code=code,
        message=None,
        traceId=get_trace_id(request),
        error_message=error_message,
        error_code=error_code
    )
    return response.model_dump()