"""
DATABASE MODEL - Veritabanı Bağlantıları Tablosu
================================================

Amaç:
    - Workspace içinde kullanılan veritabanı bağlantılarını yönetir
    - Connection string ve credentials bilgilerini tutar
    - Workflow'larda database işlemleri için kullanılır

İlişkiler:
    - Workspace (workspace) - Hangi workspace'de [N:1]

Temel Alanlar:
    - workspace_id: Hangi workspace'de
    - name: Bağlantı adı (workspace içinde benzersiz)
    - database_type: Veritabanı tipi (POSTGRESQL, MYSQL, MONGODB, REDIS, vb.)
    - host: Sunucu adresi
    - port: Port numarası
    - database_name: Veritabanı adı
    - username: Kullanıcı adı
    - password: Şifre (şifrelenmiş)

Connection Details:
    - connection_string: Connection string (opsiyonel)
    - ssl_enabled: SSL kullanılıyor mu?
    - additional_params: Ek parametreler (JSON)

Status:
    - is_active: Bağlantı aktif mi?
    - last_tested_at: Son test zamanı
    - last_test_status: Son test durumu (SUCCESS, FAILED)

Metadata:
    - description: Bağlantı açıklaması
    - tags: Etiketler (JSON array)

Veri Bütünlüğü:
    - UniqueConstraint: (workspace_id, name) benzersiz olmalı

Önemli Notlar:
    - Workspace silindiğinde bağlantılar da silinir (CASCADE)
    - password alanı şifrelenmiş saklanmalı
    - connection_string kullanılırsa host/port/username/password opsiyonel
    - BaseModel'den created_by/updated_by kullanılır
    - ID prefix: DBS (örn: DBS-ABC123...)
"""

from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, Integer, Text, Boolean, DateTime, ForeignKey, JSON, Enum, UniqueConstraint

from ..base_model import BaseModel
from ..enums import *


class Database(BaseModel):
    """Veritabanı bağlantıları"""
    __prefix__ = "DBS"
    __tablename__ = 'databases'
    __table_args__ = (
        UniqueConstraint('workspace_id', 'name', name='_workspace_database_name_unique'),
    )

    # İlişkiler
    workspace_id = Column(String(20), ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=False, index=True)
    owner_id = Column(String(20), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)


    # Temel bilgiler
    name = Column(String(100), nullable=False, index=True, unique=True)
    database_type = Column(Enum(DatabaseType), nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Bağlantı detayları
    host = Column(String(255), nullable=True)
    port = Column(Integer, nullable=True)
    database_name = Column(String(100), nullable=True)
    username = Column(String(100), nullable=True)
    password = Column(Text, nullable=True)  # Şifrelenmiş
    connection_string = Column(Text, nullable=True)  # Tekil alanlara alternatif
    ssl_enabled = Column(Boolean, default=False, nullable=False)
    additional_params = Column(JSON, default=lambda: {}, nullable=True)

    # Durum
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    last_tested_at = Column(DateTime, nullable=True)
    last_test_status = Column(String(20), nullable=True)

    # Üst veri
    tags = Column(JSON, default=lambda: [], nullable=True)

    # İlişkiler
    workspace = relationship("Workspace", back_populates="databases")
    owner = relationship("User", foreign_keys="[Database.owner_id]")


