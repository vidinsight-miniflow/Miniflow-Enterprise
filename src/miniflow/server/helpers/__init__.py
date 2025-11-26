"""
Server helpers module for authentication and authorization dependencies.

This module provides FastAPI dependencies for:
- Authentication: JWT token and API key validation
- Authorization: Workspace access control and member validation
"""

from .authorization import (
    AuthUser,
    ApiKeyUser,
    authenticate_user,
    authenticate_api_key,
)

from .workspace_authorization import (
    extract_workspace_id,
    require_valid_workspace,
    validate_workspace_member,
    validate_workspace_member_allow_suspended,
)

__all__ = [
    # Authentication
    "AuthUser",
    "ApiKeyUser",
    "authenticate_user",
    "authenticate_api_key",
    # Authorization
    "extract_workspace_id",
    "require_valid_workspace",
    "validate_workspace_member",
    "validate_workspace_member_allow_suspended",
]

