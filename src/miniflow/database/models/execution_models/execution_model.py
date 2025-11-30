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

    # Execution verisi - Giriş ve çıkış
    trigger_data = Column(JSON, default=lambda: {}, nullable=False)  # Trigger'dan gelen input
    results = Column(JSON, default=lambda: {}, nullable=False)  # Final sonuçlar

    # Retry ve kurtarma
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=0, nullable=False)
    is_retry = Column(Boolean, default=False, nullable=False)
    parent_execution_id = Column(String(20), ForeignKey('executions.id', ondelete='SET NULL'), nullable=True)

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
    def duration(self):
        """Süreyi hesapla ve güncelle"""
        if self.ended_at and self.started_at:
            # Timezone-aware ve timezone-naive datetime'ları uyumlu hale getir
            ended_at = self.ended_at
            started_at = self.started_at
            
            # Eğer biri timezone-aware, diğeri timezone-naive ise, naive olanı UTC'ye çevir
            if ended_at.tzinfo is None and started_at.tzinfo is not None:
                ended_at = ended_at.replace(tzinfo=timezone.utc)
            elif ended_at.tzinfo is not None and started_at.tzinfo is None:
                started_at = started_at.replace(tzinfo=timezone.utc)
            
            delta = ended_at - started_at
            return delta.total_seconds()
        return -1