from typing import Optional, List
from datetime import datetime, timezone

from src.miniflow.database import with_transaction, with_readonly_session
from src.miniflow.database import RepositoryRegistry

from src.miniflow.core.exceptions import BusinessRuleViolationError
from src.miniflow.database.models.enums import InvitationStatus


class WorkspaceMemberService:

    def __init__(self):
        self._registry: RepositoryRegistry = RepositoryRegistry()

        self._workspace_member_repo = self._registry.workspace_member_repository
        self._workspace_repo = self._registry.workspace_repository
        self._workspace_invitation_repo = self._registry.workspace_invitation_repository
        self._user_repo = self._registry.user_repository
        self._user_roles_repo = self._registry.user_roles_repository

    # ========================================================================================= HELPER METHODS =====

    def _validate_workspace(self, session, workspace_id: str):
        """Workspace var mı kontrol et"""
        workspace = self._workspace_repo._get_by_id(session, record_id=workspace_id, include_deleted=False)
        if not workspace:
            raise BusinessRuleViolationError(
                rule_name="workspace_not_found",
                rule_detail="workspace not found",
                message="Workspace not found",
            )
        return workspace

    def _validate_user(self, session, user_id: str, error_name: str = "user_not_found"):
        """User var mı kontrol et"""
        user = self._user_repo._get_by_id(session, record_id=user_id, include_deleted=False)
        if not user:
            raise BusinessRuleViolationError(
                rule_name=error_name,
                rule_detail=error_name.replace("_", " "),
                message=error_name.replace("_", " ").title(),
            )
        return user

    def _validate_role(self, session, role_id: str):
        """Role var mı kontrol et"""
        role = self._user_roles_repo._get_by_id(session, record_id=role_id, include_deleted=False)
        if not role:
            raise BusinessRuleViolationError(
                rule_name="role_not_found",
                rule_detail="role not found",
                message="Role not found",
            )
        return role

    def _check_member_limit(self, workspace):
        """Member limit kontrolü"""
        if workspace.current_member_count >= workspace.member_limit:
            raise BusinessRuleViolationError(
                rule_name="workspace_member_limit_reached",
                rule_detail="workspace member limit reached",
                message="Workspace member limit reached",
            )

    def _check_existing_member(self, session, workspace_id: str, user_id: str):
        """Kullanıcı zaten member mı kontrol et"""
        existing = self._workspace_member_repo._get_by_workspace_id_and_user_id(
            session, workspace_id=workspace_id, user_id=user_id, include_deleted=False
        )
        if existing:
            raise BusinessRuleViolationError(
                rule_name="user_already_member",
                rule_detail="user already member",
                message="User is already a member of this workspace",
            )

    def _create_member(
        self,
        session,
        workspace_id: str,
        user_id: str,
        role_id: str,
        invited_by: str,
        workspace,
    ):
        """Ortak member oluşturma metodu"""
        self._check_member_limit(workspace)
        self._check_existing_member(session, workspace_id, user_id)

        member = self._workspace_member_repo._create(
            session,
            workspace_id=workspace_id,
            user_id=user_id,
            role_id=role_id,
            invited_by=invited_by,
            joined_at=datetime.now(timezone.utc),
            last_accessed_at=datetime.now(timezone.utc),
            custom_permissions=None,
        )

        workspace.current_member_count += 1
        session.add(workspace)

        return member

    @with_readonly_session(manager=None)
    def validate_workspace_member(
        self,
        session,
        *,
        workspace_id: str,
        user_id: str,
    ):
        self._validate_workspace(session, workspace_id)
        self._validate_user(session, user_id)

        member = self._workspace_member_repo._get_by_workspace_id_and_user_id(session, workspace_id=workspace_id, user_id=user_id, include_deleted=False)
        if not member:
            raise BusinessRuleViolationError(
                rule_name="workspace_member_not_found",
                rule_detail="workspace member not found",
                message="Workspace member not found",
            )

        return True

    @with_transaction(manager=None)
    def add_workspace_member(
        self,
        session,
        *,
        workspace_id: str,
        owner_id: str,
        user_id: str,
        role_id: str,
    ):
        workspace = self._validate_workspace(session, workspace_id)
        self._validate_user(session, owner_id, "owner_not_found")
        self._validate_user(session, user_id)
        self._validate_role(session, role_id)

        member = self._create_member(
            session,
            workspace_id=workspace_id,
            user_id=user_id,
            role_id=role_id,
            invited_by=owner_id,
            workspace=workspace,
        )

        return member.to_dict()

    @with_transaction(manager=None)
    def remove_workspace_member(
        self,
        session,
        *,
        workspace_id: str,
        user_id: str,
    ):
        workspace = self._validate_workspace(session, workspace_id)
        self._validate_user(session, user_id)

        member = self._workspace_member_repo._get_by_workspace_id_and_user_id(session, workspace_id=workspace_id, user_id=user_id, include_deleted=False)
        if not member:
            raise BusinessRuleViolationError(
                rule_name="workspace_member_not_found",
                rule_detail="workspace member not found",
                message="Workspace member not found",
            )

        if workspace.owner_id == user_id:
            raise BusinessRuleViolationError(
                rule_name="cannot_remove_owner",
                rule_detail="cannot remove owner",
                message="Cannot remove workspace owner. Transfer ownership first or delete the workspace.",
            )

        self._workspace_member_repo._delete(session, record_id=member.id)

        if workspace.current_member_count > 0:
            workspace.current_member_count -= 1
        session.add(workspace)

        return True

    @with_readonly_session(manager=None)
    def get_workspace_members(
        self,
        session,
        *,
        workspace_id: str,
    ):
        self._validate_workspace(session, workspace_id)
        members = self._workspace_member_repo._get_all(session, workspace_id=workspace_id, include_deleted=False)
        return [member.to_dict() for member in members]

    @with_readonly_session(manager=None)
    def get_workspace_member(
        self,
        session,
        *,
        workspace_id: str,
        user_id: str,
    ):
        self._validate_workspace(session, workspace_id)
        member = self._workspace_member_repo._get_by_workspace_id_and_user_id(session, workspace_id=workspace_id, user_id=user_id, include_deleted=False)
        if not member:
            raise BusinessRuleViolationError(
                rule_name="workspace_member_not_found",
                rule_detail="workspace member not found",
                message="Workspace member not found",
            )
        return member.to_dict()

    @with_readonly_session(manager=None)
    def get_workspace_member_permissions(
        self,
        session,
        *,
        user_id: str,
        workspace_id: str,
    ):
        self._validate_workspace(session, workspace_id)
        self._validate_user(session, user_id)

        member = self._workspace_member_repo._get_by_workspace_id_and_user_id(session, workspace_id=workspace_id, user_id=user_id, include_deleted=False)
        if not member:
            raise BusinessRuleViolationError(
                rule_name="workspace_member_not_found",
                rule_detail="workspace member not found",
                message="Workspace member not found",
            )

        role = self._validate_role(session, member.role_id)

        return {
            "role_name": role.name,
            "can_view_workspace": role.can_view_workspace,
            "can_edit_workspace": role.can_edit_workspace,
            "can_delete_workspace": role.can_delete_workspace,
            "can_invite_members": role.can_invite_members,
            "can_remove_members": role.can_remove_members,
            "can_change_plan": role.can_change_plan,
            "can_view_workflows": role.can_view_workflows,
            "can_create_workflows": role.can_create_workflows,
            "can_edit_workflows": role.can_edit_workflows,
            "can_delete_workflows": role.can_delete_workflows,
            "can_execute_workflows": role.can_execute_workflows,
            "can_share_workflows": role.can_share_workflows,
            "can_view_credentials": role.can_view_credentials,
            "can_create_credentials": role.can_create_credentials,
            "can_edit_credentials": role.can_edit_credentials,
            "can_delete_credentials": role.can_delete_credentials,
            "can_share_credentials": role.can_share_credentials,
            "can_view_credential_values": role.can_view_credential_values,
            "can_view_files": role.can_view_files,
            "can_upload_files": role.can_upload_files,
            "can_download_files": role.can_download_files,
            "can_delete_files": role.can_delete_files,
            "can_share_files": role.can_share_files,
            "can_view_databases": role.can_view_databases,
            "can_create_databases": role.can_create_databases,
            "can_edit_databases": role.can_edit_databases,
            "can_delete_databases": role.can_delete_databases,
            "can_share_databases": role.can_share_databases,
            "can_view_connection_details": role.can_view_connection_details,
            "can_view_variables": role.can_view_variables,
            "can_create_variables": role.can_create_variables,
            "can_edit_variables": role.can_edit_variables,
            "can_delete_variables": role.can_delete_variables,
            "can_share_variables": role.can_share_variables,
            "can_view_variable_values": role.can_view_variable_values,
            "can_view_api_keys": role.can_view_api_keys,
            "can_create_api_keys": role.can_create_api_keys,
            "can_edit_api_keys": role.can_edit_api_keys,
            "can_delete_api_keys": role.can_delete_api_keys,
            "can_share_api_keys": role.can_share_api_keys,
            "can_view_api_key_values": role.can_view_api_key_values,
            "custom_permissions": member.custom_permissions,
        }

    @with_transaction(manager=None)
    def change_user_role(
        self,
        session,
        *,
        workspace_id: str,
        user_id: str,
        role_id: str,
    ):
        self._validate_workspace(session, workspace_id)
        self._validate_user(session, user_id)
        self._validate_role(session, role_id)

        member = self._workspace_member_repo._get_by_workspace_id_and_user_id(session, workspace_id=workspace_id, user_id=user_id, include_deleted=False)
        if not member:
            raise BusinessRuleViolationError(
                rule_name="workspace_member_not_found",
                rule_detail="workspace member not found",
                message="Workspace member not found",
            )

        member = self._workspace_member_repo._update(session, record_id=member.id, role_id=role_id)
        return member.to_dict()

    # ========================================================================================= INVITATION METHODS =====

    @with_transaction(manager=None)
    def create_invitation(
        self,
        session,
        *,
        workspace_id: str,
        invited_by: str,
        user_id: str,
        role_id: str,
        message: Optional[str] = None,
    ):
        workspace = self._validate_workspace(session, workspace_id)
        self._validate_user(session, invited_by, "inviter_not_found")
        self._validate_role(session, role_id)
        self._check_member_limit(workspace)
        invitee_user = self._validate_user(session, user_id)
        self._check_existing_member(session, workspace_id, user_id)

        existing_invitation = self._workspace_invitation_repo._get_by_workspace_id_and_user_id(
            session, workspace_id=workspace_id, user_id=user_id, include_deleted=False
        )
        if existing_invitation and existing_invitation.is_pending:
            raise BusinessRuleViolationError(
                rule_name="invitation_already_exists",
                rule_detail="invitation already exists",
                message="A pending invitation already exists for this user",
            )

        invitation = self._workspace_invitation_repo._create(
            session,
            workspace_id=workspace_id,
            invited_by=invited_by,
            invitee_id=user_id,
            email=invitee_user.email,
            role_id=role_id,
            status=InvitationStatus.PENDING,
            message=message,
        )

        return invitation.to_dict()

    @with_transaction(manager=None)
    def accept_invitation(
        self,
        session,
        *,
        invitation_id: str,
        user_id: str,
    ):
        invitation = self._workspace_invitation_repo._get_by_id(session, record_id=invitation_id, include_deleted=False)
        if not invitation:
            raise BusinessRuleViolationError(
                rule_name="invitation_not_found",
                rule_detail="invitation not found",
                message="Invitation not found",
            )

        if invitation.status != InvitationStatus.PENDING:
            raise BusinessRuleViolationError(
                rule_name="invitation_already_processed",
                rule_detail="invitation already processed",
                message=f"Invitation has already been {invitation.status.value.lower()}",
            )

        user = self._user_repo._get_by_id(session, record_id=user_id, include_deleted=False)
        if not user:
            raise BusinessRuleViolationError(
                rule_name="user_not_found",
                rule_detail="user not found",
                message="User not found",
            )

        if invitation.invitee_id != user_id:
            raise BusinessRuleViolationError(
                rule_name="user_mismatch",
                rule_detail="user mismatch",
                message="This invitation is for a different user",
            )

        workspace = self._validate_workspace(session, invitation.workspace_id)
        invitation.accept_invitation()
        session.add(invitation)

        member = self._create_member(
            session,
            workspace_id=invitation.workspace_id,
            user_id=user_id,
            role_id=invitation.role_id,
            invited_by=invitation.invited_by,
            workspace=workspace,
        )

        return member.to_dict()

    @with_transaction(manager=None)
    def decline_invitation(
        self,
        session,
        *,
        invitation_id: str,
        user_id: str,
    ):
        invitation = self._workspace_invitation_repo._get_by_id(session, record_id=invitation_id, include_deleted=False)
        if not invitation:
            raise BusinessRuleViolationError(
                rule_name="invitation_not_found",
                rule_detail="invitation not found",
                message="Invitation not found",
            )

        if invitation.invitee_id != user_id:
            raise BusinessRuleViolationError(
                rule_name="unauthorized",
                rule_detail="unauthorized",
                message="You can only decline your own invitations",
            )

        if invitation.status != InvitationStatus.PENDING:
            raise BusinessRuleViolationError(
                rule_name="invitation_already_processed",
                rule_detail="invitation already processed",
                message=f"Invitation has already been {invitation.status.value.lower()}",
            )

        invitation.decline_invitation()
        session.add(invitation)

        return True

    @with_transaction(manager=None)
    def cancel_invitation(
        self,
        session,
        *,
        invitation_id: str,
        cancelled_by: str,
    ):
        invitation = self._workspace_invitation_repo._get_by_id(session, record_id=invitation_id, include_deleted=False)
        if not invitation:
            raise BusinessRuleViolationError(
                rule_name="invitation_not_found",
                rule_detail="invitation not found",
                message="Invitation not found",
            )

        if invitation.invited_by != cancelled_by:
            raise BusinessRuleViolationError(
                rule_name="unauthorized",
                rule_detail="unauthorized",
                message="Only the inviter can cancel the invitation",
            )

        if invitation.status != InvitationStatus.PENDING:
            raise BusinessRuleViolationError(
                rule_name="invitation_already_processed",
                rule_detail="invitation already processed",
                message=f"Invitation has already been {invitation.status.value.lower()}",
            )

        invitation.cancel_invitation()
        session.add(invitation)

        return True

    @with_readonly_session(manager=None)
    def get_workspace_invitations(
        self,
        session,
        *,
        workspace_id: str,
        status: Optional[InvitationStatus] = None,
    ):
        self._validate_workspace(session, workspace_id)

        invitations = self._workspace_invitation_repo._get_all(session, workspace_id=workspace_id, include_deleted=False)
        
        if status:
            invitations = [inv for inv in invitations if inv.status == status]

        return [invitation.to_dict() for invitation in invitations]

    @with_readonly_session(manager=None)
    def get_user_pending_invitations(
        self,
        session,
        *,
        user_id: str,
    ):
        self._validate_user(session, user_id)

        invitations = self._workspace_invitation_repo._get_pending_by_user_id(session, user_id=user_id, include_deleted=False)
        
        result = []
        for invitation in invitations:
            inv_dict = invitation.to_dict()
            if invitation.workspace:
                inv_dict["workspace_name"] = invitation.workspace.name
                inv_dict["workspace_slug"] = invitation.workspace.slug
            if invitation.inviter:
                inv_dict["inviter_name"] = invitation.inviter.name
                inv_dict["inviter_email"] = invitation.inviter.email
            if invitation.role:
                inv_dict["role_name"] = invitation.role.name
            result.append(inv_dict)
        
        return result

