"""
EXECUTION OUTPUT MODEL - Node Execution Çıktıları Tablosu
=========================================================

Amaç:
    - Her node execution'ının sonucunu saklar
    - Performans takibi (süre, bellek, vb.)
    - Hata loglama ve hata ayıklama

İlişkiler:
    - Execution (execution) - Hangi execution [N:1]
    - Workflow (workflow) - Hangi workflow [N:1]
    - Node (node) - Hangi node [N:1, nullable]

Temel Alanlar:
    - execution_id: Hangi execution
    - workflow_id: Hangi workflow
    - workspace_id: Hangi workspace
    - node_id: Hangi node (nullable - node silinirse kalır)

Execution Durumu:
    - status: Node execution durumu (String: PENDING, RUNNING, SUCCESS, FAILED, SKIPPED, TIMEOUT, CANCELLED)
    - exit_code: İşlem çıkış kodu (0 = başarılı, >0 = hata)

Execution Sonuçları:
    - result_data: Execution çıktı verisi (JSON)
    - stdout: Standart çıktı (loglar)
    - stderr: Standart hata (hatalar)

Performans Takibi:
    - started_at: Başlangıç zamanı
    - ended_at: Bitiş zamanı
    - duration_seconds: Toplam süre (saniye)
    - memory_mb: Kullanılan bellek (MB)
    - cpu_percent: CPU kullanım yüzdesi

Hata ve Retry Takibi:
    - error_message: Kısa hata mesajı
    - error_details: Detaylı hata bilgisi (JSON - stack trace, vb.)
    - retry_count: Kaç kez retry edildi
    - is_retry: Bu bir retry mı?

Üst Veri:
    - execution_metadata: Ek üst veri (JSON)

BaseModel'den Gelen Alanlar:
    - id: ExecutionOutput ID
    - created_at: Oluşturulma zamanı
    - updated_at: Son güncelleme

Veri Bütünlüğü:
    - CheckConstraint: retry_count >= 0
    - duration property olarak hesaplanır (duration_seconds kolon değil)

Önemli Notlar:
    - Execution silindiğinde output'lar da silinir (CASCADE)
    - Workspace silindiğinde output'lar da silinir (CASCADE)
    - Node silindiğinde output kalır ama node_id NULL olur (SET NULL)
    - Hata ayıklama için stdout/stderr saklanır
    - Performans metrikleri sonradan analiz için kullanılır
    - ID prefix: EXO (örn: EXO-ABC123...)
"""

from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, Text, ForeignKey, JSON, CheckConstraint, Index

from ..base_model import BaseModel


class ExecutionOutput(BaseModel):
    """Node execution sonuçları ve performans takibi"""
    __prefix__ = "EXO"
    __tablename__ = 'execution_outputs'
    __table_args__ = (
        # Veri bütünlüğü kısıtlamaları
        CheckConstraint('retry_count >= 0', name='_non_negative_retry_count'),
        # Performans optimizasyonu
        Index('idx_execution_output_exec_status', 'execution_id', 'status'),
    )

    # İlişkiler - Ana execution, workflow, workspace ve node
    execution_id = Column(String(20), ForeignKey('executions.id', ondelete='CASCADE'), nullable=False, index=True)
    workflow_id = Column(String(20), ForeignKey('workflows.id', ondelete='CASCADE'), nullable=False, index=True)
    workspace_id = Column(String(20), ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=False, index=True)
    node_id = Column(String(20), ForeignKey('nodes.id', ondelete='SET NULL'), nullable=True, index=True)

    # Execution durumu (PENDING, RUNNING, SUCCESS, FAILED, SKIPPED, TIMEOUT, CANCELLED)
    status = Column(String(20), default='PENDING', nullable=False, index=True)

    # Execution sonuçları
    result_data = Column(JSON, nullable=True, default=lambda: {})  # Node çıktı verisi

    # Performans takibi - Zamanlama
    started_at = Column(DateTime, nullable=True, index=True)
    ended_at = Column(DateTime, nullable=True)

    # Performans takibi - Kaynaklar
    memory_mb = Column(Float, nullable=True)  # En yüksek bellek kullanımı (MB)
    cpu_percent = Column(Float, nullable=True)  # Ortalama CPU kullanımı (%)

    # Hata ve retry takibi
    error_message = Column(Text, nullable=True)  # Kısa hata mesajı
    error_details = Column(JSON, nullable=True)  # Detaylı hata bilgisi (stack trace, vb.)
    retry_count = Column(Integer, default=0, nullable=False)  # Kaç kez retry edildi

    # Üst veri
    execution_metadata = Column(JSON, default=lambda: {}, nullable=True)  # Ek üst veri

    # İlişkiler
    execution = relationship("Execution", back_populates="execution_outputs")
    workflow = relationship("Workflow", back_populates="execution_outputs")
    workspace = relationship("Workspace", back_populates="execution_outputs")
    node = relationship("Node", back_populates="execution_outputs")
    
    # ========================================================================================= YARDIMCI METODLAR =====
    
    @property
    def duration(self):
        """Süreyi hesapla ve güncelle"""
        if self.ended_at and self.started_at:
            delta = self.ended_at - self.started_at
            return delta.total_seconds()
        return -1