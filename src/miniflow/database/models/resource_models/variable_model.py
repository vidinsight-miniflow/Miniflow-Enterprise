"""
VARIABLE MODEL - Environment Variables Tablosu
==============================================

Amaç:
    - Workspace içinde kullanılan environment variable'ları yönetir
    - Key-value çiftleri olarak saklanır
    - Workflow execution'larında kullanılır

İlişkiler:
    - Workspace (workspace) - Hangi workspace'de [N:1]

Temel Alanlar:
    - workspace_id: Hangi workspace'de
    - key: Variable anahtarı (workspace içinde benzersiz)
    - value: Variable değeri
    - description: Variable açıklaması
    - is_secret: Gizli mi? (şifreler, token'lar için)

Veri Bütünlüğü:
    - UniqueConstraint: (workspace_id, key) benzersiz olmalı

Önemli Notlar:
    - Workspace silindiğinde variable'lar da silinir (CASCADE)
    - is_secret=True ise value şifrelenmiş saklanmalı
    - BaseModel'den created_by/updated_by kullanılır
    - ID prefix: ENV (örn: ENV-ABC123...)
"""

from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, Text, Boolean, ForeignKey, UniqueConstraint

from ..base_model import BaseModel


class Variable(BaseModel):
    """Workspace environment variable'ları"""
    __prefix__ = "ENV"
    __tablename__ = 'variables'
    __table_args__ = (
        UniqueConstraint('workspace_id', 'key', name='_workspace_variable_key_unique'),
    )

    # İlişkiler
    workspace_id = Column(String(20), ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=False, index=True)
    owner_id = Column(String(20), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)


    # Variable verisi
    key = Column(String(100), nullable=False, index=True, unique=True)
    value = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    is_secret = Column(Boolean, default=False, nullable=False, index=True)

    # İlişkiler
    workspace = relationship("Workspace", back_populates="variables")
    owner = relationship("User", foreign_keys="[Variable.owner_id]")
