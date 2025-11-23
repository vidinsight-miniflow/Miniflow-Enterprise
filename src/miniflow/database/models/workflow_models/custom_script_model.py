from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Float, Text, ForeignKey, JSON, Enum, UniqueConstraint, Index

from ..base_model import BaseModel
from ..enums import *


class CustomScript(BaseModel):
    """Kullanıcı script'leri - workspace'lerde yüklenen onay workflow'u ile custom script'ler"""
    __prefix__ = "CSC"
    __tablename__ = 'custom_scripts'
    __table_args__ = (
        UniqueConstraint('workspace_id', 'name', name='_workspace_script_name_unique'),
        # Performans optimizasyonu
        Index('idx_custom_script_approval', 'workspace_id', 'approval_status'),
    )

    # Workspace ve sahiplik
    workspace_id = Column(String(20), ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=False, index=True,
        comment="Hangi workspace'de")
    uploaded_by = Column(String(20), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True,
        comment="Script'i yükleyen kullanıcı")
    
    # Temel bilgiler
    name = Column(String(100), nullable=False, unique=True, index=True,
        comment="Script adı (workspace içinde benzersiz)")
    description = Column(Text, nullable=True,
        comment="Script açıklaması")
    content = Column(Text, nullable=False,
        comment="Script içeriği (zorunlu)")
    file_extension = Column(String(10), nullable=True,
        comment="Dosya uzantısı (.py, .js, .sh)")
    file_size = Column(Integer, nullable=True,
        comment="Dosya boyutu (byte)")
    file_path = Column(Text, nullable=True,
        comment="Disk üzerindeki dosya yolu")
    
    # Organizasyon - Gruplama için kategori ve alt kategori
    category = Column(String(50), nullable=True, index=True,
        comment="Kategori (opsiyonel)")
    subcategory = Column(String(50), nullable=True, index=True,
        comment="Alt kategori (opsiyonel)")
    
    # Ortam ve gereksinimler
    required_packages = Column(JSON, default=lambda: [], nullable=False,
        comment="Gerekli paketler (JSON array)")
    input_schema = Column(JSON, default=lambda: {}, nullable=False,
        comment="Input validation şeması (JSON)")
    output_schema = Column(JSON, default=lambda: {}, nullable=False,
        comment="Output validation şeması (JSON)")
    
    # Onay workflow'u
    approval_status = Column(Enum(ScriptApprovalStatus), default=ScriptApprovalStatus.PENDING, nullable=False, index=True,
        comment="Durum (PENDING, APPROVED, REJECTED)")
    reviewed_by = Column(String(20), ForeignKey('users.id', ondelete='SET NULL'), nullable=True,
        comment="Script'i review eden kullanıcı")
    reviewed_at = Column(DateTime, nullable=True,
        comment="Ne zaman review edildi")
    review_notes = Column(Text, nullable=True,
        comment="Review notları")
    
    # Test ve kalite
    test_status = Column(Enum(ScriptTestStatus), default=ScriptTestStatus.UNTESTED, nullable=False, index=True,
        comment="Test durumu (UNTESTED, PASSED, FAILED, SKIPPED)")
    test_coverage = Column(Float, nullable=True,
        comment="Test coverage yüzdesi")
    test_results = Column(JSON, default=lambda: {}, nullable=False,
        comment="Test sonuçları (JSON)")
    is_dangerous = Column(Boolean, default=False, nullable=False,
        comment="Tehlikeli script işareti")
    
    # Üst veri
    tags = Column(JSON, default=lambda: [], nullable=True,
        comment="Etiketler (JSON array)")
    documentation_url = Column(String(500), nullable=True,
        comment="Dokümantasyon URL'i")
    
    # İlişkiler
    workspace = relationship("Workspace", back_populates="custom_scripts")
    uploader = relationship("User", foreign_keys="[CustomScript.uploaded_by]", back_populates="uploaded_scripts")
    reviewer = relationship("User", foreign_keys="[CustomScript.reviewed_by]", back_populates="reviewed_scripts")
    nodes = relationship("Node", back_populates="custom_script")
