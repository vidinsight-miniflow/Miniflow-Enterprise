from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Float, Text, ForeignKey, JSON, UniqueConstraint, CheckConstraint, Enum

from ..base_model import BaseModel
from ..enums import *


class Workspace(BaseModel):
    """Çalışma alanları - workflow'ları organize etmek ve takım işbirliği için"""
    __prefix__ = "WSP"
    __tablename__ = 'workspaces'
    __table_args__ = (
        UniqueConstraint('slug', name='_workspace_slug_unique'),
        CheckConstraint('member_limit > 0', name='_positive_member_limit'),
        CheckConstraint('workflow_limit > 0', name='_positive_workflow_limit'),
        CheckConstraint('current_member_count >= 0', name='_non_negative_member_count'),
        CheckConstraint('current_workflow_count >= 0', name='_non_negative_workflow_count'),
    )

    # Temel bilgiler
    name = Column(String(100), nullable=False, index=True,
        comment="Workspace adı")
    slug = Column(String(100), nullable=False, unique=True, index=True,
        comment="URL-friendly benzersiz slug")
    description = Column(Text, nullable=True,
        comment="Workspace açıklaması")
    
    # Sahiplik
    owner_id = Column(String(20), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True,
        comment="Workspace sahibinin ID'si")
    
    # Plan ve limitler (WORKSPACE TABANLI - oluşturulurken seçilir)
    plan_id = Column(String(20), ForeignKey('workspace_plans.id', ondelete='RESTRICT'), nullable=False, index=True,
        comment="Plan ID'si")
    
    # Üye limitleri
    member_limit = Column(Integer, nullable=False,
        comment="Üye limiti (seçilen plana göre PlanLimits'ten)")
    current_member_count = Column(Integer, default=1, nullable=False,
        comment="Mevcut üye sayısı (sahip dahil)")
    
    # Workflow limitleri
    workflow_limit = Column(Integer, nullable=False,
        comment="Workflow limiti (seçilen plana göre PlanLimits'ten)")
    current_workflow_count = Column(Integer, default=0, nullable=False,
        comment="Mevcut workflow sayısı")
    
    # Custom script limitleri
    custom_script_limit = Column(Integer, nullable=False,
        comment="Custom script limiti (seçilen plana göre PlanLimits'ten)")
    current_custom_script_count = Column(Integer, default=0, nullable=False,
        comment="Mevcut custom script sayısı")

    # Depolama ve execution limitleri
    max_file_size_mb_per_workspace = Column(Integer, nullable=False,
        comment="Dosya başına yükleme limiti")
    storage_limit_mb = Column(Integer, nullable=False,
        comment="Depolama limiti (MB)")
    current_storage_mb = Column(Float, default=0.0, nullable=False,
        comment="Mevcut depolama kullanımı (MB)")

    # API Key limitleri
    api_key_limit = Column(Integer, nullable=False,
        comment="API key limiti (seçilen plana göre PlanLimits'ten)")
    current_api_key_count = Column(Integer, default=0, nullable=False,
        comment="Mevcut API key sayısı")

    # Aylık limitler
    monthly_execution_limit = Column(Integer, nullable=False,
        comment="Aylık execution limiti")
    current_month_executions = Column(Integer, default=0, nullable=False,
        comment="Mevcut ay execution sayısı")
     
    monthly_concurrent_executions = Column(Integer, nullable=False,
        comment="Aylık eşzamanlı execution limiti")
    current_month_concurrent_executions = Column(Integer, default=0, nullable=False,
        comment="Mevcut ay eşzamanlı execution sayısı")


    # Durum
    is_suspended = Column(Boolean, default=False, nullable=False, index=True,
        comment="Workspace askıya alınmış mı? (ödeme yapılmadığında)")
    suspension_reason = Column(Text, nullable=True,
        comment="Askıya alma nedeni")
    suspended_at = Column(DateTime, nullable=True,
        comment="Askıya alma zamanı")
    
    # Ödeme sağlayıcı entegrasyonu (Stripe/Paddle)
    stripe_customer_id = Column(String(100), nullable=True, index=True,
        comment="Stripe customer ID (örn: cus_xxx)")
    stripe_subscription_id = Column(String(100), nullable=True, index=True,
        comment="Stripe subscription ID (örn: sub_xxx)")
    billing_email = Column(String(100), nullable=True,
        comment="Fatura email adresi (hızlı erişim için cache)")
    billing_currency = Column(String(3), default='USD', nullable=False,
        comment="Fatura para birimi")
    
    # Billing döngüsü (Stripe tarafından yönetilir, hızlı erişim için cache)
    current_period_start = Column(DateTime, nullable=True,
        comment="Mevcut billing döngüsü başlangıcı")
    current_period_end = Column(DateTime, nullable=True,
        comment="Mevcut billing döngüsü bitişi")
    
    # İlişkiler
    owner = relationship("User", foreign_keys="[Workspace.owner_id]", back_populates="owned_workspaces")
    members = relationship("WorkspaceMember", back_populates="workspace", cascade="all, delete-orphan", lazy="noload")
    invitations = relationship("WorkspaceInvitation", back_populates="workspace", cascade="all, delete-orphan", lazy="noload")
    
    # Workflow ve kaynak ilişkileri
    workflows = relationship("Workflow", back_populates="workspace", cascade="all, delete-orphan", lazy="noload")
    executions = relationship("Execution", foreign_keys="[Execution.workspace_id]", cascade="all, delete-orphan", lazy="noload", overlaps="workspace")
    execution_inputs = relationship("ExecutionInput", back_populates="workspace", cascade="all, delete-orphan", lazy="noload")
    execution_outputs = relationship("ExecutionOutput", back_populates="workspace", cascade="all, delete-orphan", lazy="noload")
    triggers = relationship("Trigger", back_populates="workspace", cascade="all, delete-orphan", lazy="noload")
    custom_scripts = relationship("CustomScript", back_populates="workspace", cascade="all, delete-orphan", lazy="noload")
    api_keys = relationship("ApiKey", back_populates="workspace", cascade="all, delete-orphan", lazy="noload")
    variables = relationship("Variable", back_populates="workspace", cascade="all, delete-orphan", lazy="noload")
    files = relationship("File", back_populates="workspace", cascade="all, delete-orphan", lazy="noload")
    databases = relationship("Database", back_populates="workspace", cascade="all, delete-orphan", lazy="noload")
    credentials = relationship("Credential", back_populates="workspace", cascade="all, delete-orphan", lazy="noload")