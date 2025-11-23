"""
USER LIMITS MODEL - Kullanıcı Rolleri ve Yetkileri Tablosu
==========================================================

Amaç:
    - Kullanıcı rollerini ve yetkilerini tek tabloda yönetir
    - Enum yerine database tablosu kullanır
    - Plan bazlı yetki kısıtlamaları
    - Basit ve etkili yetki kontrolü

İlişkiler:
    - WorkspaceMember (workspace_members) - Bu rolü kullanan üyeler [1:N]

Temel Alanlar:
    - name: Rol adı (örn: "Owner", "Admin", "Editor", "Viewer")
    - description: Rol açıklaması

Workspace Yetkileri:
    - can_view_workspace: Workspace görüntüleme
    - can_edit_workspace: Workspace düzenleme
    - can_delete_workspace: Workspace silme
    - can_invite_members: Üye davet etme
    - can_remove_members: Üye çıkarma
    - can_change_plan: Plan değiştirme

Workflow Yetkileri:
    - can_view_workflows: Workflow görüntüleme
    - can_create_workflows: Workflow oluşturma
    - can_edit_workflows: Workflow düzenleme
    - can_delete_workflows: Workflow silme
    - can_execute_workflows: Workflow çalıştırma
    - can_share_workflows: Workflow paylaşımı

Credential Yetkileri:
    - can_view_credentials: Credential görüntüleme
    - can_create_credentials: Credential oluşturma
    - can_edit_credentials: Credential düzenleme
    - can_delete_credentials: Credential silme
    - can_share_credentials: Credential paylaşımı
    - can_view_credential_values: Credential değerlerini görme

File Yetkileri:
    - can_view_files: Dosya görüntüleme
    - can_upload_files: Dosya yükleme
    - can_download_files: Dosya indirme
    - can_delete_files: Dosya silme
    - can_share_files: Dosya paylaşımı

Database Yetkileri:
    - can_view_databases: Database görüntüleme
    - can_create_databases: Database oluşturma
    - can_edit_databases: Database düzenleme
    - can_delete_databases: Database silme
    - can_share_databases: Database paylaşımı
    - can_view_connection_details: Bağlantı detaylarını görme

Variable Yetkileri:
    - can_view_variables: Variable görüntüleme
    - can_create_variables: Variable oluşturma
    - can_edit_variables: Variable düzenleme
    - can_delete_variables: Variable silme
    - can_share_variables: Variable paylaşımı
    - can_view_variable_values: Variable değerlerini görme

API Key Yetkileri:
    - can_view_api_keys: API Key görüntüleme
    - can_create_api_keys: API Key oluşturma
    - can_edit_api_keys: API Key düzenleme
    - can_delete_api_keys: API Key silme
    - can_share_api_keys: API Key paylaşımı
    - can_view_api_key_values: API Key değerlerini görme

Plan ve Sistem:
    - min_plan_level: Minimum plan seviyesi (0-4)
    - is_system_role: Sistem rolü mü? (silinemez)
    - is_active: Aktif mi?
    - display_order: Sıralama

Veri Bütünlüğü:
    - UniqueConstraint: code benzersiz olmalı
    - CheckConstraint: min_plan_level 0-4 arasında olmalı

Önemli Notlar:
    - Bu tablo seed data ile doldurulur
    - Sistem rolleri silinemez (is_system_role=True)
    - Plan seviyesine göre yetkiler kısıtlanabilir
    - ID prefix: URM (örn: URM-ABC123...)
"""

from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, Integer, Boolean, Text, UniqueConstraint, CheckConstraint, Enum

from ..base_model import BaseModel

class UserRoles(BaseModel):
    """Kullanıcı rolleri ve yetkileri tek tabloda"""
    __prefix__ = "URM"
    __tablename__ = 'user_roles'
    __table_args__ = (
        UniqueConstraint('name', name='_user_role_name_unique'),
    )

    # Temel bilgiler
    name = Column(String(50), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Workspace Yetkileri
    can_view_workspace = Column(Boolean, default=True, nullable=False)
    can_edit_workspace = Column(Boolean, default=False, nullable=False)
    can_delete_workspace = Column(Boolean, default=False, nullable=False)
    can_invite_members = Column(Boolean, default=False, nullable=False)
    can_remove_members = Column(Boolean, default=False, nullable=False)
    can_change_plan = Column(Boolean, default=False, nullable=False)
    
    # Workflow Yetkileri
    can_view_workflows = Column(Boolean, default=True, nullable=False)
    can_create_workflows = Column(Boolean, default=False, nullable=False)
    can_edit_workflows = Column(Boolean, default=False, nullable=False)
    can_delete_workflows = Column(Boolean, default=False, nullable=False)
    can_execute_workflows = Column(Boolean, default=True, nullable=False)
    can_share_workflows = Column(Boolean, default=False, nullable=False)
    
    # Credential Yetkileri
    can_view_credentials = Column(Boolean, default=True, nullable=False)
    can_create_credentials = Column(Boolean, default=False, nullable=False)
    can_edit_credentials = Column(Boolean, default=False, nullable=False)
    can_delete_credentials = Column(Boolean, default=False, nullable=False)
    can_share_credentials = Column(Boolean, default=False, nullable=False)
    can_view_credential_values = Column(Boolean, default=False, nullable=False)
    
    # File Yetkileri
    can_view_files = Column(Boolean, default=True, nullable=False)
    can_upload_files = Column(Boolean, default=False, nullable=False)
    can_download_files = Column(Boolean, default=True, nullable=False)
    can_delete_files = Column(Boolean, default=False, nullable=False)
    can_share_files = Column(Boolean, default=False, nullable=False)
    
    # Database Yetkileri
    can_view_databases = Column(Boolean, default=True, nullable=False)
    can_create_databases = Column(Boolean, default=False, nullable=False)
    can_edit_databases = Column(Boolean, default=False, nullable=False)
    can_delete_databases = Column(Boolean, default=False, nullable=False)
    can_share_databases = Column(Boolean, default=False, nullable=False)
    can_view_connection_details = Column(Boolean, default=False, nullable=False)
    
    # Variable Yetkileri
    can_view_variables = Column(Boolean, default=True, nullable=False)
    can_create_variables = Column(Boolean, default=False, nullable=False)
    can_edit_variables = Column(Boolean, default=False, nullable=False)
    can_delete_variables = Column(Boolean, default=False, nullable=False)
    can_share_variables = Column(Boolean, default=False, nullable=False)
    can_view_variable_values = Column(Boolean, default=False, nullable=False)
    
    # API Key Yetkileri
    can_create_api_keys = Column(Boolean, default=False, nullable=False)
    can_view_api_keys = Column(Boolean, default=True, nullable=False)
    can_edit_api_keys = Column(Boolean, default=False, nullable=False)
    can_delete_api_keys = Column(Boolean, default=False, nullable=False)
    can_share_api_keys = Column(Boolean, default=False, nullable=False)
    can_view_api_key_values = Column(Boolean, default=False, nullable=False)
    
    # Plan ve Sistem
    is_system_role = Column(Boolean, default=True, nullable=False)
    display_order = Column(Integer, default=0, nullable=False)
    
    # Relationships
    workspace_members = relationship("WorkspaceMember", back_populates="user_role")