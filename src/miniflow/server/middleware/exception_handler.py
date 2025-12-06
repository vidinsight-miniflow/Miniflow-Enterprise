import os
from typing import Optional, Any
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from miniflow.core.exceptions import AppException, ErrorCode
from ..schemas import (
    create_error_response,
    get_trace_id,
)

from miniflow.utils import EnvironmentHandler


# ---------------------------------------------------------
# Environment Control
# ---------------------------------------------------------
is_production = EnvironmentHandler.get("APP_ENV", "dev").lower() == "prod"


# ---------------------------------------------------------
# ErrorCode → HTTP mapping
# ---------------------------------------------------------
ERROR_CODE_TO_HTTP_STATUS = {
    # Validation Errors
    ErrorCode.VALIDATION_ERROR: status.HTTP_422_UNPROCESSABLE_ENTITY,  # Note: HTTP_422_UNPROCESSABLE_CONTENT not yet available in FastAPI
    ErrorCode.INVALID_INPUT: status.HTTP_400_BAD_REQUEST,
    ErrorCode.RESOURCE_NOT_FOUND: status.HTTP_404_NOT_FOUND,
    ErrorCode.RESOURCE_ALREADY_EXISTS: status.HTTP_409_CONFLICT,
    ErrorCode.BUSINESS_RULE_VIOLATION: status.HTTP_400_BAD_REQUEST,
    ErrorCode.DATABASE_VALIDATION_ERROR: status.HTTP_400_BAD_REQUEST,

    # Authentication
    ErrorCode.AUTHENTICATION_FAILED: status.HTTP_401_UNAUTHORIZED,
    ErrorCode.INVALID_CREDENTIALS: status.HTTP_401_UNAUTHORIZED,
    ErrorCode.TOKEN_EXPIRED: status.HTTP_401_UNAUTHORIZED,
    ErrorCode.TOKEN_INVALID: status.HTTP_401_UNAUTHORIZED,
    ErrorCode.UNAUTHORIZED: status.HTTP_401_UNAUTHORIZED,
    ErrorCode.FORBIDDEN: status.HTTP_403_FORBIDDEN,
    ErrorCode.INSUFFICIENT_PERMISSIONS: status.HTTP_403_FORBIDDEN,
    ErrorCode.INVALID_API_KEY: status.HTTP_401_UNAUTHORIZED,

    # Rate Limit
    ErrorCode.IP_RATE_LIMIT_EXCEEDED: status.HTTP_429_TOO_MANY_REQUESTS,
    ErrorCode.USER_RATE_LIMIT_EXCEEDED: status.HTTP_429_TOO_MANY_REQUESTS,
    ErrorCode.API_KEY_MINUTE_RATE_LIMIT_EXCEEDED: status.HTTP_429_TOO_MANY_REQUESTS,
    ErrorCode.API_KEY_HOUR_RATE_LIMIT_EXCEEDED: status.HTTP_429_TOO_MANY_REQUESTS,
    ErrorCode.API_KEY_DAY_RATE_LIMIT_EXCEEDED: status.HTTP_429_TOO_MANY_REQUESTS,

    # Database
    ErrorCode.DATABASE_CONNECTION_ERROR: status.HTTP_503_SERVICE_UNAVAILABLE,
    ErrorCode.DATABASE_QUERY_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
    ErrorCode.DATABASE_TRANSACTION_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
    ErrorCode.DATABASE_SESSION_ERROR: status.HTTP_503_SERVICE_UNAVAILABLE,
    ErrorCode.DATABASE_ENGINE_ERROR: status.HTTP_503_SERVICE_UNAVAILABLE,
    ErrorCode.DATABASE_CONFIGURATION_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,

    # External
    ErrorCode.EXTERNAL_SERVICE_TIMEOUT: status.HTTP_504_GATEWAY_TIMEOUT,
    ErrorCode.EXTERNAL_SERVICE_UNAVAILABLE: status.HTTP_503_SERVICE_UNAVAILABLE,
    ErrorCode.EXTERNAL_SERVICE_CONNECTION_ERROR: status.HTTP_503_SERVICE_UNAVAILABLE,
    ErrorCode.EXTERNAL_SERVICE_REQUEST_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
    ErrorCode.EXTERNAL_SERVICE_RESPONSE_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
    ErrorCode.EXTERNAL_SERVICE_VALIDATION_ERROR: status.HTTP_400_BAD_REQUEST,
    ErrorCode.EXTERNAL_SERVICE_AUTHORIZATION_ERROR: status.HTTP_403_FORBIDDEN,
    ErrorCode.EXTERNAL_SERVICE_RATE_LIMIT_ERROR: status.HTTP_429_TOO_MANY_REQUESTS,

    # Internal
    ErrorCode.INTERNAL_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
    ErrorCode.NOT_IMPLEMENTED: status.HTTP_501_NOT_IMPLEMENTED,
    
    # Scheduler
    ErrorCode.SCHEDULER_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
    ErrorCode.CONTEXT_CREATION_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
    ErrorCode.PAYLOAD_PREPARATION_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
    ErrorCode.ENGINE_SUBMISSION_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
    ErrorCode.RESULT_PROCESSING_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
    ErrorCode.HANDLER_CONFIGURATION_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
}


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def get_http_status_code(error_code: ErrorCode) -> int:
    return ERROR_CODE_TO_HTTP_STATUS.get(error_code, status.HTTP_500_INTERNAL_SERVER_ERROR)


