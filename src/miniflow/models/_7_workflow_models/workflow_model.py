from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, Integer, Boolean, Float, Text, ForeignKey, JSON, Enum, UniqueConstraint, Index

from ..base_model import BaseModel
from ..enums import WorkflowStatus

class Workflow(BaseModel):
    """İş akışları tanımlama ve yönetim tablosu"""
    __prefix__ = "WFL"
    __tablename__ = 'workflows'
    __table_args__ = (
        UniqueConstraint('workspace_id', 'name', name='_workspace_workflow_name_unique'),
        
        # Performans optimizasyonu için bileşik indeks
        Index('idx_workflow_workspace_status', 'workspace_id', 'status'),
    )

    # Sahiplik ve erişim kontrolü
    workspace_id = Column(String(20), ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=False, index=True,
        comment="Hangi workspace'de")

    # Temel workflow bilgileri
    name = Column(String(100), nullable=False, index=True,
        comment="Workflow adı (workspace içinde benzersiz)")
    description = Column(Text, nullable=True,
        comment="Workflow açıklaması")
    priority = Column(Integer, default=1, nullable=False,
        comment="Öncelik seviyesi (varsayılan: 1)")
    status = Column(Enum(WorkflowStatus), default=WorkflowStatus.DRAFT, nullable=False, index=True,
        comment="Durum (DRAFT, ACTIVE, DEACTIVATED, ARCHIVED)")
    status_message = Column(Text, nullable=True, default='Currently no error context is available',
        comment="Durum mesajı")
    tags = Column(JSON, default=lambda: [], nullable=True,
        comment="Etiketler (JSON array)")

    # İlişkiler
    workspace = relationship("Workspace", back_populates="workflows")
    nodes = relationship("Node", back_populates="workflow", cascade="all, delete-orphan")
    edges = relationship("Edge", back_populates="workflow", cascade="all, delete-orphan")
    executions = relationship("Execution", back_populates="workflow", cascade="all, delete-orphan")
    triggers = relationship("Trigger", back_populates="workflow", cascade="all, delete-orphan")
    execution_inputs = relationship("ExecutionInput", back_populates="workflow", cascade="all, delete-orphan")
    execution_outputs = relationship("ExecutionOutput", back_populates="workflow", cascade="all, delete-orphan")