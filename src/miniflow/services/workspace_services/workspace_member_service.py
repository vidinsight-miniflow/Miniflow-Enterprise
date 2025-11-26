from typing import Optional, List, Dict, Any
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

    def _check_custom_permission(self, member, permission_name: str) -> Optional[bool]:
        """Custom permission override kontrolü (None = override yok)"""
        if not member.custom_permissions:
            return None
        return member.custom_permissions.get(permission_name)


    @with_readonly_session(manager=None)
    def validate_workspace_member(
        self,
        session,
        *,
        workspace_id,
        user_id
    ) -> bool:

        self._validate_workspace(session, workspace_id)
        self._validate_user(session, user_id)

        if not self._workspace_member_repo._get_by_workspace_id_and_user_id(session, workspace_id=workspace_id, user_id=user_id, include_deleted=False):
            raise BusinessRuleViolationError(
                rule_name="workspace_member_not_found",
                rule_detail="workspace member not found",
                message="Workspace member not found",
            )

        return True

    @with_readonly_session(manager=None)
    def validate_workspace_member_role(
        self,
        session,
        *,
        member_id: str,
        role_id: str
    ) -> bool:
        member = self._workspace_member_repo._get_by_id(session, record_id=member_id, include_deleted=False)
        if not member or member.role_id != role_id:
            raise BusinessRuleViolationError(
                rule_name="workspace_member_role_not_found",
                rule_detail="workspace member role not found",
                message="Workspace member role not found",
            )
        return True

    @with_readonly_session(manager=None)
    def get_user_workspaces(
        self,
        session,
        *,
        user_id: str
    ) -> Dict[str, Any]:
        self._validate_user(session, user_id)

        owned_workspaces = self._workspace_member_repo._get_owned_workspaces_by_user_id(session, user_id=user_id, include_deleted=False)
        memberships = self._workspace_member_repo._get_memberships_by_user_id(session, user_id=user_id, include_deleted=False)

        payload = {
            'owned_workspaces': [],
            'memberships': [],
        }
        for workspace in owned_workspaces:
            self._validate_workspace(session, workspace.workspace_id)
            payload['owned_workspaces'].append({
                'workspace_id': workspace.workspace_id,
                'workspace_name': workspace.workspace.name,
                'workspace_slug': workspace.workspace.slug,
                'user_role': workspace.role_name.upper(),
            })
        for membership in memberships:
            self._validate_workspace(session, membership.workspace_id)
            payload['memberships'].append({
                'workspace_id': membership.workspace_id,
                'workspace_name': membership.workspace.name,
                'workspace_slug': membership.workspace.slug,
                'user_role': membership.role_name.upper(),
            })
        return payload

    @with_readonly_session(manager=None)
    def get_workspace_members(
        self,
        session,
        *,
        workspace_id: str,
    ) -> List[Dict[str, Any]]:
        self._validate_workspace(session, workspace_id)
        members = self._workspace_member_repo._get_all(session, workspace_id=workspace_id, include_deleted=False)
        payload = []
        for member in members:
            self._validate_user(session, member.user_id)
            payload.append({
                'member_id': member.id,
                'user_id': member.user_id,
                'user_name': member.user.name,
                'user_email': member.user.email,
            })
        return payload

    @with_readonly_session(manager=None)
    def get_workspace_member(
        self,
        session,
        *,
        member_id: str,
    ) -> Dict[str, Any]:
        member = self._workspace_member_repo._get_by_id(session, record_id=member_id, include_deleted=False)
        if not member:
            raise BusinessRuleViolationError(
                rule_name="workspace_member_not_found",
                rule_detail="workspace member not found",
                message="Workspace member not found",
            )
        return member.to_dict()

    @with_transaction(manager=None)
    def change_user_role(
        self,
        session,
        *,
        member_id: str,
        role_id: str,
    ):
        member = self._workspace_member_repo._get_by_id(session, record_id=member_id, include_deleted=False)
        if not member:
            raise BusinessRuleViolationError(
                rule_name="workspace_member_not_found",
                rule_detail="workspace member not found",
                message="Workspace member not found",
            )
        role = self._user_roles_repo._get_by_id(session, record_id=role_id, include_deleted=False)
        if not role:
            raise BusinessRuleViolationError(
                rule_name="role_not_found",
                rule_detail="role not found",
                message="Role not found",
            )
        member.role_id = role.id
        member.role_name = role.name
        session.add(member)

        return {
            'member_id': member.id,
            'user_id': member.user_id,
            'user_email': member.user.email,
            'role_id': role.id,
            'role_name': role.name,
        }

    
    @with_transaction(manager=None)
    def delete_user_from_workspace(
        self,
        session,
        *,
        workspace_id: str,
        user_id: str,
    ) -> Dict[str, Any]:
        workspace = self._validate_workspace(session, workspace_id)
        self._validate_user(session, user_id)
        
        if workspace.owner_id == user_id:
            raise BusinessRuleViolationError(
                rule_name="cannot_remove_owner",
                rule_detail="cannot remove owner",
                message="Cannot remove workspace owner. Transfer ownership first or delete the workspace.",
            )
        
        member = self._workspace_member_repo._get_by_workspace_id_and_user_id(
            session, workspace_id=workspace_id, user_id=user_id, include_deleted=False
        )
        if not member:
            raise BusinessRuleViolationError(
                rule_name="workspace_member_not_found",
                rule_detail="workspace member not found",
                message="User is not a member of this workspace",
            )
        
        member_id = member.id
        self._workspace_member_repo._delete(session, record_id=member.id)
        
        if workspace.current_member_count > 0:
            workspace.current_member_count -= 1
        session.add(workspace)
        
        return {
            'member_id': member_id,
            'workspace_id': workspace_id,
            'user_id': user_id,
            'deleted': True,
        }