from typing import Optional, Any, Dict
from fastapi import Request, status
from fastapi.responses import JSONResponse

from qbitra.core.exceptions import QBitraException
from qbitra.core.exceptions.error_levels import ErrorDetailLevel, get_error_level_from_env
from qbitra.utils.handlers.environment_handler import EnvironmentHandler


def _get_error_level():
    """Lazy evaluation of error level - only called when needed."""
    try:
        app_env = EnvironmentHandler.get_value_as_str("APP_ENV", default="prod")
        return get_error_level_from_env(app_env)
    except Exception:
        # Fallback to production level if environment not initialized
        return {"include_traceback": False, "include_details": False}


ERROR_LEVEL = None

def build_error_response(
    exception: QBitraException,
    level: Optional[ErrorDetailLevel] = None,
) -> JSONResponse:
    """Build error response with environment-based detail level."""
    global ERROR_LEVEL
    if ERROR_LEVEL is None:
        ERROR_LEVEL = _get_error_level()
    
    exception_dict = exception.to_dict(include_traceback=ERROR_LEVEL["include_traceback"], include_details=ERROR_LEVEL["include_details"])
    response_data = {
        'success': False,
        'error': exception_dict
    }
    return JSONResponse(content=response_data, status_code=exception.status_code)

async def qbitra_exception_handler(request: Request, exception: Exception) -> JSONResponse:
    response = build_error_response(exception)
    return response

def register_qbitra_handler(app) -> None:
    app.add_exception_handler(QBitraException, qbitra_exception_handler)