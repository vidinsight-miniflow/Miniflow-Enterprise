"""
EXECUTION INPUT MODEL - Node Execution Giriş Parametreleri Tablosu
===================================================================

Amaç:
    - Her node için execution parametrelerini saklar
    - Execution zamanlama ve bağımlılık takibi
    - Node çalıştırma sırasını belirler

İlişkiler:
    - Execution (execution) - Hangi execution [N:1]
    - Workflow (workflow) - Hangi workflow [N:1]
    - Workspace (workspace) - Hangi workspace [N:1]
    - Node (node) - Hangi node [N:1, nullable]

Temel Alanlar:
    - execution_id: Hangi execution
    - workflow_id: Hangi workflow
    - workspace_id: Hangi workspace (kaynak çözümleme için gerekli)
    - node_id: Hangi node (nullable - node silinirse kalır)
    - correlation_id: Dağıtık izleme için correlation ID

Zamanlama Parametreleri:
    - dependency_count: Kaç bağımlılık var (execution sırasını belirler)
    - priority: Öncelik seviyesi (yüksek önce çalışır)
    - wait_factor: Bekleme faktörü

Node Execution Verisi:
    - node_name: Node adı (anlık görüntü - node silinirse kaybolmaz)
    - node_params: Node parametreleri (JSON) - Kaynak referansları içerir
    - script_name: Script adı (anlık görüntü)
    - script_path: Script yolu (anlık görüntü)
    - script_content: Script içeriği (anlık görüntü - execution sırasında değişmemeli)

Giriş/Çıkış Şeması:
    - input_schema: Beklenen giriş şeması (doğrulama için)
    - output_schema: Beklenen çıkış şeması (doğrulama için)
    - input_data: Gerçek giriş verisi (JSON) - Trigger verisi ve önceki node çıktıları

BaseModel'den Gelen Alanlar:
    - id: ExecutionInput ID
    - created_at: Oluşturulma zamanı

Node Params Format:
    {
        "resources": {
            "credentials": [{"id": "CRD-XXX", "alias": "api_key"}],
            "databases": [{"id": "DBS-XXX", "alias": "postgres"}],
            "variables": [{"id": "ENV-XXX", "alias": "token"}],
            "files": [{"id": "FLE-XXX", "alias": "input_file"}]
        },
        "static_params": {
            "timeout": 30,
            "max_retries": 3
        }
    }

Input Data Format:
    {
        "trigger_data": {...},  # Trigger'dan gelen veriler
        "previous_nodes": {     # Önceki node'lardan gelen çıktılar
            "NODE-ID-1": {...},
            "NODE-ID-2": {...}
        }
    }

Önemli Notlar:
    - Execution silindiğinde input'lar da silinir (CASCADE)
    - Workspace silindiğinde input'lar da silinir (CASCADE)
    - Node silindiğinde input kalır ama node_id NULL olur (SET NULL)
    - Execution sırasında kullanılan tüm veri anlık görüntü olarak saklanır
    - workspace_id kaynak çözümleme için kritik
    - ID prefix: EXI (örn: EXI-ABC123...)
"""

from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, Integer, Text, ForeignKey, JSON, CheckConstraint, Index

from ..base_model import BaseModel


class ExecutionInput(BaseModel):
    """Node execution giriş parametreleri ve zamanlama"""
    __prefix__ = "EXI"
    __tablename__ = 'execution_inputs'
    __table_args__ = (
        # Veri bütünlüğü kısıtlamaları
        CheckConstraint('max_retries >= 0', name='_non_negative_max_retries'),
        CheckConstraint('retry_count >= 0', name='_non_negative_retry_count'),
        CheckConstraint('resource_retry_count >= 0', name='_non_negative_resource_retry_count'),
        CheckConstraint('timeout_seconds > 0', name='_positive_timeout'),
        CheckConstraint('dependency_count >= 0', name='_non_negative_dependency_count'),
        CheckConstraint('priority >= 0', name='_non_negative_priority'),
        
        # Performans optimizasyonu indeksleri
        # Kaldırıldı: next_retry_at ile Index (next_retry_at kolonu kaldırıldı)
        Index('idx_execution_input_ready', 'dependency_count'),  # get_ready_with_retry_check
        Index('idx_execution_input_cleanup', 'retry_count', 'resource_retry_count', 'created_at'),  # cleanup_failed_tasks
        # Composite index for _get_ready_inputs: filters by dependency_count=0 and orders by priority DESC, created_at ASC
        Index('idx_execution_input_ready_sorted', 'dependency_count', 'priority', 'created_at'),  # _get_ready_inputs optimization
    )

    # İlişkiler - Ana execution, workflow, workspace ve node
    execution_id = Column(String(20), ForeignKey('executions.id', ondelete='CASCADE'), nullable=False, index=True)
    workflow_id = Column(String(20), ForeignKey('workflows.id', ondelete='CASCADE'), nullable=False, index=True)
    workspace_id = Column(String(20), ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=False, index=True)
    node_id = Column(String(20), ForeignKey('nodes.id', ondelete='SET NULL'), nullable=True, index=True)

    # Zamanlama parametreleri - Execution sırası ve öncelik
    dependency_count = Column(Integer, default=0, nullable=False)
    priority = Column(Integer, default=0, nullable=False)
    wait_factor = Column(Integer, default=0, nullable=False)
    
    # Execution yapılandırması - Oluşturulma zamanında Node'dan kopyalanır
    max_retries = Column(Integer, default=3, nullable=False)
    timeout_seconds = Column(Integer, default=300, nullable=False)
    
    # Retry yönetimi - Kaynak izleme entegrasyonu
    retry_count = Column(Integer, default=0, nullable=False, index=True)
    resource_retry_count = Column(Integer, default=0, nullable=False)
    last_rejection_reason = Column(Text, nullable=True)

    # Node execution verisi - Execution zamanında anlık görüntü
    node_name = Column(String(100), nullable=False)
    params = Column(JSON, default=lambda: {}, nullable=False)
    
    # Script bilgileri - Execution zamanında anlık görüntü
    script_name = Column(String(100), nullable=False)
    script_path = Column(Text, nullable=False)

    # İlişkiler
    execution = relationship("Execution", back_populates="execution_inputs")
    workflow = relationship("Workflow", back_populates="execution_inputs")
    workspace = relationship("Workspace", back_populates="execution_inputs")
    node = relationship("Node", back_populates="execution_inputs")

