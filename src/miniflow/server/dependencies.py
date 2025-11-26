from functools import lru_cache
from src.miniflow.services import *


@lru_cache(maxsize=1)
def get_auth_service() -> AuthenticationService:
    return AuthenticationService()

@lru_cache(maxsize=1)
def get_workspace_plans_service() -> WorkspacePlansService:
    return WorkspacePlansService()

@lru_cache(maxsize=1)
def get_user_role_service() -> UserRolesService:
    return UserRolesService()

@lru_cache(maxsize=1)
def get_agreement_service() -> AgreementService:
    return AgreementService()

@lru_cache(maxsize=1)
def get_user_service() -> UserService:
    return UserService()

@lru_cache(maxsize=1)
def get_workspace_service() -> WorkspaceService:
    return WorkspaceService()

@lru_cache(maxsize=1)
def get_workspace_member_service() -> WorkspaceMemberService:
    return WorkspaceMemberService()

@lru_cache(maxsize=1)
def get_workspace_invatation_service() -> WorkspaceInvatationService:
    return WorkspaceInvatationService()

@lru_cache(maxsize=1)
def get_api_key_service() -> ApiKeyService:
    return ApiKeyService()

@lru_cache(maxsize=1)
def get_variable_service() -> VariableService:
    return VariableService()

@lru_cache(maxsize=1)
def get_database_service() -> DatabaseService:
    return DatabaseService()

@lru_cache(maxsize=1)
def get_file_service() -> FileService:
    return FileService()

@lru_cache(maxsize=1)
def get_credential_service() -> CredentialService:
    return CredentialService()

@lru_cache(maxsize=1)
def get_global_script_service() -> GlobalScriptService:
    return GlobalScriptService()

@lru_cache(maxsize=1)
def get_custom_script_service() -> CustomScriptService:
    return CustomScriptService()

@lru_cache(maxsize=1)
def get_workflow_service() -> WorkflowService:
    return WorkflowService()

@lru_cache(maxsize=1)
def get_trigger_service() -> TriggerService:
    return TriggerService()

@lru_cache(maxsize=1)
def get_node_service() -> NodeService:
    return NodeService()

@lru_cache(maxsize=1)
def get_edge_service() -> EdgeService:
    return EdgeService()