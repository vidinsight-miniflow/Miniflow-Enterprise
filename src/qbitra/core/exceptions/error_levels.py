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
    app_env_lower = app_env.lower() if app_env else "prod"
    
    # Development environments: Show everything
    if "dev" in app_env_lower or "local" in app_env_lower:
        return {"include_traceback": True, "include_details": True}
    
    # Staging/Test environments: Show details but no traceback
    elif "stage" in app_env_lower or "test" in app_env_lower:
        return {"include_traceback": False, "include_details": True}
    
    # Production: Minimal information only
    else:
        return {"include_traceback": False, "include_details": False}
