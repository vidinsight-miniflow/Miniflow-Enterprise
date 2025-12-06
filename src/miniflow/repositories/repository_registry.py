# Info Repositories
from ._1_info_reop import (
    WorkspacePlansRepository, 
    UserRolesRepository,
    AgreementVersionRepository,
    UserAgreementAcceptanceRepository,
)

# User Repositories
from ._3_user_repo import (
    UserRepository,
    UserPreferenceRepository,
    PasswordHistoryRepository,
    LoginHistoryRepository,
    AuthSessionRepository,
)

# Workspace Repositories
from ._4_workspace_repo import (
    WorkspaceRepository,
    WorkspaceMemberRepository,
    WorkspaceInvitationRepository,
)

# Script Repositories
from ._6_script_repo import (
    ScriptRepository,
    CustomScriptRepository,
)

# Workflow Repositories
from ._7_workflow_repo import (
    WorkflowRepository,
    NodeRepository,
    EdgeRepository,
    TriggerRepository,
)

# Resource Repositories
from ._5_resource_repo import (
    CredentialRepository,
    DatabaseRepository,
    VariableRepository,
    FileRepository,
    ApiKeyRepository,
)

# Execution Repositories
from ._8_execution_repo import (
    ExecutionRepository,
    ExecutionInputRepository,
    ExecutionOutputRepository,
)


class RepositoryRegistry:
    """
    Central registry for all repository instances.
    Provides singleton access to all repositories via methods.
    """
    
    # Singleton instances
    _user_roles_repo = None
    _workspace_plans_repo = None
    _agreement_version_repo = None
    _user_agreement_acceptance_repo = None
    _user_repo = None
    _user_preference_repo = None
    _password_history_repo = None
    _login_history_repo = None
    _auth_session_repo = None
    _workspace_repo = None
    _workspace_member_repo = None
    _workspace_invitation_repo = None
    _global_script_repo = None
    _custom_script_repo = None
    _workflow_repo = None
    _node_repo = None
    _edge_repo = None
    _trigger_repo = None
    _credential_repo = None
    _database_repo = None
    _variable_repo = None
    _file_repo = None
    _api_key_repo = None
    _execution_repo = None
    _execution_input_repo = None
    _execution_output_repo = None
    
    # Info Repositories
    @classmethod
    def user_roles_repository(cls):
        if cls._user_roles_repo is None:
            cls._user_roles_repo = UserRolesRepository()
        return cls._user_roles_repo
    
    @classmethod
    def workspace_plans_repository(cls):
        if cls._workspace_plans_repo is None:
            cls._workspace_plans_repo = WorkspacePlansRepository()
        return cls._workspace_plans_repo
    
    @classmethod
    def agreement_version_repository(cls):
        if cls._agreement_version_repo is None:
            cls._agreement_version_repo = AgreementVersionRepository()
        return cls._agreement_version_repo
    
    @classmethod
    def user_agreement_acceptance_repository(cls):
        if cls._user_agreement_acceptance_repo is None:
            cls._user_agreement_acceptance_repo = UserAgreementAcceptanceRepository()
        return cls._user_agreement_acceptance_repo
    
    # User Repositories
    @classmethod
    def user_repository(cls):
        if cls._user_repo is None:
            cls._user_repo = UserRepository()
        return cls._user_repo
    
    @classmethod
    def user_preference_repository(cls):
        if cls._user_preference_repo is None:
            cls._user_preference_repo = UserPreferenceRepository()
        return cls._user_preference_repo
    
    @classmethod
    def password_history_repository(cls):
        if cls._password_history_repo is None:
            cls._password_history_repo = PasswordHistoryRepository()
        return cls._password_history_repo
    
    @classmethod
    def login_history_repository(cls):
        if cls._login_history_repo is None:
            cls._login_history_repo = LoginHistoryRepository()
        return cls._login_history_repo
    
    @classmethod
    def auth_session_repository(cls):
        if cls._auth_session_repo is None:
            cls._auth_session_repo = AuthSessionRepository()
        return cls._auth_session_repo
    
    # Workspace Repositories
    @classmethod
    def workspace_repository(cls):
        if cls._workspace_repo is None:
            cls._workspace_repo = WorkspaceRepository()
        return cls._workspace_repo
    
    @classmethod
    def workspace_member_repository(cls):
        if cls._workspace_member_repo is None:
            cls._workspace_member_repo = WorkspaceMemberRepository()
        return cls._workspace_member_repo
    
    @classmethod
    def workspace_invitation_repository(cls):
        if cls._workspace_invitation_repo is None:
            cls._workspace_invitation_repo = WorkspaceInvitationRepository()
        return cls._workspace_invitation_repo
    
    # Script Repositories
    @classmethod
    def global_script_repository(cls):
        if cls._global_script_repo is None:
            cls._global_script_repo = ScriptRepository()
        return cls._global_script_repo
    
    @classmethod
    def script_repository(cls):
        """Alias for global_script_repository for backward compatibility."""
        return cls.global_script_repository()
    
    @classmethod
    def custom_script_repository(cls):
        if cls._custom_script_repo is None:
            cls._custom_script_repo = CustomScriptRepository()
        return cls._custom_script_repo
    
    # Workflow Repositories
    @classmethod
    def workflow_repository(cls):
        if cls._workflow_repo is None:
            cls._workflow_repo = WorkflowRepository()
        return cls._workflow_repo
    
    @classmethod
    def node_repository(cls):
        if cls._node_repo is None:
            cls._node_repo = NodeRepository()
        return cls._node_repo
    
    @classmethod
    def edge_repository(cls):
        if cls._edge_repo is None:
            cls._edge_repo = EdgeRepository()
        return cls._edge_repo
    
    @classmethod
    def trigger_repository(cls):
        if cls._trigger_repo is None:
            cls._trigger_repo = TriggerRepository()
        return cls._trigger_repo
    
    # Resource Repositories
    @classmethod
    def credential_repository(cls):
        if cls._credential_repo is None:
            cls._credential_repo = CredentialRepository()
        return cls._credential_repo
    
    @classmethod
    def database_repository(cls):
        if cls._database_repo is None:
            cls._database_repo = DatabaseRepository()
        return cls._database_repo
    
    @classmethod
    def variable_repository(cls):
        if cls._variable_repo is None:
            cls._variable_repo = VariableRepository()
        return cls._variable_repo
    
    @classmethod
    def file_repository(cls):
        if cls._file_repo is None:
            cls._file_repo = FileRepository()
        return cls._file_repo
    
    @classmethod
    def api_key_repository(cls):
        if cls._api_key_repo is None:
            cls._api_key_repo = ApiKeyRepository()
        return cls._api_key_repo
    
    # Execution Repositories
    @classmethod
    def execution_repository(cls):
        if cls._execution_repo is None:
            cls._execution_repo = ExecutionRepository()
        return cls._execution_repo
    
    @classmethod
    def execution_input_repository(cls):
        if cls._execution_input_repo is None:
            cls._execution_input_repo = ExecutionInputRepository()
        return cls._execution_input_repo
    
    @classmethod
    def execution_output_repository(cls):
        if cls._execution_output_repo is None:
            cls._execution_output_repo = ExecutionOutputRepository()
        return cls._execution_output_repo
