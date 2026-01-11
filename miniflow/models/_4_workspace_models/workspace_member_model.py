from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, JSON, UniqueConstraint, Enum, Index

from ..base_model import BaseModel
from ..enums import *


class WorkspaceMember(BaseModel):
    """Workspace üyelik tablosu (Junction Table) - User ve Workspace arasında many-to-many ilişki"""
    __prefix__ = "WMB"
    __tablename__ = 'workspace_members'
    __table_args__ = (
        UniqueConstraint('workspace_id', 'user_id', name='_workspace_user_unique'),
        # Performans optimizasyonu
        Index('idx_workspace_member_role', 'workspace_id', 'role_id'),
    )

    # İlişkiler
    workspace_id = Column(String(20), ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=False, index=True,
        comment="Workspace ID'si")
    user_id = Column(String(20), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True,
        comment="Kullanıcı ID'si")
    role_id = Column(String(20), ForeignKey('user_roles.id', ondelete='RESTRICT'), nullable=False, index=True,
        comment="Kullanıcı rolü ID'si")
    role_name = Column(String(100), nullable=False, index=True,
        comment="Kullanıcı rolü adı")
    
    # Davet ve katılım
    invited_by = Column(String(20), ForeignKey('users.id', ondelete='SET NULL'), nullable=True,
        comment="Daveti gönderen kullanıcının ID'si")
    joined_at = Column(DateTime, nullable=True,
        comment="Kullanıcının katılma zamanı (NULL = henüz katılmadı)")
    
    # Durum
    last_accessed_at = Column(DateTime, nullable=True,
        comment="Son erişim zamanı")
    
    # Özel izinler (opsiyonel, detaylı kontrol için)
    custom_permissions = Column(JSON, default=lambda: {}, nullable=True,
        comment="Rol bazlı izinleri override etmek için JSON (örn: {\"can_delete_workflows\": false})")
    
    # İlişkiler
    workspace = relationship("Workspace", back_populates="members")
    user = relationship("User", foreign_keys="[WorkspaceMember.user_id]", back_populates="workspace_memberships")
    inviter = relationship("User", foreign_keys="[WorkspaceMember.invited_by]")
    user_role = relationship("UserRoles", back_populates="workspace_members")

    # ========================================================================================= YARDIMCI METODLAR =====
    @property
    def is_owner(self):
        """Kullanıcının workspace sahibi olup olmadığını kontrol et"""
        return self.user_role.is_owner_level()
    
    @property
    def is_admin(self):
        """Kullanıcının admin veya owner olup olmadığını kontrol et"""
        return self.user_role.is_admin_level() or self.user_role.is_owner_level()
    
    @property
    def can_edit(self):
        """Kullanıcının kaynakları düzenleyip düzenleyemeyeceğini kontrol et (EDITOR+)"""
        return self.user_role.can_edit_workflows or self.user_role.can_edit_workspace
    
    @property
    def can_view(self):
        """Kullanıcının kaynakları görüntüleyip görüntüleyemeyeceğini kontrol et (VIEWER+)"""
        return self.user_role.can_view_workspace or self.user_role.can_view_workflows