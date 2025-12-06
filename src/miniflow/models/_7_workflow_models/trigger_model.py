from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, ForeignKey, JSON, Enum, UniqueConstraint, Index

from ..base_model import BaseModel
from ..enums import *


class Trigger(BaseModel):
    """Workflow tetikleyicileri - workspace bağlı otomatik workflow çalıştırma"""
    __prefix__ = "TRG"
    __tablename__ = 'triggers'
    __table_args__ = (
        UniqueConstraint('workspace_id', 'name', name='_workspace_trigger_name_unique'),
        # Performans optimizasyonu
        Index('idx_trigger_workspace_enabled', 'workspace_id', 'is_enabled'),
    )
    
    # İlişkiler - Workspace ve Workflow
    workspace_id = Column(String(20), ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=False, index=True,
        comment="Hangi workspace'de")
    workflow_id = Column(String(20), ForeignKey('workflows.id', ondelete='CASCADE'), nullable=False, index=True,
        comment="Hangi workflow'u tetikler")
    
    # Trigger konfigürasyonu - Temel bilgiler
    name = Column(String(100), nullable=False, index=True,
        comment="Trigger adı (workspace içinde benzersiz)")
    description = Column(Text, nullable=True,
        comment="Trigger açıklaması")
    trigger_type = Column(Enum(TriggerType), nullable=False, index=True,
        comment="Trigger tipi (API, SCHEDULED, WEBHOOK, EVENT)")
    config = Column(JSON, default=lambda: {}, nullable=False,
        comment="Trigger konfigürasyonu (JSON) - trigger tipine göre farklı parametreler")
    input_mapping = Column(JSON, default=lambda: {}, nullable=True,
        comment="Input mapping kuralları (JSON)")
    is_enabled = Column(Boolean, default=True, nullable=False, index=True,
        comment="Trigger aktif mi?")

    # İlişkiler
    workspace = relationship("Workspace", back_populates="triggers")
    workflow = relationship("Workflow", back_populates="triggers")
    executions = relationship("Execution", back_populates="trigger")
