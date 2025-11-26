from typing import Any, List, Optional, TypeVar, Generic
from pydantic import BaseModel, Field, model_serializer
from datetime import datetime, timezone
from fastapi import Request, status


T = TypeVar("T")


class BaseResponse(BaseModel, Generic[T]):
    status: str = Field(..., description="success veya error")
    code: int = Field(..., description="HTTP status code (200, 400, 500 vb.)")
    message: Optional[str] = Field(None, description="Başarılı response için mesaj")
    traceId: str = Field(..., description="Request ID (debugging ve tracing için)")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'), description="Response oluşturulma zamanı")

class SuccessResponse(BaseResponse):
    data: Optional[T] = Field(None, description="Başarılı response'da gerçek data")

class FailuresResponse(BaseResponse):
    error_message: Optional[str] = Field(None, description="Hatalı response için mesaj")
    error_code: Optional[str] = Field(None, description="Hata kodu (RESOURCE_NOT_FOUND, VALIDATION_ERROR, vb.)")

def get_trace_id(request: Request) -> str:
    return getattr(request.state, 'request_id', 'unknown')



def create_success_response(request: Request, data: Any, message: Optional[str] = None, code: int = status.HTTP_200_OK) -> SuccessResponse[Any]:
    return SuccessResponse(status="success", code=code, message=message, traceId=get_trace_id(request), data=data)

def create_error_response(request: Request, error_message: str, error_code: str, code: int = status.HTTP_400_BAD_REQUEST) -> FailuresResponse[Any]:
    return FailuresResponse(status="error", code=code, message=None, traceId=get_trace_id(request), error_message=error_message, error_code=error_code)