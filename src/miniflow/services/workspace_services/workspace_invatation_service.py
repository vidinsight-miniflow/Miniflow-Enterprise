from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from src.miniflow.database import with_transaction, with_readonly_session
from src.miniflow.database import RepositoryRegistry

from src.miniflow.core.exceptions import BusinessRuleViolationError
from src.miniflow.database.models.enums import InvitationStatus


class WorkspaceInvatationService:

    def __init__(self):
        self._registry: RepositoryRegistry = RepositoryRegistry()

        self._workspace_member_repo = self._registry.workspace_member_repository
        self._workspace_repo = self._registry.workspace_repository
        self._workspace_invitation_repo = self._registry.workspace_invitation_repository
        self._user_repo = self._registry.user_repository
        self._user_roles_repo = self._registry.user_roles_repository

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
    
    @with_readonly_session(manager=None)
    def get_user_pending_invitations(
        self,
        session,
        *,
        user_id: str,
    ) -> Dict[str, Any]:
        self._validate_user(session, user_id)
        
        invitations = self._workspace_invitation_repo._get_pending_by_user_id(
            session, user_id=user_id, include_deleted=False
        )
        
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
        
        return {
            'user_id': user_id,
            'pending_invitations': result,
            'count': len(result)
        }
    
    @with_readonly_session(manager=None)
    def get_workspace_invitations(
        self,
        session,
        *,
        workspace_id: str,
    ) -> List[Dict[str, Any]]:
        self._validate_workspace(session, workspace_id)
        
        invitations = self._workspace_invitation_repo._get_all(
            session, workspace_id=workspace_id, include_deleted=False
        )
        
        result = []
        for invitation in invitations:
            inv_dict = invitation.to_dict()
            if invitation.inviter:
                inv_dict["inviter_name"] = invitation.inviter.name
                inv_dict["inviter_email"] = invitation.inviter.email
            if invitation.invitee:
                inv_dict["invitee_name"] = invitation.invitee.name
                inv_dict["invitee_email"] = invitation.invitee.email
            if invitation.role:
                inv_dict["role_name"] = invitation.role.name
            result.append(inv_dict)
        
        return result

    @with_transaction(manager=None)
    def invite_user_to_workspace(
        self,
        session,
        *,
        workspace_id: str,
        invited_by: str,
        user_id: str,
        role_id: str,
        message: Optional[str] = None,
    ) -> Dict[str, Any]:
        workspace = self._validate_workspace(session, workspace_id)
        self._validate_user(session, invited_by, "inviter_not_found")
        invitee_user = self._validate_user(session, user_id)
        role = self._validate_role(session, role_id)

        if workspace.current_member_count >= workspace.member_limit:
            raise BusinessRuleViolationError(
                rule_name="workspace_member_limit_reached",
                rule_detail="workspace member limit reached",
                message="Workspace member limit reached",
            )

        existing_member = self._workspace_member_repo._get_by_workspace_id_and_user_id(
            session, workspace_id=workspace_id, user_id=user_id, include_deleted=False
        )
        if existing_member:
            raise BusinessRuleViolationError(
                rule_name="user_already_member",
                rule_detail="user already member",
                message="User is already a member of this workspace",
            )

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
            message=message if message else "New Invitation",
        )

        return {
            'invitation_id': invitation.id,
            'workspace_id': invitation.workspace_id,
            'invited_by': invitation.invited_by,
            'invitee_id': invitation.invitee_id,
            'email': invitation.email,
            'role_id': invitation.role_id,
            'status': invitation.status,
        }
    

    @with_transaction(manager=None)
    def decline_invitation(
        self,
        session,
        *,
        invitation_id: str,
        user_id: str,
    ) -> Dict[str, Any]:
        invitation = self._workspace_invitation_repo._get_by_id(
            session, record_id=invitation_id, include_deleted=False
        )
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
        
        return {
            'invitation_id': invitation.id,
            'status': invitation.status.value,
            'declined_at': invitation.declined_at.isoformat() if invitation.declined_at else None,
        }

    @with_transaction(manager=None)
    def cancel_invitation(
        self,
        session,
        *,
        invitation_id: str,
        cancelled_by: str,
    ) -> Dict[str, Any]:
        invitation = self._workspace_invitation_repo._get_by_id(
            session, record_id=invitation_id, include_deleted=False
        )
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
        
        return {
            'invitation_id': invitation.id,
            'status': invitation.status.value,
        }

    @with_transaction(manager=None)
    def accept_invitation(
        self,
        session,
        *,
        invitation_id: str,
        accepted_by: str,
    ) -> Dict[str, Any]:
        invitation = self._workspace_invitation_repo._get_by_id(
            session, record_id=invitation_id, include_deleted=False
        )
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
        
        if invitation.invitee_id != accepted_by:
            raise BusinessRuleViolationError(
                rule_name="user_mismatch",
                rule_detail="user mismatch",
                message="This invitation is for a different user",
            )
        
        workspace = self._validate_workspace(session, invitation.workspace_id)
        
        if workspace.current_member_count >= workspace.member_limit:
            raise BusinessRuleViolationError(
                rule_name="workspace_member_limit_reached",
                rule_detail="workspace member limit reached",
                message="Workspace member limit reached",
            )
        
        existing_member = self._workspace_member_repo._get_by_workspace_id_and_user_id(
            session, workspace_id=invitation.workspace_id, user_id=accepted_by, include_deleted=False
        )
        if existing_member:
            raise BusinessRuleViolationError(
                rule_name="user_already_member",
                rule_detail="user already member",
                message="User is already a member of this workspace",
            )
        
        invitation.accept_invitation()
        session.add(invitation)
        
        member = self._workspace_member_repo._create(
            session,
            workspace_id=invitation.workspace_id,
            user_id=accepted_by,
            role_id=invitation.role_id,
            invited_by=invitation.invited_by,
            joined_at=datetime.now(timezone.utc),
            last_accessed_at=datetime.now(timezone.utc),
            custom_permissions=None,
        )
        
        workspace.current_member_count += 1
        session.add(workspace)
        
        return {
            'invitation_id': invitation.id,
            'member_id': member.id,
            'workspace_id': member.workspace_id,
            'user_id': member.user_id,
            'role_id': member.role_id,
            'status': invitation.status.value,
            'accepted_at': invitation.accepted_at.isoformat() if invitation.accepted_at else None,
        }