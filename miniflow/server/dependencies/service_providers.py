from functools import lru_cache
from miniflow.services import *


@lru_cache(maxsize=1)
def get_agreement_service() -> AgreementService:
    return AgreementService()

@lru_cache(maxsize=1)
def get_user_role_service() -> UserRoleService:
    return UserRoleService()

@lru_cache(maxsize=1)
def get_workspace_plan_service() -> WorkspacePlanService:
    return WorkspacePlanService()

@lru_cache(maxsize=1)
def get_register_service() -> RegisterService:
    return RegisterService()

@lru_cache(maxsize=1)
def get_login_service() -> LoginService:
    return LoginService()

@lru_cache(maxsize=1)
def get_session_management_service() -> SessionManagementService:
    return SessionManagementService()

@lru_cache(maxsize=1)
def get_login_history_service() -> LoginHistoryService:
    return LoginHistoryService()

@lru_cache(maxsize=1)
def get_user_management_service() -> UserManagementService:
    return UserManagementService()

@lru_cache(maxsize=1)
def get_user_profile_service() -> UserProfileService:
    return UserProfileService()

@lru_cache(maxsize=1)
def get_user_password_service() -> UserPasswordService:
    return UserPasswordService()

@lru_cache(maxsize=1)
def get_workspace_management_service() -> WorkspaceManagementService:
    return WorkspaceManagementService()

# Alias for workspace service
get_workspace_service = get_workspace_management_service

@lru_cache(maxsize=1)
def get_workspace_member_service() -> WorkspaceMemberService:
    return WorkspaceMemberService()

@lru_cache(maxsize=1)
def get_workspace_invitation_service() -> WorkspaceInvitationService:
    return WorkspaceInvitationService()

@lru_cache(maxsize=1)
def get_workspace_plan_management_service() -> WorkspacePlanManagementService:
    return WorkspacePlanManagementService()

@lru_cache(maxsize=1)
def get_api_key_service() -> ApiKeyService:
    return ApiKeyService()

@lru_cache(maxsize=1)
def get_credential_service() -> CredentialService:
    return CredentialService()

@lru_cache(maxsize=1)
def get_file_service() -> FileService:
    return FileService()

@lru_cache(maxsize=1)
def get_variable_service() -> VariableService:
    return VariableService()

@lru_cache(maxsize=1)
def get_database_service() -> DatabaseService:
    return DatabaseService()

@lru_cache(maxsize=1)
def get_custom_script_service() -> CustomScriptService:
    return CustomScriptService()

@lru_cache(maxsize=1)
def get_global_script_service() -> GlobalScriptService:
    return GlobalScriptService()

@lru_cache(maxsize=1)
def get_script_testing_service() -> ScriptTestingService:
    return ScriptTestingService()

@lru_cache(maxsize=1)
def get_workflow_service() -> WorkflowManagementService:
    return WorkflowManagementService()

@lru_cache(maxsize=1)
def get_node_service() -> NodeService:
    return NodeService()

@lru_cache(maxsize=1)
def get_edge_service() -> EdgeService:
    return EdgeService()

@lru_cache(maxsize=1)
def get_trigger_service() -> TriggerService:
    return TriggerService()

@lru_cache(maxsize=1)
def get_execution_service() -> ExecutionManagementService:
    return ExecutionManagementService()

@lru_cache(maxsize=1)
def get_execution_input_service() -> ExecutionInputService:
    return ExecutionInputService()

@lru_cache(maxsize=1)
def get_execution_output_service() -> ExecutionOutputService:
    return ExecutionOutputService()