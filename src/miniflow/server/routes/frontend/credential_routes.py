"""Credential routes for frontend."""

from fastapi import APIRouter, Request, Depends, Path, Query
from datetime import datetime

from miniflow.server.dependencies import (
    get_credential_service,
    authenticate_user,
    require_workspace_access,
)
from miniflow.server.dependencies.auth import AuthenticatedUser
from miniflow.server.schemas.base_schemas import create_success_response
from miniflow.models.enums import CredentialType
from .schemas.credential_schemas import (
    CreateApiKeyCredentialRequest,
    CreateSlackCredentialRequest,
    CreateCredentialResponse,
    CredentialResponse,
    WorkspaceCredentialsResponse,
    UpdateCredentialRequest,
    ActivateCredentialResponse,
    DeactivateCredentialResponse,
    DeleteCredentialResponse,
)

router = APIRouter(prefix="/workspaces", tags=["Credentials"])


# ============================================================================
# CREATE CREDENTIAL ENDPOINTS
# ============================================================================

@router.post("/{workspace_id}/credentials/api-key", response_model_exclude_none=True)
async def create_api_key_credential(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    credential_data: CreateApiKeyCredentialRequest = ...,
    service = Depends(get_credential_service),
    current_user: AuthenticatedUser = Depends(authenticate_user),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Create API key credential.
    
    Requires: Workspace access
    Note: Credential data is encrypted automatically.
    """
    expires_at = None
    if credential_data.expires_at:
        expires_at = datetime.fromisoformat(credential_data.expires_at.replace('Z', '+00:00'))
    
    result = service.create_api_key_credential(
        workspace_id=workspace_id,
        owner_id=current_user["user_id"],
        name=credential_data.name,
        api_key=credential_data.api_key,
        provider=credential_data.provider,
        description=credential_data.description,
        tags=credential_data.tags,
        expires_at=expires_at
    )
    
    response_data = CreateCredentialResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="API key credential created successfully."
    )


@router.post("/{workspace_id}/credentials/slack", response_model_exclude_none=True)
async def create_slack_credential(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    credential_data: CreateSlackCredentialRequest = ...,
    service = Depends(get_credential_service),
    current_user: AuthenticatedUser = Depends(authenticate_user),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Create Slack credential.
    
    Requires: Workspace access
    Note: Credential data is encrypted automatically.
    """
    expires_at = None
    if credential_data.expires_at:
        expires_at = datetime.fromisoformat(credential_data.expires_at.replace('Z', '+00:00'))
    
    result = service.create_slack_credential(
        workspace_id=workspace_id,
        owner_id=current_user["user_id"],
        name=credential_data.name,
        bot_token=credential_data.bot_token,
        signing_secret=credential_data.signing_secret,
        app_token=credential_data.app_token,
        description=credential_data.description,
        tags=credential_data.tags,
        expires_at=expires_at
    )
    
    response_data = CreateCredentialResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Slack credential created successfully."
    )


# ============================================================================
# GET CREDENTIAL ENDPOINTS
# ============================================================================

@router.get("/{workspace_id}/credentials/{credential_id}", response_model_exclude_none=True)
async def get_credential(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    credential_id: str = Path(..., description="Credential ID"),
    include_secret: bool = Query(default=False, description="Include secret data (for workflow execution)"),
    service = Depends(get_credential_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Get credential details.
    
    Requires: Workspace access
    Note: Secret data is excluded by default. Set include_secret=True for workflow execution.
    """
    result = service.get_credential(
        credential_id=credential_id,
        include_secret=include_secret
    )
    
    response_data = CredentialResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump()
    )


@router.get("/{workspace_id}/credentials", response_model_exclude_none=True)
async def get_workspace_credentials(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    credential_type: str = Query(None, description="Filter by credential type (API_KEY, etc.)"),
    service = Depends(get_credential_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Get all workspace credentials.
    
    Requires: Workspace access
    """
    cred_type = None
    if credential_type:
        try:
            cred_type = CredentialType(credential_type.upper())
        except ValueError:
            pass
    
    result = service.get_workspace_credentials(
        workspace_id=workspace_id,
        credential_type=cred_type
    )
    
    response_data = WorkspaceCredentialsResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump()
    )


# ============================================================================
# UPDATE CREDENTIAL ENDPOINTS
# ============================================================================

@router.put("/{workspace_id}/credentials/{credential_id}", response_model_exclude_none=True)
async def update_credential(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    credential_id: str = Path(..., description="Credential ID"),
    credential_data: UpdateCredentialRequest = ...,
    service = Depends(get_credential_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Update credential metadata.
    
    Requires: Workspace access
    Note: Credential data cannot be changed. Create a new credential instead.
    """
    result = service.update_credential(
        credential_id=credential_id,
        name=credential_data.name,
        description=credential_data.description,
        tags=credential_data.tags
    )
    
    response_data = CredentialResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Credential updated successfully."
    )


# ============================================================================
# ACTIVATE/DEACTIVATE CREDENTIAL ENDPOINTS
# ============================================================================

@router.post("/{workspace_id}/credentials/{credential_id}/activate", response_model_exclude_none=True)
async def activate_credential(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    credential_id: str = Path(..., description="Credential ID"),
    service = Depends(get_credential_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Activate credential.
    
    Requires: Workspace access
    """
    result = service.activate_credential(
        credential_id=credential_id
    )
    
    response_data = ActivateCredentialResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Credential activated successfully."
    )


@router.post("/{workspace_id}/credentials/{credential_id}/deactivate", response_model_exclude_none=True)
async def deactivate_credential(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    credential_id: str = Path(..., description="Credential ID"),
    service = Depends(get_credential_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Deactivate credential.
    
    Requires: Workspace access
    """
    result = service.deactivate_credential(
        credential_id=credential_id
    )
    
    response_data = DeactivateCredentialResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Credential deactivated successfully."
    )


# ============================================================================
# DELETE CREDENTIAL ENDPOINTS
# ============================================================================

@router.delete("/{workspace_id}/credentials/{credential_id}", response_model_exclude_none=True)
async def delete_credential(
    request: Request,
    workspace_id: str = Path(..., description="Workspace ID"),
    credential_id: str = Path(..., description="Credential ID"),
    service = Depends(get_credential_service),
    _: str = Depends(require_workspace_access),
) -> dict:
    """
    Delete credential.
    
    Requires: Workspace access
    """
    result = service.delete_credential(
        credential_id=credential_id
    )
    
    response_data = DeleteCredentialResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Credential deleted successfully."
    )

