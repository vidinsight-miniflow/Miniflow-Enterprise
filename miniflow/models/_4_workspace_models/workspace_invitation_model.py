from datetime import datetime, timezone
from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, UniqueConstraint, Enum, Index

from ..base_model import BaseModel
from ..enums import *


class WorkspaceInvitation(BaseModel):
    """Workspace davet yönetimi"""
    __prefix__ = "WIN"  # Workspace Invitation
    __tablename__ = 'workspace_invitations'
    __table_args__ = (
        UniqueConstraint('workspace_id', 'invitee_id', name='_workspace_invitee_unique'),
        Index('idx_invitation_invitee', 'invitee_id'),
        Index('idx_invitation_status', 'status'),
    )

    # İlişkiler
    workspace_id = Column(String(20), ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=False, index=True,
        comment="Hangi workspace'e davet")
    invited_by = Column(String(20), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True,
        comment="Daveti gönderen kullanıcının ID'si")
    invitee_id = Column(String(20), ForeignKey('users.id', ondelete='SET NULL'), nullable=False, index=True,
        comment="Davet edilen kullanıcı ID'si")
    
    # Davet detayları
    email = Column(String(100), nullable=True, index=True,
        comment="Davet edilen kullanıcının email adresi (bilgi amaçlı)")
    role_id = Column(String(20), ForeignKey('user_roles.id', ondelete='RESTRICT'), nullable=False,
        comment="Davet edilen kullanıcıya verilecek rol")
    
    # Durum
    status = Column(Enum(InvitationStatus), default=InvitationStatus.PENDING, nullable=False, index=True,
        comment="Davet durumu (PENDING, ACCEPTED, DECLINED, EXPIRED, CANCELLED)")
    accepted_at = Column(DateTime, nullable=True,
        comment="Kabul edilme zamanı")
    declined_at = Column(DateTime, nullable=True,
        comment="Reddedilme zamanı")
    
    # Opsiyonel mesaj
    message = Column(Text, nullable=True,
        comment="Davet mesajı (opsiyonel)")
    
    # İlişkiler
    workspace = relationship("Workspace", back_populates="invitations")
    inviter = relationship("User", foreign_keys="[WorkspaceInvitation.invited_by]")
    invitee = relationship("User", foreign_keys="[WorkspaceInvitation.invitee_id]")
    role = relationship("UserRoles")
    
    # ========================================================================================= YARDIMCI METODLAR =====
    @property
    def is_pending(self) -> bool:
        """Davetin hala bekleyen durumda olup olmadığını kontrol et"""
        return self.status == InvitationStatus.PENDING
    
    @property
    def is_accepted(self) -> bool:
        """Davetin kabul edilip edilmediğini kontrol et"""
        return self.status == InvitationStatus.ACCEPTED
    
    @property
    def is_declined(self) -> bool:
        """Davetin reddedilip reddedilmediğini kontrol et"""
        return self.status == InvitationStatus.DECLINED
    
    def accept_invitation(self):
        """Daveti kabul et"""
        self.status = InvitationStatus.ACCEPTED
        self.accepted_at = datetime.now(timezone.utc)
    
    def decline_invitation(self):
        """Daveti reddet"""
        self.status = InvitationStatus.DECLINED
        self.declined_at = datetime.now(timezone.utc)
    
    def cancel_invitation(self):
        """Daveti iptal et"""
        self.status = InvitationStatus.CANCELLED