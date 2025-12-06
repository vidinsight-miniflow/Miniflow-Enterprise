from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

from miniflow.database import RepositoryRegistry, with_transaction, with_readonly_session
from miniflow.core.exceptions import (
    ResourceNotFoundError,
    BusinessRuleViolationError,
)


class WorkspaceMemberService:
    """
    Workspace üye yönetim servisi.
    
    Üye listeleme, rol değiştirme ve üye çıkarma işlemlerini yönetir.
    NOT: workspace_exists ve user_exists kontrolleri middleware'de yapılır.
    """
    _registry = RepositoryRegistry()
    _workspace_repo = _registry.workspace_repository()
    _workspace_member_repo = _registry.workspace_member_repository()
    _user_roles_repo = _registry.user_roles_repository()
    _user_repo = _registry.user_repository()

    # ==================================================================================== VALIDATE ==
    @classmethod
    @with_readonly_session(manager=None)
    def validate_workspace_member(
        cls,
        session,
        *,
        workspace_id: str,
        user_id: str,
    ) -> bool:
        """
        Kullanıcının workspace üyesi olup olmadığını doğrular.
        
        Args:
            workspace_id: Workspace ID'si
            user_id: Kullanıcı ID'si
            
        Returns:
            True (üye ise)
            
        Raises:
            BusinessRuleViolationError: Kullanıcı üye değil
        """
        member = cls._workspace_member_repo._get_by_workspace_id_and_user_id(
            session, 
            workspace_id=workspace_id, 
            user_id=user_id
        )
        
        if not member:
            raise BusinessRuleViolationError(
                rule_name="not_workspace_member",
                message="User is not a member of this workspace"
            )
        
        return True

    @classmethod
    @with_readonly_session(manager=None)
    def validate_member_role(
        cls,
        session,
        *,
        member_id: str,
        required_roles: List[str],
    ) -> bool:
        """
        Üyenin belirtilen rollerden birine sahip olup olmadığını doğrular.
        
        Args:
            member_id: Üye ID'si
            required_roles: Gerekli rol adları listesi (örn: ["Owner", "Admin"])
            
        Returns:
            True (rol uygunsa)
            
        Raises:
            BusinessRuleViolationError: Yetersiz yetki
        """
        member = cls._workspace_member_repo._get_by_id(session, record_id=member_id)
        
        if not member:
            raise ResourceNotFoundError(
                resource_name="WorkspaceMember",
                resource_id=member_id
            )
        
        if member.role_name not in required_roles:
            raise BusinessRuleViolationError(
                rule_name="insufficient_permissions",
                message=f"Requires one of these roles: {', '.join(required_roles)}"
            )
        
        return True

    # ==================================================================================== LIST ==
    @classmethod
    @with_readonly_session(manager=None)
    def get_workspace_members(
        cls,
        session,
        *,
        workspace_id: str,
    ) -> Dict[str, Any]:
        """
        Workspace üyelerini listeler.
        
        Args:
            workspace_id: Workspace ID'si
            
        Returns:
            {
                "workspace_id": str,
                "members": List[Dict],
                "total_count": int
            }
        """
        members = cls._workspace_member_repo._get_all_by_workspace_id(session, workspace_id=workspace_id)
        
        member_list = []
        for member in members:
            member_list.append({
                "id": member.id,
                "user_id": member.user_id,
                "user_name": member.user.name if member.user else None,
                "user_email": member.user.email if member.user else None,
                "role_id": member.role_id,
                "role_name": member.role_name,
                "joined_at": member.joined_at.isoformat() if member.joined_at else None,
                "last_accessed_at": member.last_accessed_at.isoformat() if member.last_accessed_at else None
            })
        
        return {
            "workspace_id": workspace_id,
            "members": member_list,
            "total_count": len(member_list)
        }

    @classmethod
    @with_readonly_session(manager=None)
    def get_member_details(
        cls,
        session,
        *,
        member_id: str,
    ) -> Dict[str, Any]:
        """
        Üye detaylarını getirir.
        
        Args:
            member_id: Üye ID'si
            
        Returns:
            Üye detayları
        """
        member = cls._workspace_member_repo._get_by_id(session, record_id=member_id)
        
        if not member:
            raise ResourceNotFoundError(
                resource_name="WorkspaceMember",
                resource_id=member_id
            )
        
        return {
            "id": member.id,
            "workspace_id": member.workspace_id,
            "user_id": member.user_id,
            "user_name": member.user.name if member.user else None,
            "user_email": member.user.email if member.user else None,
            "role_id": member.role_id,
            "role_name": member.role_name,
            "invited_by": member.invited_by,
            "joined_at": member.joined_at.isoformat() if member.joined_at else None,
            "last_accessed_at": member.last_accessed_at.isoformat() if member.last_accessed_at else None,
            "custom_permissions": member.custom_permissions
        }

    @classmethod
    @with_readonly_session(manager=None)
    def get_user_workspaces(
        cls,
        session,
        *,
        user_id: str,
    ) -> Dict[str, Any]:
        """
        Kullanıcının üyesi olduğu tüm workspace'leri getirir.
        
        Args:
            user_id: Kullanıcı ID'si
            
        Returns:
            {
                "owned_workspaces": List[Dict],
                "memberships": List[Dict]
            }
        """
        owned = cls._workspace_member_repo._get_owned_workspaces_by_user_id(session, user_id=user_id)
        memberships = cls._workspace_member_repo._get_memberships_by_user_id(session, user_id=user_id)
        
        owned_list = []
        for member in owned:
            if member.workspace:
                owned_list.append({
                    "workspace_id": member.workspace_id,
                    "workspace_name": member.workspace.name,
                    "workspace_slug": member.workspace.slug,
                    "role": member.role_name
                })
        
        membership_list = []
        for member in memberships:
            if member.workspace:
                membership_list.append({
                    "workspace_id": member.workspace_id,
                    "workspace_name": member.workspace.name,
                    "workspace_slug": member.workspace.slug,
                    "role": member.role_name
                })
        
        return {
            "owned_workspaces": owned_list,
            "memberships": membership_list
        }

    # ==================================================================================== UPDATE ROLE ==
    @classmethod
    @with_transaction(manager=None)
    def change_member_role(
        cls,
        session,
        *,
        member_id: str,
        new_role_id: str,
    ) -> Dict[str, Any]:
        """
        Üyenin rolünü değiştirir.
        
        NOT: Owner rolü değiştirilemez, bunun için transfer_ownership kullanılmalı.
        
        Args:
            member_id: Üye ID'si
            new_role_id: Yeni rol ID'si
            
        Returns:
            Güncellenmiş üye bilgileri
            
        Raises:
            BusinessRuleViolationError: Owner rolü değiştirilemez
        """
        member = cls._workspace_member_repo._get_by_id(session, record_id=member_id)
        
        if not member:
            raise ResourceNotFoundError(
                resource_name="WorkspaceMember",
                resource_id=member_id
            )
        
        # Owner rolü değiştirilemez
        if member.role_name.lower() == "owner":
            raise BusinessRuleViolationError(
                rule_name="cannot_change_owner_role",
                message="Cannot change owner role. Use transfer ownership instead."
            )
        
        # Yeni rolü al
        new_role = cls._user_roles_repo._get_by_id(session, record_id=new_role_id)
        if not new_role:
            raise ResourceNotFoundError(
                resource_name="UserRole",
                resource_id=new_role_id
            )
        
        # Owner rolüne atama yapılamaz (bu sadece transfer ile olur)
        if new_role.name.lower() == "owner":
            raise BusinessRuleViolationError(
                rule_name="cannot_assign_owner_role",
                message="Cannot assign owner role directly. Use transfer ownership instead."
            )
        
        cls._workspace_member_repo._update_role(
            session,
            member_id=member_id,
            role_id=new_role.id,
            role_name=new_role.name
        )
        
        return {
            "id": member_id,
            "user_id": member.user_id,
            "role_id": new_role.id,
            "role_name": new_role.name
        }

    # ==================================================================================== REMOVE ==
    @classmethod
    @with_transaction(manager=None)
    def remove_member(
        cls,
        session,
        *,
        workspace_id: str,
        user_id: str,
    ) -> Dict[str, Any]:
        """
        Üyeyi workspace'den çıkarır.
        
        NOT: Owner kendini çıkaramaz, önce ownership transfer edilmeli.
        
        Args:
            workspace_id: Workspace ID'si
            user_id: Çıkarılacak kullanıcı ID'si
            
        Returns:
            {"success": True}
            
        Raises:
            BusinessRuleViolationError: Owner çıkarılamaz
        """
        workspace = cls._workspace_repo._get_by_id(session, record_id=workspace_id)
        if not workspace:
            raise ResourceNotFoundError(
                resource_name="Workspace",
                resource_id=workspace_id
            )
        
        # Owner kendini çıkaramaz
        if workspace.owner_id == user_id:
            raise BusinessRuleViolationError(
                rule_name="cannot_remove_owner",
                message="Cannot remove workspace owner. Transfer ownership first or delete the workspace."
            )
        
        member = cls._workspace_member_repo._get_by_workspace_id_and_user_id(
            session, 
            workspace_id=workspace_id, 
            user_id=user_id
        )
        
        if not member:
            raise BusinessRuleViolationError(
                rule_name="not_workspace_member",
                message="User is not a member of this workspace"
            )
        
        # Üyeyi sil
        cls._workspace_member_repo._delete(session, record_id=member.id)
        
        # Üye sayısını azalt
        cls._workspace_repo._decrement_member_count(session, workspace_id=workspace_id)
        
        return {
            "success": True,
            "workspace_id": workspace_id,
            "removed_user_id": user_id
        }

    @classmethod
    @with_transaction(manager=None)
    def leave_workspace(
        cls,
        session,
        *,
        workspace_id: str,
        user_id: str,
    ) -> Dict[str, Any]:
        """
        Kullanıcı workspace'den ayrılır.
        
        NOT: Owner ayrılamaz, önce ownership transfer edilmeli.
        
        Args:
            workspace_id: Workspace ID'si
            user_id: Ayrılan kullanıcı ID'si
            
        Returns:
            {"success": True}
        """
        # remove_member ile aynı mantık
        return cls.remove_member(session, workspace_id=workspace_id, user_id=user_id)

    # ==================================================================================== CUSTOM PERMISSIONS ==
    @classmethod
    @with_transaction(manager=None)
    def set_custom_permissions(
        cls,
        session,
        *,
        member_id: str,
        custom_permissions: Dict[str, bool],
    ) -> Dict[str, Any]:
        """
        Üyeye özel izinler atar (rol bazlı izinleri override eder).
        
        Args:
            member_id: Üye ID'si
            custom_permissions: Özel izinler dict'i (örn: {"can_delete_workflows": false})
            
        Returns:
            Güncellenmiş izinler
        """
        member = cls._workspace_member_repo._get_by_id(session, record_id=member_id)
        
        if not member:
            raise ResourceNotFoundError(
                resource_name="WorkspaceMember",
                resource_id=member_id
            )
        
        cls._workspace_member_repo._update(
            session,
            record_id=member_id,
            custom_permissions=custom_permissions
        )
        
        return {
            "id": member_id,
            "custom_permissions": custom_permissions
        }

    @classmethod
    @with_transaction(manager=None)
    def clear_custom_permissions(
        cls,
        session,
        *,
        member_id: str,
    ) -> Dict[str, Any]:
        """
        Üyenin özel izinlerini temizler (rol bazlı izinlere döner).
        
        Args:
            member_id: Üye ID'si
            
        Returns:
            {"success": True}
        """
        member = cls._workspace_member_repo._get_by_id(session, record_id=member_id)
        
        if not member:
            raise ResourceNotFoundError(
                resource_name="WorkspaceMember",
                resource_id=member_id
            )
        
        cls._workspace_member_repo._update(
            session,
            record_id=member_id,
            custom_permissions=None
        )
        
        return {"success": True}

    # ==================================================================================== ACCESS TRACKING ==
    @classmethod
    @with_transaction(manager=None)
    def update_last_accessed(
        cls,
        session,
        *,
        workspace_id: str,
        user_id: str,
    ) -> None:
        """
        Üyenin son erişim zamanını günceller.
        
        Args:
            workspace_id: Workspace ID'si
            user_id: Kullanıcı ID'si
        """
        member = cls._workspace_member_repo._get_by_workspace_id_and_user_id(
            session, 
            workspace_id=workspace_id, 
            user_id=user_id
        )
        
        if member:
            cls._workspace_member_repo._update_last_accessed(session, member_id=member.id)

