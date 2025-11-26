"""
Workspace Plans route schemas.

Request and Response models for workspace plans endpoints.
"""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


# ============================================================================
# GET API LIMITS
# ============================================================================

# Response is dict from service, no specific schema needed
# Returns: {plan_id: {"limits": {"minute": int, "hour": int, "day": int}}}

