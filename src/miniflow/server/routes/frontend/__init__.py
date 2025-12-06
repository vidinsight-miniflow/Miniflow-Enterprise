"""Frontend routes."""

from fastapi import APIRouter

from .agreement_routes import router as agreement_router
from .user_role_routes import router as user_role_router
from .workspace_plan_routes import router as workspace_plan_router
from .auth_routes import router as auth_router
from .session_routes import router as session_router
from .login_history_routes import router as login_history_router
from .user_management_routes import router as user_management_router
from .user_profile_routes import router as user_profile_router
from .user_password_routes import router as user_password_router
from .workspace_management_routes import router as workspace_management_router
from .workspace_member_routes import router as workspace_member_router
from .workspace_plan_management_routes import router as workspace_plan_management_router
from .workspace_invitation_routes import router as workspace_invitation_router
from .variable_routes import router as variable_router
from .credential_routes import router as credential_router
from .api_key_routes import router as api_key_router
from .database_routes import router as database_router
from .file_routes import router as file_router
from .custom_script_routes import router as custom_script_router
from .global_script_routes import router as global_script_router
from .script_testing_routes import router as script_testing_router
from .workflow_management_routes import router as workflow_management_router
from .node_routes import router as node_router
from .edge_routes import router as edge_router
from .trigger_routes import router as trigger_router
from .execution_management_routes import router as execution_management_router

# Create main frontend router
router = APIRouter(prefix="/frontend", tags=["Frontend"])

# Include all sub-routers
router.include_router(agreement_router)
router.include_router(user_role_router)
router.include_router(workspace_plan_router)
router.include_router(auth_router)
router.include_router(session_router)
router.include_router(login_history_router)
router.include_router(user_management_router)
router.include_router(user_profile_router)
router.include_router(user_password_router)
router.include_router(workspace_management_router)
router.include_router(workspace_member_router)
router.include_router(workspace_plan_management_router)
router.include_router(workspace_invitation_router)
router.include_router(variable_router)
router.include_router(credential_router)
router.include_router(api_key_router)
router.include_router(database_router)
router.include_router(file_router)
router.include_router(custom_script_router)
router.include_router(global_script_router)
router.include_router(script_testing_router)
router.include_router(workflow_management_router)
router.include_router(node_router)
router.include_router(edge_router)
router.include_router(trigger_router)
router.include_router(execution_management_router)

__all__ = ["router"]

