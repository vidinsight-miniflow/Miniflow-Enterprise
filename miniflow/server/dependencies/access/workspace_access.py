import re
from fastapi import Depends, HTTPException, Request, Path, status

from miniflow.core.exceptions import AppException
from ..auth import authenticate_user, AuthenticatedUser
from ..service_providers import get_workspace_service, get_workspace_member_service


# Regex pattern for workspace ID validation
WORKSPACE_ID_PATTERN = re.compile(r"^WSP-[A-F0-9]{16}$")

async def extract_workspace_id(
    workspace_id: str = Path(..., alias="workspace_id", description="Workspace ID")
) -> str:
    if not workspace_id or workspace_id in ("undefined", "null", "None"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Workspace ID is required. Please select a workspace.")
    
    # Validate format
    if not WORKSPACE_ID_PATTERN.match(workspace_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid workspace ID format. Expected: WSP-[16 hex chars], got: {workspace_id}",)
    
    return workspace_id


async def require_workspace_access(
    request: Request,
    workspace_id: str = Depends(extract_workspace_id),
    current_user: AuthenticatedUser = Depends(authenticate_user),
    workspace_service = Depends(get_workspace_service),
    member_service = Depends(get_workspace_member_service),
) -> str:
    try:
        # 1. Validate workspace exists and not suspended
        workspace_service.validate_workspace(
            workspace_id=workspace_id,
            check_suspended=True,
        )
        
        # 2. Validate user is a member
        member_service.validate_workspace_member(
            workspace_id=workspace_id, 
            user_id=current_user["user_id"]
        )
        
        # 3. Set request state
        request.state.workspace_id = workspace_id
        
        return workspace_id
        
    except HTTPException:
        raise

    except AppException as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Workspace access check failed: {str(e)}")


async def require_workspace_access_allow_suspended(
    request: Request,
    workspace_id: str = Depends(extract_workspace_id),
    current_user: AuthenticatedUser = Depends(authenticate_user),
    workspace_service = Depends(get_workspace_service),
    member_service = Depends(get_workspace_member_service),
) -> str:
    try:
        # 1. Validate workspace exists (allow suspended)
        workspace_service.validate_workspace(
            workspace_id=workspace_id,
            check_suspended=False,
        )
        
        # 2. Validate user is a member
        member_service.validate_workspace_member(
            workspace_id=workspace_id,
            user_id=current_user["user_id"],
        )
        
        # 3. Set request state
        request.state.workspace_id = workspace_id
        
        return workspace_id
        
    except HTTPException:
        raise

    except AppException as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Workspace access check failed: {str(e)}")


async def require_workspace_owner(
    request: Request,
    workspace_id: str = Depends(extract_workspace_id),
    current_user: AuthenticatedUser = Depends(authenticate_user),
    workspace_service = Depends(get_workspace_service),
) -> str:
    try:
        # Get workspace and check ownership
        workspace = workspace_service.get_workspace(workspace_id=workspace_id)
        
        if workspace.get("owner_id") != current_user["user_id"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the workspace owner can perform this action")
        
        request.state.workspace_id = workspace_id
        return workspace_id
        
    except HTTPException:
        raise

    except AppException as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Workspace owner check failed: {str(e)}")