from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Float, Text, ForeignKey, JSON, Enum

from ..base_model import BaseModel
from ..enums import *


class Script(BaseModel):
    """Global script kütüphanesi - versiyonlama, test ve performans takibi ile çalıştırılabilir script'ler"""
    __prefix__ = "SCR"
    __tablename__ = 'scripts'

    # Temel bilgiler
    name = Column(String(100), nullable=False, unique=True, index=True,
        comment="Script adı (global olarak benzersiz)")
    description = Column(Text, nullable=True,
        comment="Script açıklaması")

    # Organizasyon - Gruplama için kategori ve alt kategori
    category = Column(String(50), nullable=False, index=True,
        comment="Kategori (zorunlu)")
    subcategory = Column(String(50), nullable=True, index=True,
        comment="Alt kategori (opsiyonel)")

    # Dosya bilgileri - Script depolama ve üst veri
    file_extension = Column(String(10), nullable=True,
        comment="Dosya uzantısı (.py, .js, .sh)")
    file_path = Column(Text, nullable=True,
        comment="Dosya yolu")
    file_size = Column(Integer, nullable=True,
        comment="Dosya boyutu (byte)")
    content = Column(Text, nullable=True,
        comment="Script içeriği")
    script_metadata = Column(JSON, nullable=True,
        comment="Meta veriler (JSON)")

    # Ortam - Gerekli Python paketleri
    required_packages = Column(JSON, default=lambda: [], nullable=False,
        comment="Gerekli paketler (JSON array)")

    # Şema tanımları - Input/output doğrulama
    input_schema = Column(JSON, default=lambda: {}, nullable=False,
        comment="Input validation şeması (JSON)")
    output_schema = Column(JSON, default=lambda: {}, nullable=False,
        comment="Output validation şeması (JSON)")

    # Üst veri ve dokümantasyon
    tags = Column(JSON, default=lambda: [], nullable=True,
        comment="Etiketler (JSON array)")
    documentation_url = Column(String(500), nullable=True,
        comment="Dokümantasyon URL'i")

    # İlişkiler
    nodes = relationship("Node", back_populates="script")