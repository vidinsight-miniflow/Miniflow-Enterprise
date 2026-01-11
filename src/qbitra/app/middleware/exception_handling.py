from typing import Optional, Any, Dict
from fastapi import Request, status
from fastapi.responses import JSONResponse

from qbitra.core.exceptions import QBitraException
from qbitra.core.exceptions.error_levels import ErrorDetailLevel, get_error_level_from_env
from qbitra.utils.handlers.environment_handler import EnvironmentHandler


APP_ENV = EnvironmentHandler.get_value_as_str("APP_ENV", default="prod")
ERROR_LEVEL = get_error_level_from_env(APP_ENV)


def build_error_response(
    exception: QBitraException,
    level: ErrorDetailLevel = ERROR_LEVEL,
) -> JSONResponse:
    
    exception_dict = exception.to_dict(include_traceback=level["include_traceback"], include_details=level["include_details"])
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