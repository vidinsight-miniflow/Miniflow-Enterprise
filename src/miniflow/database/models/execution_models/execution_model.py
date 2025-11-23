"""
EXECUTION MODEL - Workflow Execution İnstance'ları Tablosu
==========================================================

Amaç:
    - Workflow çalıştırmalarını takip eder
    - Gerçek zamanlı execution izleme
    - Performans ve hata takibi

İlişkiler:
    - Workspace (workspace) - Hangi workspace'de [N:1]
    - Workflow (workflow) - Hangi workflow çalıştırılıyor [N:1]
    - Trigger (trigger) - Nasıl tetiklendi [N:1, nullable]
    - ExecutionInput (execution_inputs) - Node input'ları [1:N]
    - ExecutionOutput (execution_outputs) - Node output'ları [1:N]

Temel Alanlar:
    - workspace_id: Hangi workspace'de (çoklu kiracılık)
    - workflow_id: Hangi workflow
    - trigger_id: Nasıl tetiklendi (manuel, zamanlanmış, webhook, vb.)
    - status: Execution durumu (PENDING, RUNNING, COMPLETED, FAILED, CANCELLED, TIMEOUT)

Zamanlama ve Performans:
    - started_at: Başlangıç zamanı
    - ended_at: Bitiş zamanı
    - duration_seconds: Toplam süre (saniye)
    - timeout_seconds: Timeout limiti

Node İlerleme Takibi:
    - pending_nodes: Bekleyen node'lar
    - running_nodes: Çalışan node'lar
    - completed_nodes: Tamamlanan node'lar (başarılı + başarısız)
    
    NOT: total_nodes property olarak hesaplanır (pending + running + completed)

Execution Verisi:
    - trigger_data: Trigger'dan gelen giriş verisi (JSON)
    - results: Final execution sonuçları (JSON)
    - error_message: Hata mesajı (eğer varsa)
    - error_details: Detaylı hata bilgisi (JSON)

Retry ve Kurtarma:
    - retry_count: Kaç kez retry edildi
    - max_retries: Maksimum retry sayısı
    - is_retry: Bu bir retry execution mı?
    - parent_execution_id: Retry ise, ana execution ID'si

Üst Veri:
    - triggered_by: Kim tetikledi (user_id veya 'system')
    - execution_context: Execution bağlam bilgisi (JSON)

BaseModel'den Gelen Alanlar:
    - id: Execution ID
    - created_at: Oluşturulma zamanı
    - created_by: Oluşturan kullanıcı
    - updated_at: Son güncelleme

Veri Bütünlüğü:
    - CheckConstraint: retry_count >= 0
    - CheckConstraint: max_retries >= 0
    - duration_seconds property olarak hesaplanır (kolon değil)

Önemli Notlar:
    - Workspace silindiğinde execution'lar da silinir (CASCADE)
    - Workflow silindiğinde execution'lar da silinir (CASCADE)
    - Trigger silindiğinde execution kalır ama trigger_id NULL olur (SET NULL)
    - Gerçek zamanlı takip için status ve node sayaçları güncellenir
    - ID prefix: EXE (örn: EXE-ABC123...)
"""

from datetime import datetime, timezone
from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, Text, ForeignKey, JSON, Enum, CheckConstraint, Index

from ..base_model import BaseModel
from ..enums import ExecutionStatus