def narrative_traceback(exception: Exception) -> str:
    """Human-readable traceback."""
    import traceback
    tb = traceback.extract_tb(exception.__traceback__)

    lines = [
        "ERROR TRACEBACK!",
        "",
        f"- Exception: {exception.__class__.__name__}",
        f"- Message: {str(exception)}",
        "",
        "Call Stack (most recent last):"
    ]

    for frame in tb:
        lines.append(
            f"  → In {frame.filename}, line {frame.lineno}, function {frame.name}\n"
            f"      Code: {frame.line}"
        )

    return "\n".join(lines)


def get_error_detail(exception: AppException) -> Optional[Any]:
    """Extracts error details for AppException."""
    detail = {}

    if exception.error_details:
        detail.update(exception.error_details)

    if not is_production and exception.__cause__:
        detail["original_error"] = {
            "type": type(exception.__cause__).__name__,
            "message": str(exception.__cause__)
        }

    return detail or None


def format_exception_log(request: Request, exception: Exception, error_detail: Optional[Any] = None) -> None:
    """Pretty developer log output."""
    separator = "═" * 50
    divider = "─" * 50

    method = getattr(request, "method", "UNKNOWN")
    path = getattr(request, "url", None).path if hasattr(request, "url") else "UNKNOWN"
    trace_id = get_trace_id(request)

    print(f"\n{separator}")
    print("EXCEPTION OCCURRED")
    print(separator)

    print(f"Request: {method} {path}")
    print(f"Trace ID: {trace_id}")
    print(divider)

    print(f"Exception Type: {type(exception).__name__}")
    print(f"Message: {str(exception)}")

    if hasattr(exception, 'error_code'):
        print(f"Error Code: {exception.error_code.value}")

    # Önce parametre olarak geçilen error_detail'i kontrol et
    if error_detail:
        print(f"Error Details: {error_detail}")
    elif hasattr(exception, 'error_details') and exception.error_details:
        print(f"Error Details: {exception.error_details}")

    print(divider)

    if exception.__cause__:
        print("Original Error:")
        print(f"  Type: {type(exception.__cause__).__name__}")
        print(f"  Message: {str(exception.__cause__)}")

    print(divider)
    print(narrative_traceback(exception))
    print(separator + "\n")


# ---------------------------------------------------------
# Exception Handlers
# ---------------------------------------------------------

async def app_exception_handler(request: Request, exception: AppException) -> JSONResponse:
    """Handles custom AppException."""
    http_status = get_http_status_code(exception.error_code)
    error_detail = get_error_detail(exception)
    
    if not is_production:
        format_exception_log(request, exception, error_detail=error_detail)

    response_data = create_error_response(
        request,
        error_message=exception.error_message,
        error_code=exception.error_code.value,
        code=http_status,
    )

    return JSONResponse(status_code=http_status, content=response_data)


async def validation_exception_handler(request: Request, exception: RequestValidationError) -> JSONResponse:
    """Handles Pydantic/FastAPI validation errors."""
    error_detail = {
        "errors": [
            {
                "field": " -> ".join(str(loc) for loc in error.get("loc", [])),
                "type": error.get("type", "validation_error"),
                "message": error.get("msg")
            }
            for error in exception.errors()
        ]
    }
    
    if not is_production:
        format_exception_log(request, exception, error_detail=error_detail)

    response_data = create_error_response(
        request,
        error_message="Request validation failed",
        error_code="VALIDATION_ERROR",
        code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    )

    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=response_data)


async def http_exception_handler(request: Request, exception: StarletteHTTPException) -> JSONResponse:
    """Handles Starlette HTTP errors."""
    if not is_production:
        format_exception_log(request, exception)

    message = exception.detail if isinstance(exception.detail, str) else str(exception.detail)

    response_data = create_error_response(
        request,
        error_message=message,
        error_code=f"HTTP_{exception.status_code}",
        code=exception.status_code,
    )

    return JSONResponse(status_code=exception.status_code, content=response_data)


async def generic_exception_handler(request: Request, exception: Exception) -> JSONResponse:
    """
    Catches all unexpected exceptions.
    - Development: returns full traceback & details
    - Production: hides sensitive info
    """
    # Development — Show full details
    if not is_production:
        error_message = f"Unexpected error: {str(exception)}"
        error_detail = {
            "type": type(exception).__name__,
            "message": str(exception),
            "traceback": narrative_traceback(exception)
        }
        format_exception_log(request, exception, error_detail=error_detail)
    else:
        # Production — Hide details
        error_message = "An unexpected error occurred. Our team has been notified."
        error_detail = None

    response_data = create_error_response(
        request,
        error_message=error_message,
        error_code="INTERNAL_ERROR",
        code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response_data
    )


def register_exception_handlers(app) -> None:
    """Register all exception handlers to FastAPI app."""
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)


"""
Bu sistem, FastAPI uygulamasında oluşabilecek her türlü hatayı yakalayan, sınıflandıran ve doğru
formatta API response'a çeviren merkezi bir hata yönetim modülüdür. Sistemde 4 ana handler vardır:
- AppException handler: Bizim uygulama için ürettiğimiz özel hataları yakalar
- ValidationError handler (FastAPI / Pydantic): Request body, query, path gibi parametrelerde hata olduğunda çalışır.
- HTTPException handler (Starlette): Yetki hataları, manual raise edilen 404, 403, 405 gibi durumları yakalar.
- Generic Exception handler: Tüm beklenmeyen hataları yakalayan son kalkan.
"""