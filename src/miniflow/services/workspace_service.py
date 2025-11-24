from typing import Optional
from datetime import datetime, timezone, timedelta

from src.miniflow.database import with_transaction, with_readonly_session
from src.miniflow.database import RepositoryRegistry

from src.miniflow.core.exceptions import BusinessRuleViolationError
from src.miniflow.utils.helpers.file_helper import (
    get_workspace_file_path,
    get_workspace_custom_script_path,
    get_workspace_temp_path,
    delete_folder,
)


class WorkspaceService:

    def __init__(self):
        self._registry: RepositoryRegistry = RepositoryRegistry()

        self._workspace_repo = self._registry.workspace_repository
        self._workspace_member_repo = self._registry.workspace_member_repository
        self._workspace_invitation_repo = self._registry.workspace_invitation_repository
        self._workspace_plan_repo = self._registry.workspace_plans_repository
        self._user_roles_repo = self._registry.user_roles_repository
        self._user_repo = self._registry.user_repository
        self._workflow_repo = self._registry.workflow_repository
        self._custom_script_repo = self._registry.custom_script_repository
        self._execution_repo = self._registry.execution_repository
        self._execution_input_repo = self._registry.execution_input_repository
        self._execution_output_repo = self._registry.execution_output_repository
        self._trigger_repo = self._registry.trigger_repository
        self._variable_repo = self._registry.variable_repository
        self._file_repo = self._registry.file_repository
        self._database_repo = self._registry.database_repository
        self._credential_repo = self._registry.credential_repository
        self._api_key_repo = self._registry.api_key_repository

    @with_readonly_session(manager=None)
    def validate_workspace(
        self,
        session,
        *,
        workspace_id: str,
        check_suspended: bool = True,
    ):
        workspace = self._workspace_repo._get_by_id(session, record_id=workspace_id, include_deleted=False)
        if not workspace:
            raise BusinessRuleViolationError(
                rule_name="workspace_not_found",
                rule_detail="workspace not found",
                message="Workspace not found",
            )
        if check_suspended and workspace.is_suspended:
            raise BusinessRuleViolationError(
                rule_name="workspace_suspended",
                rule_detail="workspace suspended",
                message="Workspace is suspended",
            )
        return True

    @with_transaction(manager=None)
    def create_workspace(
        self,
        session,
        *,
        name: str,
        slug: str,
        description: Optional[str] = None,
        owner_id: str,
    ):
        user = self._user_repo._get_by_id(session, record_id=owner_id, include_deleted=False)
        if not user:
            raise BusinessRuleViolationError(
                rule_name="user_not_found",
                rule_detail="user not found",
                message="User not found",
            )

        if self._workspace_repo._get_by_slug(session, slug=slug, include_deleted=False):
            raise BusinessRuleViolationError(
                rule_name="workspace_already_exists",
                rule_detail="workspace already exists",
                message="Workspace already exists",
            )
        
        if self._workspace_repo._get_by_name(session, name=name, include_deleted=False):
            raise BusinessRuleViolationError(
                rule_name="workspace_already_exists",
                rule_detail="workspace already exists",
                message="Workspace already exists",
            )

        plan = self._workspace_plan_repo._get_by_name(session, name="Freemium")
        if not plan:
            raise BusinessRuleViolationError(
                rule_name="plan_not_found",
                rule_detail="Freemium plan not found",
                message="Freemium plan not found in system",
            )

        owner_role = self._user_roles_repo._get_by_name(session, name="Owner")
        if not owner_role:
            raise BusinessRuleViolationError(
                rule_name="role_not_found",
                rule_detail="Owner role not found",
                message="Owner role not found in system",
            )

        workspace = self._workspace_repo._create(
            session, 
            name=name, 
            slug=slug, 
            description=description, 
            owner_id=owner_id, 
            plan_id=plan.id,
            member_limit=plan.max_members_per_workspace,
            current_member_count=1,
            workflow_limit=plan.max_workflows_per_workspace,
            current_workflow_count=0,
            custom_script_limit=plan.max_custom_scripts_per_workspace,
            current_custom_script_count=0,
            storage_limit_mb=plan.storage_limit_mb_per_workspace,
            current_storage_mb=0,
            api_key_limit=plan.max_api_keys_per_workspace,
            current_api_key_count=0,
            monthly_execution_limit=plan.monthly_execution_limit,
            current_month_executions=0,
            monthly_concurrent_executions=plan.max_concurrent_executions,
            current_month_concurrent_executions=0,
            current_period_start = datetime.now(timezone.utc),
            current_period_end = datetime.now(timezone.utc) + timedelta(days=30),
            )

        self._workspace_member_repo._create(
            session,
            workspace_id=workspace.id,
            user_id=owner_id,
            role_id=owner_role.id,
            invited_by=owner_id,
            joined_at=datetime.now(timezone.utc),
            last_accessed_at=datetime.now(timezone.utc),
            custom_permissions=None,
        )

        user.current_workspace_count += 1
        user.current_free_workspace_count += 1
        session.add(user)

        return {
            "workspace_id": workspace.id,
            "workspace_name": workspace.name,
            "workspace_slug": workspace.slug,
            "workspace_description": workspace.description,
            "workspace_owner_id": workspace.owner_id,
        }

    @with_readonly_session(manager=None)
    def get_workspace_details(
        self,
        session,
        *,
        workspace_id: str,
    ):
        workspace = self._workspace_repo._get_by_id(session, record_id=workspace_id, include_deleted=False)
        if not workspace:
            raise BusinessRuleViolationError(
                rule_name="workspace_not_found",
                rule_detail="workspace not found",
                message="Workspace not found",
            )

        if not workspace.owner:
            raise BusinessRuleViolationError(
                rule_name="workspace_owner_not_found",
                rule_detail="workspace owner not found",
                message="Workspace owner not found",
            )

        return {
            "workspace_id": workspace.id,
            "workspace_name": workspace.name,
            "workspace_slug": workspace.slug,
            "workspace_description": workspace.description,
            "workspace_owner_id": workspace.owner_id,
            "workspace_owner_name": workspace.owner.name,
            "workspace_owner_email": workspace.owner.email,
        }

    @with_readonly_session(manager=None)
    def get_workspace_limits(
        self,
        session,
        *,
        workspace_id: str,
    ):
        workspace = self._workspace_repo._get_by_id(session, record_id=workspace_id, include_deleted=False)
        if not workspace:
            raise BusinessRuleViolationError(
                rule_name="workspace_not_found",
                rule_detail="workspace not found",
                message="Workspace not found",
            )

        return {
            "max_members_per_workspace": workspace.member_limit,
            "current_members_count": workspace.current_member_count,
            "max_workflows_per_workspace": workspace.workflow_limit,
            "current_workflows_count": workspace.current_workflow_count,
            "max_custom_scripts_per_workspace": workspace.custom_script_limit,
            "current_custom_scripts_count": workspace.current_custom_script_count,
            "storage_limit_mb_per_workspace": workspace.storage_limit_mb,
            "current_storage_mb": workspace.current_storage_mb,
            "max_api_keys_per_workspace": workspace.api_key_limit,
            "current_api_keys_count": workspace.current_api_key_count,
            "monthly_execution_limit": workspace.monthly_execution_limit,
            "current_month_executions": workspace.current_month_executions,
            "monthly_concurrent_executions": workspace.monthly_concurrent_executions,
            "current_month_concurrent_executions": workspace.current_month_concurrent_executions,
            "current_period_start": workspace.current_period_start.isoformat() if workspace.current_period_start else None,
            "current_period_end": workspace.current_period_end.isoformat() if workspace.current_period_end else None,
        }

    @with_transaction(manager=None)
    def update_workspace(
        self,
        session,
        *,
        workspace_id: str,
        name: Optional[str] = None,
        slug: Optional[str] = None,
        description: Optional[str] = None,
    ):
        workspace = self._workspace_repo._get_by_id(session, record_id=workspace_id, include_deleted=False)
        if not workspace:
            raise BusinessRuleViolationError(
                rule_name="workspace_not_found",
                rule_detail="workspace not found",
                message="Workspace not found",
            )

        if name:
            if name != workspace.name:
                if self._workspace_repo._get_by_name(session, name=name, include_deleted=False):
                    raise BusinessRuleViolationError(
                        rule_name="workspace_already_exists",
                        rule_detail="workspace already exists",
                        message="Workspace already exists",
                    )
                workspace.name = name
        if slug:
            if slug != workspace.slug:
                if self._workspace_repo._get_by_slug(session, slug=slug, include_deleted=False):
                    raise BusinessRuleViolationError(
                        rule_name="workspace_already_exists",
                        rule_detail="workspace already exists",
                        message="Workspace already exists",
                    )
                workspace.slug = slug

        if description:
            workspace.description = description

        return {
            "workspace_id": workspace.id,
            "workspace_name": workspace.name,
            "workspace_slug": workspace.slug,
            "workspace_description": workspace.description,
        }

    @with_transaction(manager=None)
    def delete_workspace(
        self,
        session,
        *,
        workspace_id: str,
    ):
        workspace = self._workspace_repo._get_by_id(session, record_id=workspace_id, include_deleted=False)
        if not workspace:
            raise BusinessRuleViolationError(
                rule_name="workspace_not_found",
                rule_detail="workspace not found",
                message="Workspace not found",
            )

        owner_id = workspace.owner_id

        deleted_members = 0
        members = self._workspace_member_repo._get_all(session, workspace_id=workspace_id, include_deleted=False)
        for member in members:
            self._workspace_member_repo._delete(session, record_id=member.id)
            deleted_members += 1

        deleted_invitations = 0
        invitations = self._workspace_invitation_repo._get_all(session, workspace_id=workspace_id, include_deleted=False)
        for invitation in invitations:
            self._workspace_invitation_repo._delete(session, record_id=invitation.id)
            deleted_invitations += 1

        deleted_workflows = 0
        workflows = self._workflow_repo._get_all(session, workspace_id=workspace_id, include_deleted=False)
        for workflow in workflows:
            self._workflow_repo._delete(session, record_id=workflow.id)
            deleted_workflows += 1

        deleted_custom_scripts = 0
        custom_scripts = self._custom_script_repo._get_all(session, workspace_id=workspace_id, include_deleted=False)
        for custom_script in custom_scripts:
            self._custom_script_repo._delete(session, record_id=custom_script.id)
            deleted_custom_scripts += 1

        deleted_executions = 0
        executions = self._execution_repo._get_all(session, workspace_id=workspace_id, include_deleted=False)
        for execution in executions:
            self._execution_repo._delete(session, record_id=execution.id)
            deleted_executions += 1

        deleted_execution_inputs = 0
        execution_inputs = self._execution_input_repo._get_all(session, workspace_id=workspace_id, include_deleted=False)
        for execution_input in execution_inputs:
            self._execution_input_repo._delete(session, record_id=execution_input.id)
            deleted_execution_inputs += 1

        deleted_execution_outputs = 0
        execution_outputs = self._execution_output_repo._get_all(session, workspace_id=workspace_id, include_deleted=False)
        for execution_output in execution_outputs:
            self._execution_output_repo._delete(session, record_id=execution_output.id)
            deleted_execution_outputs += 1

        deleted_triggers = 0
        triggers = self._trigger_repo._get_all(session, workspace_id=workspace_id, include_deleted=False)
        for trigger in triggers:
            self._trigger_repo._delete(session, record_id=trigger.id)
            deleted_triggers += 1

        deleted_variables = 0
        variables = self._variable_repo._get_all(session, workspace_id=workspace_id, include_deleted=False)
        for variable in variables:
            self._variable_repo._delete(session, record_id=variable.id)
            deleted_variables += 1

        deleted_files = 0
        files = self._file_repo._get_all(session, workspace_id=workspace_id, include_deleted=False)
        for file in files:
            self._file_repo._delete(session, record_id=file.id)
            deleted_files += 1

        deleted_databases = 0
        databases = self._database_repo._get_all(session, workspace_id=workspace_id, include_deleted=False)
        for database in databases:
            self._database_repo._delete(session, record_id=database.id)
            deleted_databases += 1

        deleted_credentials = 0
        credentials = self._credential_repo._get_all(session, workspace_id=workspace_id, include_deleted=False)
        for credential in credentials:
            self._credential_repo._delete(session, record_id=credential.id)
            deleted_credentials += 1

        deleted_api_keys = 0
        api_keys = self._api_key_repo._get_all(session, workspace_id=workspace_id, include_deleted=False)
        for api_key in api_keys:
            self._api_key_repo._delete(session, record_id=api_key.id)
            deleted_api_keys += 1

        user = self._user_repo._get_by_id(session, record_id=owner_id, include_deleted=False)
        if user:
            user.current_workspace_count -= 1
            user.current_free_workspace_count -= 1
            session.add(user)

        self._workspace_repo._delete(session, record_id=workspace.id)

        try:
            files_path = get_workspace_file_path(workspace_id)
            delete_folder(files_path)
        except Exception:
            pass

        try:
            scripts_path = get_workspace_custom_script_path(workspace_id)
            delete_folder(scripts_path)
        except Exception:
            pass

        try:
            temp_path = get_workspace_temp_path(workspace_id)
            delete_folder(temp_path)
        except Exception:
            pass

        return {
            "deleted_members": deleted_members,
            "deleted_invitations": deleted_invitations,
            "deleted_workflows": deleted_workflows,
            "deleted_custom_scripts": deleted_custom_scripts,
            "deleted_executions": deleted_executions,
            "deleted_execution_inputs": deleted_execution_inputs,
            "deleted_execution_outputs": deleted_execution_outputs,
            "deleted_triggers": deleted_triggers,
            "deleted_variables": deleted_variables,
            "deleted_files": deleted_files,
            "deleted_databases": deleted_databases,
            "deleted_credentials": deleted_credentials,
            "deleted_api_keys": deleted_api_keys,
        }