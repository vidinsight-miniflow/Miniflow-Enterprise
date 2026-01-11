from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Float, Text, ForeignKey, JSON, UniqueConstraint, CheckConstraint, Enum

from ..base_model import BaseModel
from ..enums import *


class Node(BaseModel):
    """Workflow node'ları tablosu"""
    __prefix__ = "NOD"
    __tablename__ = 'nodes'
    __table_args__ = (
        UniqueConstraint('workflow_id', 'name', name='_workflow_node_name_unique'),
        CheckConstraint('max_retries >= 0', name='_non_negative_retries'),
        CheckConstraint('timeout_seconds > 0', name='_positive_timeout'),
        CheckConstraint(
            '(script_id IS NOT NULL AND custom_script_id IS NULL) OR (script_id IS NULL AND custom_script_id IS NOT NULL)',
            name='_single_script_required'
        ),
    )

    # İlişkiler - Ana workflow ve ilişkili script (XOR: sadece biri ayarlanabilir)
    workflow_id = Column(String(20), ForeignKey('workflows.id', ondelete='CASCADE'), nullable=False, index=True,
        comment="Hangi workflow'da")
    script_id = Column(String(20), ForeignKey('scripts.id', ondelete='RESTRICT'), nullable=True, index=True,
        comment="Global script (script_id veya custom_script_id'den biri olmalı)")
    custom_script_id = Column(String(20), ForeignKey('custom_scripts.id', ondelete='RESTRICT'), nullable=True, index=True,
        comment="Custom script (script_id veya custom_script_id'den biri olmalı)")

    # Node konfigürasyonu
    name = Column(String(100), nullable=False,
        comment="Node adı (workflow içinde benzersiz)")
    description = Column(Text, nullable=True,
        comment="Node açıklaması")
    input_params = Column(JSON, nullable=True, default=lambda: {},
        comment="Giriş parametreleri (JSON)")
    output_params = Column(JSON, nullable=True, default=lambda: {},
        comment="Çıkış parametreleri (JSON)")
    meta_data = Column(JSON, default=lambda: {}, nullable=True,
        comment="Meta veriler (JSON)")
    
    # Execution ayarları - Retry ve timeout konfigürasyonu
    max_retries = Column(Integer, default=3, nullable=False,
        comment="Maksimum tekrar deneme sayısı (varsayılan: 3)")
    timeout_seconds = Column(Integer, default=300, nullable=False,
        comment="Timeout süresi saniye (varsayılan: 300)")

    # İlişkiler
    workflow = relationship("Workflow", back_populates="nodes")
    script = relationship("Script", back_populates="nodes")
    custom_script = relationship("CustomScript", back_populates="nodes")
    outgoing_edges = relationship("Edge", foreign_keys="[Edge.from_node_id]", back_populates="from_node", cascade="all, delete-orphan")
    incoming_edges = relationship("Edge", foreign_keys="[Edge.to_node_id]", back_populates="to_node", cascade="all, delete-orphan")
    execution_inputs = relationship("ExecutionInput", back_populates="node")
    execution_outputs = relationship("ExecutionOutput", back_populates="node")

    # ========================================================================================= YARDIMCI METODLAR =====
    @property
    def executable_script(self):
        """
        Çalıştırılacak script'i döndürür (global Script veya CustomScript)
        
        Kullanım:
            script = node.executable_script
            if script:
                execute(script.content)
        """
        return self.script or self.custom_script
    
    @property
    def script_type(self):
        """
        Kullanılan script tipini döndürür
        
        Returns:
            'GLOBAL' eğer global Script kullanılıyorsa
            'CUSTOM' eğer CustomScript kullanılıyorsa
            None eğer script atanmamışsa
        """
        if self.script_id:
            return 'GLOBAL'
        elif self.custom_script_id:
            return 'CUSTOM'
        return None

