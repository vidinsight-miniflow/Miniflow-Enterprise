"""Global script routes for frontend."""

from typing import Optional
from fastapi import APIRouter, Request, Depends, Path, Query

from miniflow.server.dependencies import (
    get_global_script_service,
    authenticate_admin,
)
from miniflow.server.dependencies.auth import AuthenticatedUser
from miniflow.server.schemas.base_schemas import create_success_response
from .schemas.global_script_schemas import (
    CreateGlobalScriptRequest,
    CreateGlobalScriptResponse,
    GlobalScriptResponse,
    GlobalScriptByNameResponse,
    GlobalScriptContentResponse,
    AllGlobalScriptsResponse,
    CategoriesResponse,
    UpdateGlobalScriptRequest,
    DeleteGlobalScriptResponse,
    SeedScriptsRequest,
    SeedScriptsResponse,
)

router = APIRouter(prefix="/admin", tags=["Global Scripts"])


# ============================================================================
# CREATE SCRIPT ENDPOINTS
# ============================================================================

@router.post("/scripts", response_model_exclude_none=True)
async def create_global_script(
    request: Request,
    script_data: CreateGlobalScriptRequest = ...,
    service = Depends(get_global_script_service),
    current_user: AuthenticatedUser = Depends(authenticate_admin),
) -> dict:
    """
    Create a new global script.
    
    Requires: Admin authentication
    Note: Script content cannot be changed after creation. Scripts are available to all workspaces.
    """
    result = service.create_script(
        name=script_data.name,
        category=script_data.category,
        content=script_data.content,
        description=script_data.description,
        subcategory=script_data.subcategory,
        script_metadata=script_data.script_metadata,
        required_packages=script_data.required_packages,
        input_schema=script_data.input_schema,
        output_schema=script_data.output_schema,
        tags=script_data.tags,
        documentation_url=script_data.documentation_url
    )
    
    response_data = CreateGlobalScriptResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Global script created successfully."
    )


# ============================================================================
# GET SCRIPT ENDPOINTS
# ============================================================================

@router.get("/scripts/{script_id}", response_model_exclude_none=True)
async def get_global_script(
    request: Request,
    script_id: str = Path(..., description="Script ID"),
    service = Depends(get_global_script_service),
) -> dict:
    """
    Get global script details (without content).
    
    Public endpoint - no authentication required.
    """
    result = service.get_script(
        script_id=script_id
    )
    
    response_data = GlobalScriptResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump()
    )


@router.get("/scripts/name/{name}", response_model_exclude_none=True)
async def get_script_by_name(
    request: Request,
    name: str = Path(..., description="Script name"),
    service = Depends(get_global_script_service),
) -> dict:
    """
    Get global script by name.
    
    Public endpoint - no authentication required.
    """
    result = service.get_script_by_name(
        name=name
    )
    
    response_data = GlobalScriptByNameResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump()
    )


@router.get("/scripts/{script_id}/content", response_model_exclude_none=True)
async def get_script_content(
    request: Request,
    script_id: str = Path(..., description="Script ID"),
    service = Depends(get_global_script_service),
) -> dict:
    """
    Get script content and schemas.
    
    Public endpoint - no authentication required.
    """
    result = service.get_script_content(
        script_id=script_id
    )
    
    response_data = GlobalScriptContentResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump()
    )


@router.get("/scripts", response_model_exclude_none=True)
async def get_all_scripts(
    request: Request,
    category: Optional[str] = Query(None, description="Filter by category"),
    subcategory: Optional[str] = Query(None, description="Filter by subcategory"),
    service = Depends(get_global_script_service),
) -> dict:
    """
    Get all global scripts.
    
    Public endpoint - no authentication required.
    """
    result = service.get_all_scripts(
        category=category,
        subcategory=subcategory
    )
    
    response_data = AllGlobalScriptsResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump()
    )


@router.get("/scripts/categories", response_model_exclude_none=True)
async def get_categories(
    request: Request,
    service = Depends(get_global_script_service),
) -> dict:
    """
    Get all script categories.
    
    Public endpoint - no authentication required.
    """
    result = service.get_categories()
    
    response_data = CategoriesResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump()
    )


# ============================================================================
# UPDATE SCRIPT ENDPOINTS
# ============================================================================

@router.put("/scripts/{script_id}", response_model_exclude_none=True)
async def update_global_script(
    request: Request,
    script_id: str = Path(..., description="Script ID"),
    script_data: UpdateGlobalScriptRequest = ...,
    service = Depends(get_global_script_service),
    current_user: AuthenticatedUser = Depends(authenticate_admin),
) -> dict:
    """
    Update script metadata.
    
    Requires: Admin authentication
    Note: Script content cannot be changed. Create a new script instead.
    """
    result = service.update_script(
        script_id=script_id,
        description=script_data.description,
        tags=script_data.tags,
        documentation_url=script_data.documentation_url
    )
    
    response_data = GlobalScriptResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Script metadata updated successfully."
    )


# ============================================================================
# DELETE SCRIPT ENDPOINTS
# ============================================================================

@router.delete("/scripts/{script_id}", response_model_exclude_none=True)
async def delete_global_script(
    request: Request,
    script_id: str = Path(..., description="Script ID"),
    service = Depends(get_global_script_service),
    current_user: AuthenticatedUser = Depends(authenticate_admin),
) -> dict:
    """
    Delete global script.
    
    Requires: Admin authentication
    Note: Both file and database record will be deleted.
    """
    result = service.delete_script(
        script_id=script_id
    )
    
    response_data = DeleteGlobalScriptResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message="Script deleted successfully."
    )


# ============================================================================
# SEED SCRIPTS ENDPOINTS
# ============================================================================

@router.post("/scripts/seed", response_model_exclude_none=True)
async def seed_scripts(
    request: Request,
    seed_data: SeedScriptsRequest = ...,
    service = Depends(get_global_script_service),
    current_user: AuthenticatedUser = Depends(authenticate_admin),
) -> dict:
    """
    Seed global scripts (initial data).
    
    Requires: Admin authentication
    Note: Existing scripts with same name will be skipped.
    """
    result = service.seed_scripts(
        scripts_data=seed_data.scripts_data
    )
    
    response_data = SeedScriptsResponse(**result)
    return create_success_response(
        request,
        data=response_data.model_dump(),
        message=f"Script seeding completed. Created: {result['created']}, Skipped: {result['skipped']}."
    )

