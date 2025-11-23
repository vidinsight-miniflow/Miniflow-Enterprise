from datetime import datetime, timezone, timedelta
import secrets
from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, DateTime, Boolean, Text, ForeignKey, UniqueConstraint, Enum, Index

from ..base_model import BaseModel
from ..enums import *


class WorkspaceInvitation(BaseModel):
    """Workspace davet yönetimi"""
    __prefix__ = "WIN"  # Workspace Invitation
    __tablename__ = 'workspace_invitations'
    __table_args__ = (
        UniqueConstraint('workspace_id', 'email', name='_workspace_email_unique'),
        Index('idx_invitation_token', 'invitation_token'),
        Index('idx_invitation_email', 'email'),
        Index('idx_invitation_status', 'status'),
        Index('idx_invitation_expires', 'expires_at'),
    )

    # İlişkiler
    workspace_id = Column(String(20), ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=False, index=True,
        comment="Hangi workspace'e davet")
    invited_by = Column(String(20), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True,
        comment="Daveti gönderen kullanıcının ID'si")
    invitee_id = Column(String(20), ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True,
        comment="Davet edilen kullanıcı ID'si (kayıt olduktan sonra doldurulur)")
    
    # Davet detayları
    email = Column(String(100), nullable=False, index=True,
        comment="Davet edilen email adresi")
    role_id = Column(String(20), ForeignKey('user_roles.id', ondelete='RESTRICT'), nullable=False,
        comment="Davet edilen kullanıcıya verilecek rol")
    
    # Token ve güvenlik
    invitation_token = Column(String(64), nullable=False, unique=True, index=True,
        comment="Benzersiz davet token'ı (URL'de kullanılır)")
    expires_at = Column(DateTime, nullable=False, index=True,
        comment="Token son kullanma tarihi (genellikle 7 gün)")
    is_used = Column(Boolean, default=False, nullable=False,
        comment="Token kullanıldı mı?")
    
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
    @staticmethod
    def generate_invitation_token() -> str:
        """Benzersiz davet token'ı oluştur"""
        return secrets.token_urlsafe(48)
    
    @property
    def is_expired(self) -> bool:
        """Davetin süresinin dolup dolmadığını kontrol et"""
        # SQLite'dan gelen timezone-naive datetime'ı düzelt
        expires_at = self.expires_at
        if expires_at and expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        
        return datetime.now(timezone.utc) > expires_at or self.status == InvitationStatus.EXPIRED
    
    @property
    def is_pending(self) -> bool:
        """Davetin hala bekleyen durumda olup olmadığını kontrol et"""
        return self.status == InvitationStatus.PENDING and not self.is_expired
    
    @property
    def is_accepted(self) -> bool:
        """Davetin kabul edilip edilmediğini kontrol et"""
        return self.status == InvitationStatus.ACCEPTED
    
    @property
    def is_declined(self) -> bool:
        """Davetin reddedilip reddedilmediğini kontrol et"""
        return self.status == InvitationStatus.DECLINED
    
    @property
    def days_until_expiry(self) -> int:
        """Davetin süresinin dolmasına kalan gün sayısını hesapla"""
        # SQLite'dan gelen timezone-naive datetime'ı düzelt
        expires_at = self.expires_at
        if expires_at and expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        
        delta = expires_at - datetime.now(timezone.utc)
        return max(0, delta.days)
    
    def accept_invitation(self, invitee_id: str):
        """
        Daveti kabul et ve kullanıldı olarak işaretle.
        
        Args:
            invitee_id: Daveti kabul eden kullanıcının ID'si
        """
        self.status = InvitationStatus.ACCEPTED
        self.accepted_at = datetime.now(timezone.utc)
        self.invitee_id = invitee_id
        self.is_used = True
    
    def decline_invitation(self):
        """Daveti reddet"""
        self.status = InvitationStatus.DECLINED
        self.declined_at = datetime.now(timezone.utc)
    
    def cancel_invitation(self):
        """Daveti iptal et"""
        self.status = InvitationStatus.CANCELLED
    
    def mark_as_expired(self):
        """Daveti süresi dolmuş olarak işaretle"""
        self.status = InvitationStatus.EXPIRED