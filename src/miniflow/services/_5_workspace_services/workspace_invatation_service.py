from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

from miniflow.database import RepositoryRegistry, with_transaction, with_readonly_session
from miniflow.models.enums import InvitationStatus
from miniflow.core.exceptions import (
    ResourceNotFoundError,
    BusinessRuleViolationError,
)


class WorkspaceInvitationService:
    """
    Workspace davet yönetim servisi.
    
    Davet gönderme, kabul, reddetme ve iptal işlemlerini yönetir.
    NOT: workspace_exists ve user_exists kontrolleri middleware'de yapılır.
    """
    _registry = RepositoryRegistry()
    _workspace_repo = _registry.workspace_repository()
    _workspace_member_repo = _registry.workspace_member_repository()
    _workspace_invitation_repo = _registry.workspace_invitation_repository()
    _user_roles_repo = _registry.user_roles_repository()
    _user_repo = _registry.user_repository()

    # ==================================================================================== LIST ==
    @classmethod
    @with_readonly_session(manager=None)
    def get_user_pending_invitations(
        cls,
        session,
        *,
        user_id: str,
    ) -> Dict[str, Any]:
        """
        Kullanıcının bekleyen davetlerini listeler.
        
        Args:
            user_id: Kullanıcı ID'si
            
        Returns:
            {
                "user_id": str,
                "pending_invitations": List[Dict],
                "count": int
            }
        """
        invitations = cls._workspace_invitation_repo._get_pending_by_user_id(session, user_id=user_id)
        
        invitation_list = []
        for inv in invitations:
            invitation_list.append({
                "id": inv.id,
                "workspace_id": inv.workspace_id,
                "workspace_name": inv.workspace.name if inv.workspace else None,
                "workspace_slug": inv.workspace.slug if inv.workspace else None,
                "invited_by": inv.invited_by,
                "inviter_name": inv.inviter.name if inv.inviter else None,
                "inviter_email": inv.inviter.email if inv.inviter else None,
                "role_id": inv.role_id,
                "role_name": inv.role.name if inv.role else None,
                "message": inv.message,
                "created_at": inv.created_at.isoformat() if inv.created_at else None
            })
        
        return {
            "user_id": user_id,
            "pending_invitations": invitation_list,
            "count": len(invitation_list)
        }

    @classmethod
    @with_readonly_session(manager=None)
    def get_workspace_invitations(
        cls,
        session,
        *,
        workspace_id: str,
        status_filter: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Workspace'in davetlerini listeler.
        
        Args:
            workspace_id: Workspace ID'si
            status_filter: Durum filtresi (PENDING, ACCEPTED, DECLINED, CANCELLED)
            
        Returns:
            {
                "workspace_id": str,
                "invitations": List[Dict],
                "count": int
            }
        """
        if status_filter and status_filter.upper() == "PENDING":
            invitations = cls._workspace_invitation_repo._get_pending_by_workspace_id(
                session, 
                workspace_id=workspace_id
            )
        else:
            invitations = cls._workspace_invitation_repo._get_all_by_workspace_id(
                session, 
                workspace_id=workspace_id
            )
        
        invitation_list = []
        for inv in invitations:
            if status_filter and inv.status.value.upper() != status_filter.upper():
                continue
            
            invitation_list.append({
                "id": inv.id,
                "invitee_id": inv.invitee_id,
                "invitee_name": inv.invitee.name if inv.invitee else None,
                "invitee_email": inv.invitee.email if inv.invitee else inv.email,
                "invited_by": inv.invited_by,
                "inviter_name": inv.inviter.name if inv.inviter else None,
                "role_id": inv.role_id,
                "role_name": inv.role.name if inv.role else None,
                "status": inv.status.value,
                "message": inv.message,
                "created_at": inv.created_at.isoformat() if inv.created_at else None,
                "accepted_at": inv.accepted_at.isoformat() if inv.accepted_at else None,
                "declined_at": inv.declined_at.isoformat() if inv.declined_at else None
            })
        
        return {
            "workspace_id": workspace_id,
            "invitations": invitation_list,
            "count": len(invitation_list)
        }

    # ==================================================================================== CREATE ==
    @classmethod
    @with_transaction(manager=None)
    def invite_user(
        cls,
        session,
        *,
        workspace_id: str,
        invited_by: str,
        invitee_id: str,
        role_id: str,
        message: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Kullanıcıyı workspace'e davet eder.
        
        Args:
            workspace_id: Workspace ID'si
            invited_by: Daveti gönderen kullanıcı ID'si
            invitee_id: Davet edilen kullanıcı ID'si
            role_id: Atanacak rol ID'si
            message: Davet mesajı (opsiyonel)
            
        Returns:
            Oluşturulan davet bilgileri
            
        Raises:
            BusinessRuleViolationError: Üye limiti aşıldı, zaten üye, zaten davetli
        """
        workspace = cls._workspace_repo._get_by_id(session, record_id=workspace_id)
        if not workspace:
            raise ResourceNotFoundError(
                resource_name="Workspace",
                resource_id=workspace_id
            )
        
        # Üye limiti kontrolü
        if workspace.current_member_count >= workspace.member_limit:
            raise BusinessRuleViolationError(
                rule_name="member_limit_reached",
                rule_detail=f"Workspace {workspace_id} has {workspace.current_member_count} members, limit is {workspace.member_limit}",
                message="Workspace member limit reached. Upgrade your plan to invite more members."
            )
        
        # Davet edilen kullanıcıyı al
        invitee = cls._user_repo._get_by_id(session, record_id=invitee_id)
        if not invitee:
            raise ResourceNotFoundError(
                resource_name="User",
                resource_id=invitee_id
            )
        
        # Rolü al
        role = cls._user_roles_repo._get_by_id(session, record_id=role_id)
        if not role:
            raise ResourceNotFoundError(
                resource_name="UserRole",
                resource_id=role_id
            )
        
        # Owner rolüne davet edilemez
        if role.name.lower() == "owner":
            raise BusinessRuleViolationError(
                rule_name="cannot_invite_as_owner",
                rule_detail=f"Cannot invite user {invitee_id} as owner role in workspace {workspace_id}",
                message="Cannot invite user as owner. Use transfer ownership instead."
            )
        
        # Zaten üye mi?
        existing_member = cls._workspace_member_repo._get_by_workspace_id_and_user_id(
            session, 
            workspace_id=workspace_id, 
            user_id=invitee_id
        )
        if existing_member:
            raise BusinessRuleViolationError(
                rule_name="already_member",
                rule_detail=f"User {invitee_id} is already a member of workspace {workspace_id}",
                message="User is already a member of this workspace"
            )
        
        # Zaten bekleyen davet var mı?
        existing_invitation = cls._workspace_invitation_repo._get_by_workspace_id_and_user_id(
            session, 
            workspace_id=workspace_id, 
            user_id=invitee_id
        )
        if existing_invitation and existing_invitation.is_pending:
            raise BusinessRuleViolationError(
                rule_name="invitation_exists",
                message="A pending invitation already exists for this user"
            )
        
        # Eski daveti sil (varsa ve pending değilse)
        if existing_invitation:
            cls._workspace_invitation_repo._delete(session, record_id=existing_invitation.id)
        
        # Davet oluştur
        invitation = cls._workspace_invitation_repo._create(
            session,
            workspace_id=workspace_id,
            invited_by=invited_by,
            invitee_id=invitee_id,
            email=invitee.email,
            role_id=role_id,
            status=InvitationStatus.PENDING,
            message=message or "You have been invited to join this workspace",
            created_by=invited_by
        )
        
        return {
            "id": invitation.id,
            "workspace_id": invitation.workspace_id,
            "invitee_id": invitation.invitee_id,
            "invitee_email": invitation.email,
            "role_id": invitation.role_id,
            "status": invitation.status.value,
            "message": invitation.message
        }

    # ==================================================================================== ACCEPT ==
    @classmethod
    @with_transaction(manager=None)
    def accept_invitation(
        cls,
        session,
        *,
        invitation_id: str,
        user_id: str,
    ) -> Dict[str, Any]:
        """
        Daveti kabul eder ve kullanıcıyı workspace'e üye olarak ekler.
        
        Args:
            invitation_id: Davet ID'si
            user_id: Kabul eden kullanıcı ID'si (güvenlik için)
            
        Returns:
            {
                "invitation_id": str,
                "member_id": str,
                "workspace_id": str,
                "status": "ACCEPTED"
            }
            
        Raises:
            BusinessRuleViolationError: Davet başka kullanıcıya ait, zaten işlenmiş, üye limiti
        """
        invitation = cls._workspace_invitation_repo._get_by_id(session, record_id=invitation_id)
        
        if not invitation:
            raise ResourceNotFoundError(
                resource_name="WorkspaceInvitation",
                resource_id=invitation_id
            )
        
        # Kullanıcı eşleşmesi
        if invitation.invitee_id != user_id:
            raise BusinessRuleViolationError(
                rule_name="invitation_not_yours",
                message="This invitation is for a different user"
            )
        
        # Davet durumu kontrolü
        if invitation.status != InvitationStatus.PENDING:
            raise BusinessRuleViolationError(
                rule_name="invitation_not_pending",
                message=f"Invitation has already been {invitation.status.value.lower()}"
            )
        
        # Workspace kontrolü
        workspace = cls._workspace_repo._get_by_id(session, record_id=invitation.workspace_id)
        if not workspace:
            raise ResourceNotFoundError(
                resource_name="Workspace",
                resource_id=invitation.workspace_id
            )
        
        # Üye limiti kontrolü
        if workspace.current_member_count >= workspace.member_limit:
            raise BusinessRuleViolationError(
                rule_name="member_limit_reached",
                message="Workspace member limit reached"
            )
        
        # Zaten üye mi kontrolü (edge case)
        existing_member = cls._workspace_member_repo._get_by_workspace_id_and_user_id(
            session, 
            workspace_id=invitation.workspace_id, 
            user_id=user_id
        )
        if existing_member:
            # Daveti reddet ve hata dön
            invitation.status = InvitationStatus.CANCELLED
            raise BusinessRuleViolationError(
                rule_name="already_member",
                message="You are already a member of this workspace"
            )
        
        # Rolü al
        role = cls._user_roles_repo._get_by_id(session, record_id=invitation.role_id)
        if not role:
            raise ResourceNotFoundError(
                resource_name="UserRole",
                resource_id=invitation.role_id
            )
        
        # Daveti kabul et
        invitation.accept_invitation()
        
        # Üye olarak ekle
        member = cls._workspace_member_repo._create(
            session,
            workspace_id=invitation.workspace_id,
            user_id=user_id,
            role_id=invitation.role_id,
            role_name=role.name,
            invited_by=invitation.invited_by,
            joined_at=datetime.now(timezone.utc),
            last_accessed_at=datetime.now(timezone.utc),
            custom_permissions=None,
            created_by=user_id
        )
        
        # Üye sayısını artır
        cls._workspace_repo._increment_member_count(session, workspace_id=invitation.workspace_id)
        
        return {
            "invitation_id": invitation.id,
            "member_id": member.id,
            "workspace_id": invitation.workspace_id,
            "status": invitation.status.value,
            "accepted_at": invitation.accepted_at.isoformat() if invitation.accepted_at else None
        }

    # ==================================================================================== DECLINE ==
    @classmethod
    @with_transaction(manager=None)
    def decline_invitation(
        cls,
        session,
        *,
        invitation_id: str,
        user_id: str,
    ) -> Dict[str, Any]:
        """
        Daveti reddeder.
        
        Args:
            invitation_id: Davet ID'si
            user_id: Reddeden kullanıcı ID'si (güvenlik için)
            
        Returns:
            {"id": str, "status": "DECLINED", "declined_at": str}
        """
        invitation = cls._workspace_invitation_repo._get_by_id(session, record_id=invitation_id)
        
        if not invitation:
            raise ResourceNotFoundError(
                resource_name="WorkspaceInvitation",
                resource_id=invitation_id
            )
        
        # Kullanıcı eşleşmesi
        if invitation.invitee_id != user_id:
            raise BusinessRuleViolationError(
                rule_name="invitation_not_yours",
                message="You can only decline your own invitations"
            )
        
        # Davet durumu kontrolü
        if invitation.status != InvitationStatus.PENDING:
            raise BusinessRuleViolationError(
                rule_name="invitation_not_pending",
                message=f"Invitation has already been {invitation.status.value.lower()}"
            )
        
        # Daveti reddet
        invitation.decline_invitation()
        
        return {
            "id": invitation.id,
            "status": invitation.status.value,
            "declined_at": invitation.declined_at.isoformat() if invitation.declined_at else None
        }

    # ==================================================================================== CANCEL ==
    @classmethod
    @with_transaction(manager=None)
    def cancel_invitation(
        cls,
        session,
        *,
        invitation_id: str,
        cancelled_by: str,
    ) -> Dict[str, Any]:
        """
        Daveti iptal eder.
        
        Args:
            invitation_id: Davet ID'si
            cancelled_by: İptal eden kullanıcı ID'si (daveti gönderen veya admin)
            
        Returns:
            {"id": str, "status": "CANCELLED"}
        """
        invitation = cls._workspace_invitation_repo._get_by_id(session, record_id=invitation_id)
        
        if not invitation:
            raise ResourceNotFoundError(
                resource_name="WorkspaceInvitation",
                resource_id=invitation_id
            )
        
        # Yetki kontrolü: Daveti gönderen iptal edebilir
        # TODO: Admin kontrolü eklenebilir
        if invitation.invited_by != cancelled_by:
            # Workspace owner veya admin kontrolü
            workspace = cls._workspace_repo._get_by_id(session, record_id=invitation.workspace_id)
            if workspace and workspace.owner_id != cancelled_by:
                raise BusinessRuleViolationError(
                    rule_name="unauthorized",
                    message="Only the inviter or workspace owner can cancel invitations"
                )
        
        # Davet durumu kontrolü
        if invitation.status != InvitationStatus.PENDING:
            raise BusinessRuleViolationError(
                rule_name="invitation_not_pending",
                message=f"Invitation has already been {invitation.status.value.lower()}"
            )
        
        # Daveti iptal et
        invitation.cancel_invitation()
        
        return {
            "id": invitation.id,
            "status": invitation.status.value
        }

    # ==================================================================================== RESEND ==
    @classmethod
    @with_transaction(manager=None)
    def resend_invitation(
        cls,
        session,
        *,
        invitation_id: str,
        resent_by: str,
    ) -> Dict[str, Any]:
        """
        Bekleyen daveti tekrar gönderir (notification için).
        
        Args:
            invitation_id: Davet ID'si
            resent_by: Tekrar gönderen kullanıcı ID'si
            
        Returns:
            {"success": True, "invitation_id": str}
        """
        invitation = cls._workspace_invitation_repo._get_by_id(session, record_id=invitation_id)
        
        if not invitation:
            raise ResourceNotFoundError(
                resource_name="WorkspaceInvitation",
                resource_id=invitation_id
            )
        
        # Sadece pending davetler tekrar gönderilebilir
        if invitation.status != InvitationStatus.PENDING:
            raise BusinessRuleViolationError(
                rule_name="invitation_not_pending",
                message="Only pending invitations can be resent"
            )
        
        # TODO: Notification/Email gönderimi buraya eklenebilir
        
        return {
            "success": True,
            "invitation_id": invitation.id,
            "invitee_email": invitation.email
        }

