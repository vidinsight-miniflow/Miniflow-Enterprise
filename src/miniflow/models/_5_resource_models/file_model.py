"""
FILE MODEL - Upload Edilen Dosyalar Tablosu
===========================================

Amaç:
    - Workspace içinde upload edilen dosyaları yönetir
    - File metadata ve storage bilgilerini tutar
    - Workflow'larda input/output olarak kullanılır

İlişkiler:
    - Workspace (workspace) - Hangi workspace'de [N:1]

Temel Alanlar:
    - workspace_id: Hangi workspace'de
    - name: Dosya adı (workspace içinde benzersiz)
    - original_filename: Orijinal dosya adı
    - file_path: Dosya yolu (storage)
    - file_size: Dosya boyutu (byte)
    - mime_type: MIME tipi (image/png, text/csv, vb.)
    - file_extension: Dosya uzantısı

Metadata:
    - description: Dosya açıklaması
    - tags: Etiketler (JSON array)
    - metadata: Ek metadata (JSON)

BaseModel'den Gelen Alanlar:
    - created_by: Kim upload etti (uploaded_by yerine)
    - created_at: Upload zamanı
    - updated_by: Kim güncelledi
    - updated_at: Güncellenme zamanı

Veri Bütünlüğü:
    - UniqueConstraint: (workspace_id, name) benzersiz olmalı

Önemli Notlar:
    - Workspace silindiğinde dosyalar da silinir (CASCADE)
    - file_path storage sistemine göre düzenlenir (S3, local, vb.)
    - file_size workspace storage limitine sayılır
    - BaseModel'den created_by kullanılır (uploaded_by kaldırıldı)
    - ID prefix: FLE (örn: FLE-ABC123...)
"""

from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, Integer, Text, ForeignKey, JSON, UniqueConstraint

from ..base_model import BaseModel


class File(BaseModel):
    """Yüklenen dosyalar"""
    __prefix__ = "FLE"
    __tablename__ = 'files'
    __table_args__ = (
        UniqueConstraint('workspace_id', 'name', name='_workspace_file_name_unique'),
    )

    # İlişkiler
    workspace_id = Column(String(20), ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=False, index=True)
    owner_id = Column(String(20), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)

    # Dosya bilgileri
    name = Column(String(255), nullable=False, index=True, unique=True)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(Text, nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=True)
    file_extension = Column(String(10), nullable=True)

    # Üst veri
    description = Column(Text, nullable=True)
    tags = Column(JSON, default=lambda: [], nullable=True)
    file_metadata = Column(JSON, default=lambda: {}, nullable=True)  # 'metadata' SQLAlchemy'de rezerve edilmiş

    # İlişkiler
    workspace = relationship("Workspace", back_populates="files")
    owner = relationship("User", foreign_keys="[File.owner_id]")
