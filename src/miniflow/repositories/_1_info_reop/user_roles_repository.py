from typing import Optional, Dict, List, Union
from sqlalchemy.orm import Session
from sqlalchemy import select

from ..base_repository import BaseRepository
from miniflow.models import UserRoles


class UserRolesRepository(BaseRepository[UserRoles]):
    def __init__(self):
        super().__init__(UserRoles)

    @BaseRepository._handle_db_exceptions
    def _get_by_name(self, session: Session, *, name: str) -> Optional[UserRoles]:
        query = select(UserRoles).where(self.model.name == name)
        query = self._apply_soft_delete_filter(query, include_deleted=False)
        return session.execute(query).scalar_one_or_none()
    
    @BaseRepository._handle_db_exceptions
    def _has_permission(self, session: Session, *,  role_id: str, permission_field: str) -> bool:
        if not role_id:
            return False
        
        query = select(UserRoles).where(UserRoles.id == role_id)
        query = self._apply_soft_delete_filter(query, include_deleted=False)
        role = session.execute(query).scalar_one_or_none()
        
        if not role:
            return False

        if not hasattr(role, permission_field):
            return False

        return getattr(role, permission_field, False)
    

    def can_view_workspace(self, session, *, role_id: str) -> bool:
        return self._has_permission(session, role_id=role_id, permission_field="can_view_workspace")
    
    def can_edit_workspace(self, session, *, role_id: str) -> bool:
        return self._has_permission(session, role_id=role_id, permission_field="can_edit_workspace")
    
    def can_delete_workspace(self, session, *, role_id: str) -> bool:
        return self._has_permission(session, role_id=role_id, permission_field="can_delete_workspace")
    
    def can_invite_members(self, session, *, role_id: str) -> bool:
        return self._has_permission(session, role_id=role_id, permission_field="can_invite_members")
    
    def can_remove_members(self, session, *, role_id: str) -> bool:
        return self._has_permission(session, role_id=role_id, permission_field="can_remove_members")
    
    def can_change_plan(self, session, *, role_id: str) -> bool:
        return self._has_permission(session, role_id=role_id, permission_field="can_change_plan")
    

    def can_view_workflows(self, session, *, role_id: str) -> bool:
        return self._has_permission(session, role_id=role_id, permission_field="can_view_workflows")
    
    def can_create_workflows(self, session, *, role_id: str) -> bool:
        return self._has_permission(session, role_id=role_id, permission_field="can_create_workflows")
    
    def can_edit_workflows(self, session, *, role_id: str) -> bool:
        return self._has_permission(session, role_id=role_id, permission_field="can_edit_workflows")
    
    def can_delete_workflows(self, session, *, role_id: str) -> bool:
        return self._has_permission(session, role_id=role_id, permission_field="can_delete_workflows")
    
    def can_execute_workflows(self, session, *, role_id: str) -> bool:
        return self._has_permission(session, role_id=role_id, permission_field="can_execute_workflows")
    
    def can_share_workflows(self, session, *, role_id: str) -> bool:
        return self._has_permission(session, role_id=role_id, permission_field="can_share_workflows")
    

    def can_view_credentials(self, session, *, role_id: str) -> bool:
        return self._has_permission(session, role_id=role_id, permission_field="can_view_credentials")
    
    def can_create_credentials(self, session, *, role_id: str) -> bool:
        return self._has_permission(session, role_id=role_id, permission_field="can_create_credentials")
    
    def can_edit_credentials(self, session, *, role_id: str) -> bool:
        return self._has_permission(session, role_id=role_id, permission_field="can_edit_credentials")
    
    def can_delete_credentials(self, session, *, role_id: str) -> bool:
        return self._has_permission(session, role_id=role_id, permission_field="can_delete_credentials")
    
    def can_share_credentials(self, session, *, role_id: str) -> bool:
        return self._has_permission(session, role_id=role_id, permission_field="can_share_credentials")
    
    def can_view_credential_values(self, session, *, role_id: str) -> bool:
        return self._has_permission(session, role_id=role_id, permission_field="can_view_credential_values")

    
    def can_view_files(self, session, *, role_id: str) -> bool:
        return self._has_permission(session, role_id=role_id, permission_field="can_view_files")
    
    def can_upload_files(self, session, *, role_id: str) -> bool:
        return self._has_permission(session, role_id=role_id, permission_field="can_upload_files")
    
    def can_download_files(self, session, *, role_id: str) -> bool:
        return self._has_permission(session, role_id=role_id, permission_field="can_download_files")
    
    def can_delete_files(self, session, *, role_id: str) -> bool:
        return self._has_permission(session, role_id=role_id, permission_field="can_delete_files")
    
    def can_share_files(self, session, *, role_id: str) -> bool:
        return self._has_permission(session, role_id=role_id, permission_field="can_share_files")
    

    def can_view_databases(self, session, *, role_id: str) -> bool:
        return self._has_permission(session, role_id=role_id, permission_field="can_view_databases")
    
    def can_create_databases(self, session, *, role_id: str) -> bool:
        return self._has_permission(session, role_id=role_id, permission_field="can_create_databases")
    
    def can_edit_databases(self, session, *, role_id: str) -> bool:
        return self._has_permission(session, role_id=role_id, permission_field="can_edit_databases")
    
    def can_delete_databases(self, session, *, role_id: str) -> bool:
        return self._has_permission(session, role_id=role_id, permission_field="can_delete_databases")
    
    def can_share_databases(self, session, *, role_id: str) -> bool:
        return self._has_permission(session, role_id=role_id, permission_field="can_share_databases")
    
    def can_view_connection_details(self, session, *, role_id: str) -> bool:
        return self._has_permission(session, role_id=role_id, permission_field="can_view_connection_details")
    

    def can_view_variables(self, session, *, role_id: str) -> bool:
        return self._has_permission(session, role_id=role_id, permission_field="can_view_variables")
    
    def can_create_variables(self, session, *, role_id: str) -> bool:
        return self._has_permission(session, role_id=role_id, permission_field="can_create_variables")
    
    def can_edit_variables(self, session, *, role_id: str) -> bool:
        return self._has_permission(session, role_id=role_id, permission_field="can_edit_variables")
    
    def can_delete_variables(self, session, *, role_id: str) -> bool:
        return self._has_permission(session, role_id=role_id, permission_field="can_delete_variables")
    
    def can_share_variables(self, session, *, role_id: str) -> bool:
        return self._has_permission(session, role_id=role_id, permission_field="can_share_variables")
    
    def can_view_variable_values(self, session, *, role_id: str) -> bool:
        return self._has_permission(session, role_id=role_id, permission_field="can_view_variable_values")
    

    def can_create_api_keys(self, session, *, role_id: str) -> bool:
        return self._has_permission(session, role_id=role_id, permission_field="can_create_api_keys")
    
    def can_view_api_keys(self, session, *, role_id: str) -> bool:
        return self._has_permission(session, role_id=role_id, permission_field="can_view_api_keys")
    
    def can_edit_api_keys(self, session, *, role_id: str) -> bool:
        return self._has_permission(session, role_id=role_id, permission_field="can_edit_api_keys")
    
    def can_delete_api_keys(self, session, *, role_id: str) -> bool:
        return self._has_permission(session, role_id=role_id, permission_field="can_delete_api_keys")
    
    def can_share_api_keys(self, session, *, role_id: str) -> bool:
        return self._has_permission(session, role_id=role_id, permission_field="can_share_api_keys")
    
    def can_view_api_key_values(self, session, *, role_id: str) -> bool:
        return self._has_permission(session, role_id=role_id, permission_field="can_view_api_key_values")