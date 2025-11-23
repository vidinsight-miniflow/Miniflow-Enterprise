from .info_repositories import (
    WorkspacePlansRepository, 
    UserRolesRepository
)

from .user_repositories import (
    UserRepository,
    UserPreferenceRepository,
    PasswordHistoryRepository,
    LoginHistoryRepository,
    AuthSessionRepository,
)

from .compliance_repositories import (
    AgreementVersionRepository,
    UserAgreementAcceptanceRepository,
)
from .workspace_repositories import (
    WorkspaceRepository,
    WorkspaceMemberRepository,
    WorkspaceInvitationRepository,
)
from .workflow_repositories import (
    ScriptRepository,
    CustomScriptRepository,
    WorkflowRepository,
    NodeRepository,
    EdgeRepository,
    TriggerRepository,
)
from .resource_repositories import (
    CredentialRepository,
    DatabaseRepository,
    VariableRepository,
    FileRepository,
    ApiKeyRepository,
)
from .notification_repositories import NotificationRepository
from .execution_repositories import (
    ExecutionRepository,
    ExecutionInputRepository,
    ExecutionOutputRepository,
)


class RepositoryRegistry:
    """
    Central registry for all repository instances.
    Provides singleton access to all repositories.
    """
    
    # Info Repositories
    user_roles_repository = UserRolesRepository()
    workspace_plans_repository = WorkspacePlansRepository()
    
    # User Repositories
    user_repository = UserRepository()
    user_preference_repository = UserPreferenceRepository()
    password_history_repository = PasswordHistoryRepository()
    login_history_repository = LoginHistoryRepository()
    auth_session_repository = AuthSessionRepository()
    
    # Compliance Repositories
    agreement_version_repository = AgreementVersionRepository()
    user_agreement_acceptance_repository = UserAgreementAcceptanceRepository()
    
    # Workspace Repositories
    workspace_repository = WorkspaceRepository()
    workspace_member_repository = WorkspaceMemberRepository()
    workspace_invitation_repository = WorkspaceInvitationRepository()
    
    # Workflow Repositories
    script_repository = ScriptRepository()
    custom_script_repository = CustomScriptRepository()
    workflow_repository = WorkflowRepository()
    node_repository = NodeRepository()
    edge_repository = EdgeRepository()
    trigger_repository = TriggerRepository()
    
    # Resource Repositories
    credential_repository = CredentialRepository()
    database_repository = DatabaseRepository()
    variable_repository = VariableRepository()
    file_repository = FileRepository()
    api_key_repository = ApiKeyRepository()
    
    # Notification Repositories
    notification_repository = NotificationRepository()
    
    # Execution Repositories
    execution_repository = ExecutionRepository()
    execution_input_repository = ExecutionInputRepository()
    execution_output_repository = ExecutionOutputRepository()