class Execution(BaseModel):
    """Workflow execution instance'ları kapsamlı takip ile"""
    __prefix__ = "EXE"
    __tablename__ = 'executions'
    __table_args__ = (
        # Veri bütünlüğü kısıtlamaları
        CheckConstraint('retry_count >= 0', name='_non_negative_retry_count'),
        CheckConstraint('max_retries >= 0', name='_non_negative_max_retries'),
        # Not: duration_seconds property olarak hesaplanır (kolon değil)
        
        # Performans optimizasyonu için composite indeksler
        Index('idx_execution_workspace_status_created', 'workspace_id', 'status', 'created_at'),
        Index('idx_execution_workflow_status', 'workflow_id', 'status'),
    )

    # İlişkiler - Workspace, Workflow ve Trigger
    workspace_id = Column(String(20), ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=False, index=True)
    workflow_id = Column(String(20), ForeignKey('workflows.id', ondelete='CASCADE'), nullable=False, index=True)
    trigger_id = Column(String(20), ForeignKey('triggers.id', ondelete='SET NULL'), nullable=True, index=True)

    # Execution durumu ve zamanlama
    status = Column(Enum(ExecutionStatus), default=ExecutionStatus.PENDING, nullable=False, index=True)
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    ended_at = Column(DateTime, nullable=True)
    timeout_seconds = Column(Integer, nullable=True)  # Timeout limiti (saniye)

    # Execution verisi - Giriş ve çıkış
    trigger_data = Column(JSON, default=lambda: {}, nullable=False)  # Trigger'dan gelen input
    results = Column(JSON, default=lambda: {}, nullable=False)  # Final sonuçlar
    
    # Hata takibi
    error_message = Column(Text, nullable=True)  # Kısa hata mesajı
    error_details = Column(JSON, nullable=True)  # Detaylı hata bilgisi (stack trace, vb.)
    
    # Retry ve recovery
    retry_count = Column(Integer, default=0, nullable=False)  # Kaç kez retry edildi
    max_retries = Column(Integer, default=0, nullable=False)  # Maksimum retry sayısı
    is_retry = Column(Boolean, default=False, nullable=False)  # Bu bir retry execution mı?
    parent_execution_id = Column(String(20), ForeignKey('executions.id', ondelete='SET NULL'), nullable=True)
    
    # Node ilerleme takibi (property olarak hesaplanır, kolon değil)
    # pending_nodes, running_nodes, completed_nodes property olarak hesaplanır
    
    # Üst veri
    triggered_by = Column(String(20), nullable=True, index=True)  # Kim tetikledi (user_id veya 'system')
    execution_context = Column(JSON, default=lambda: {}, nullable=True)  # Ek bağlam

    # İlişkiler
    workspace = relationship("Workspace", foreign_keys="[Execution.workspace_id]", overlaps="executions")
    workflow = relationship("Workflow", back_populates="executions")
    trigger = relationship("Trigger", back_populates="executions")
    execution_inputs = relationship("ExecutionInput", back_populates="execution", cascade="all, delete-orphan")
    execution_outputs = relationship("ExecutionOutput", back_populates="execution", cascade="all, delete-orphan")
    
    # Retry takibi için self-referential
    parent_execution = relationship("Execution", remote_side="[Execution.id]", foreign_keys="[Execution.parent_execution_id]")
    
    # ========================================================================================= YARDIMCI METODLAR =====

    @property
    def calculate_duration(self):
        """Süreyi hesapla ve güncelle"""
        if self.ended_at and self.started_at:
            delta = self.ended_at - self.started_at
            return delta.total_seconds()
        return -1
    
    @property
    def pending_nodes(self):
        """Bekleyen node sayısını hesapla"""
        return len([ei for ei in self.execution_inputs if ei.dependency_count > 0])
    
    @property
    def running_nodes(self):
        """Çalışan node sayısını hesapla"""
        return len([eo for eo in self.execution_outputs if eo.status == 'RUNNING'])
    
    @property
    def completed_nodes(self):
        """Tamamlanan node sayısını hesapla (başarılı + başarısız)"""
        return len([eo for eo in self.execution_outputs if eo.status in ['SUCCESS', 'FAILED', 'SKIPPED', 'TIMEOUT', 'CANCELLED']])
    
    @property
    def total_nodes(self):
        """Toplam node sayısını hesapla"""
        return self.pending_nodes + self.running_nodes + self.completed_nodes