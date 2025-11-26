"""
Credential management routes.

Handles credential creation, retrieval, and deletion for workspaces.
Credentials are automatically encrypted at rest.
"""
from fastapi import APIRouter, Depends, Request, status, Path, Query
from typing import Dict, Any, Optional

from src.miniflow.server.dependencies import get_credential_service
from src.miniflow.services import CredentialService
from src.miniflow.database.models.enums import CredentialType
from src.miniflow.server.helpers import (
    validate_workspace_member,
    authenticate_user,
    AuthUser,
)
from src.miniflow.server.schemas.base_schema import create_success_response
from src.miniflow.server.schemas.routes.resource_schemas.credential_schemas import (
    CreateApiKeyCredentialRequest,
)

router = APIRouter(prefix="/workspaces", tags=["credentials"])


# ============================================================================
# GET ALL CREDENTIALS
# ============================================================================

@router.get(
    "/{workspace_id}/credentials",
    summary="Get all credentials",
    description="Get all credentials for a workspace with pagination and filtering",
    status_code=status.HTTP_200_OK,
)
async def get_all_credentials(
    request: Request,
    workspace_id: str = Depends(validate_workspace_member),
    credential_type: Optional[CredentialType] = Query(None, description="Filter by credential type"),
    page: int = Query(1, ge=1, description="Page number (starts from 1)"),
    page_size: int = Query(100, ge=1, le=1000, description="Number of items per page (1-1000)"),
    order_by: Optional[str] = Query(None, description="Field to order by (default: created_at)"),
    order_desc: bool = Query(True, description="Order descending (default: True)"),
    include_deleted: bool = Query(False, description="Include deleted credentials"),
    credential_service: CredentialService = Depends(get_credential_service),
) -> Dict[str, Any]:
    """
    Get all credentials for a workspace with pagination and filtering.
    
    - **workspace_id**: Workspace ID (path parameter)
    - **credential_type**: Filter by credential type (query parameter, optional)
        - Supported types: API_KEY, OAUTH2, BASIC_AUTH, JWT, AWS_CREDENTIALS, GCP_SERVICE_ACCOUNT, SSH_KEY, BEARER_TOKEN, CUSTOM
    - **page**: Page number (query parameter, default: 1, min: 1)
    - **page_size**: Number of items per page (query parameter, default: 100, min: 1, max: 1000)
    - **order_by**: Field to order by (query parameter, optional, default: created_at)
    - **order_desc**: Order descending (query parameter, default: True)
    - **include_deleted**: Include deleted credentials (query parameter, default: False)
    
    Requires workspace membership.
    Returns paginated list of credentials. Credential data is automatically decrypted.
    """
    result = credential_service.get_all_credentials_with_pagination(
        workspace_id=workspace_id,
        credential_type=credential_type,
        page=page,
        page_size=page_size,
        order_by=order_by,
        order_desc=order_desc,
        include_deleted=include_deleted,
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="Credentials retrieved successfully",
        code=status.HTTP_200_OK,
    ).model_dump()


# ============================================================================
# GET CREDENTIAL
# ============================================================================

@router.get(
    "/{workspace_id}/credentials/{credential_id}",
    summary="Get credential",
    description="Get detailed information about a specific credential",
    status_code=status.HTTP_200_OK,
)
async def get_credential(
    request: Request,
    workspace_id: str = Depends(validate_workspace_member),
    credential_id: str = Path(..., description="Credential ID"),
    credential_service: CredentialService = Depends(get_credential_service),
) -> Dict[str, Any]:
    """
    Get detailed information about a specific credential.
    
    - **workspace_id**: Workspace ID (path parameter)
    - **credential_id**: Credential ID (path parameter)
    
    Requires workspace membership.
    Returns credential information. Credential data is automatically decrypted.
    """
    result = credential_service.get_credential(
        credential_id=credential_id,
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="Credential retrieved successfully",
        code=status.HTTP_200_OK,
    ).model_dump()


# ============================================================================
# CREATE API KEY CREDENTIAL
# ============================================================================

@router.post(
    "/{workspace_id}/credentials",
    summary="Create API key credential",
    description="Create a new API key credential for a workspace",
    status_code=status.HTTP_201_CREATED,
)
async def create_api_key_credential(
    request: Request,
    workspace_id: str = Depends(validate_workspace_member),
    body: CreateApiKeyCredentialRequest = ...,
    current_user: AuthUser = Depends(authenticate_user),
    credential_service: CredentialService = Depends(get_credential_service),
) -> Dict[str, Any]:
    """
    Create a new API key credential for a workspace.
    
    - **workspace_id**: Workspace ID (path parameter)
    - **name**: Credential name (request body, required, must be unique in workspace)
    - **api_key**: API key value (request body, required)
    - **credential_provider**: Credential provider (request body, required)
        - Supported providers: GOOGLE, MICROSOFT, GITHUB
    - **description**: Optional description (request body, optional)
    - **tags**: Optional tags (request body, optional)
    - **expires_at**: Optional expiration date (request body, optional)
    - **is_active**: Whether the credential is active (request body, optional, default: True)
    
    Requires workspace membership.
    The authenticated user will be recorded as the owner.
    API key is automatically encrypted.
    """
    result = credential_service.create_api_key_credential(
        workspace_id=workspace_id,
        owner_id=current_user["user_id"],
        name=body.name,
        api_key=body.api_key,
        credential_provider=body.credential_provider.value,
        description=body.description,
        tags=body.tags,
        expires_at=body.expires_at,
        is_active=body.is_active,
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="Credential created successfully",
        code=status.HTTP_201_CREATED,
    ).model_dump()


# ============================================================================
# DELETE CREDENTIAL
# ============================================================================

@router.delete(
    "/{workspace_id}/credentials/{credential_id}",
    summary="Delete credential",
    description="Delete a credential",
    status_code=status.HTTP_200_OK,
)
async def delete_credential(
    request: Request,
    workspace_id: str = Depends(validate_workspace_member),
    credential_id: str = Path(..., description="Credential ID"),
    credential_service: CredentialService = Depends(get_credential_service),
) -> Dict[str, Any]:
    """
    Delete a credential.
    
    - **workspace_id**: Workspace ID (path parameter)
    - **credential_id**: Credential ID (path parameter)
    
    Requires workspace membership.
    Permanently deletes the credential.
    """
    result = credential_service.delete_credential(
        credential_id=credential_id,
    )
    
    return create_success_response(
        request=request,
        data=result,
        message="Credential deleted successfully",
        code=status.HTTP_200_OK,
    ).model_dump()

