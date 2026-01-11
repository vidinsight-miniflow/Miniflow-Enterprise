"""
Error Detail Levels
===================

Environment-based error detail level configuration for API responses.
"""

from enum import Enum


class ErrorDetailLevel(str, Enum):
    """
    Error detail levels based on environment.
    
    Controls what information is exposed in error responses:
    - MINIMAL: Production - Only error_code & sanitized message
    - STANDARD: Stage/Test - Include details but no traceback
    - FULL: Development - Full details + traceback
    """
    MINIMAL = "minimal"      # Production: Only error_code & message
    STANDARD = "standard"    # Stage/Test: Include details but no traceback  
    FULL = "full"           # Development: Full details + traceback


def get_error_level_from_env(app_env: str) -> ErrorDetailLevel:
    """
    Get error detail level based on APP_ENV.
    
    Args:
        app_env: Application environment (dev, prod, stage, test, local)
        
    Returns:
        ErrorDetailLevel: Appropriate detail level for the environment
        
    Examples:
        >>> get_error_level_from_env("dev")
        ErrorDetailLevel.FULL
        >>> get_error_level_from_env("production")
        ErrorDetailLevel.MINIMAL
        >>> get_error_level_from_env("staging")
        ErrorDetailLevel.STANDARD
    """
    app_env_lower = app_env.lower() if app_env else "prod"
    
    # Development environments: Show everything
    if "dev" in app_env_lower or "local" in app_env_lower:
        return ErrorDetailLevel.FULL
    
    # Staging/Test environments: Show details but no traceback
    elif "stage" in app_env_lower or "test" in app_env_lower:
        return ErrorDetailLevel.STANDARD
    
    # Production: Minimal information only
    else:
        return ErrorDetailLevel.MINIMAL
