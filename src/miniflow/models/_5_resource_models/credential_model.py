"""
CREDENTIAL MODEL - API Credentials ve Secrets Tablosu
=====================================================

Amaç:
    - Workspace içinde kullanılan API credentials ve secrets'ı yönetir
    - API keys, tokens, passwords güvenli şekilde saklanır
    - Workflow'larda harici servis entegrasyonları için kullanılır

İlişkiler:
    - Workspace (workspace) - Hangi workspace'de [N:1]

Temel Alanlar:
    - workspace_id: Hangi workspace'de
    - name: Credential adı (workspace içinde benzersiz)
    - credential_type: Credential tipi (API_KEY, OAUTH_TOKEN, PASSWORD, SSH_KEY, vb.)
    - description: Credential açıklaması

Credential Data (Encrypted JSON):
    - credential_data: Tüm credential bilgileri (JSON, encrypted)
      Her credential tipi için farklı yapı:
      * API_KEY: {"api_key": "...", "api_secret": "..."}
      * OAUTH_TOKEN: {"access_token": "...", "refresh_token": "...", "provider": "GOOGLE", "scopes": [...]}
      * PASSWORD: {"username": "...", "password": "..."}
      * SSH_KEY: {"private_key": "...", "public_key": "...", "passphrase": "..."}
      * AWS_CREDENTIALS: {"access_key_id": "...", "secret_access_key": "...", "region": "..."}

Status:
    - is_active: Credential aktif mi?
    - expires_at: Geçerlilik süresi bitiş tarihi
    - last_used_at: Son kullanım zamanı

Metadata:
    - tags: Etiketler (JSON array)

Veri Bütünlüğü:
    - UniqueConstraint: (workspace_id, name) benzersiz olmalı

Önemli Notlar:
    - Workspace silindiğinde credentials da silinir (CASCADE)
    - credential_data şifrelenmiş saklanmalı (tüm JSON şifrelenmiş)
    - Hassas bilgiler asla düz metin olarak saklanmamalı
    - expires_at geçmişse credential kullanılmamalı
    - BaseModel'den created_by/updated_by kullanılır
    - ID prefix: CRD (örn: CRD-ABC123...)
"""

from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, JSON, Enum, UniqueConstraint

from ..base_model import BaseModel
from ..enums import CredentialType, CredentialProvider


class Credential(BaseModel):
    """API credentials ve secrets"""
    __prefix__ = "CRD"
    __tablename__ = 'credentials'
    __table_args__ = (
        UniqueConstraint('workspace_id', 'name', name='_workspace_credential_name_unique'),
    )

    # İlişkiler
    workspace_id = Column(String(20), ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=False, index=True,
        comment="Hangi workspace'de")
    owner_id = Column(String(20), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True,
        comment="Credential sahibinin ID'si")

    # Temel bilgiler
    name = Column(String(100), nullable=False, index=True,
        comment="Credential adı (workspace içinde benzersiz)")
    credential_type = Column(Enum(CredentialType), nullable=False, index=True,
        comment="Credential tipi (API_KEY, OAUTH2, BASIC_AUTH, vb.)")
    credential_provider = Column(String(50), nullable=True, index=True,
        comment="Credential provider (sadece OAuth2 için: GOOGLE, MICROSOFT, GITHUB)")
    description = Column(Text, nullable=True,
        comment="Credential açıklaması")

    # Credential verisi (tüm JSON şifrelenmiş)
    credential_data = Column(JSON, nullable=False,
        comment="Tüm credential detayları ile şifrelenmiş JSON")

    # Durum
    is_active = Column(Boolean, default=True, nullable=False, index=True,
        comment="Credential aktif mi?")
    expires_at = Column(DateTime, nullable=True, index=True,
        comment="Geçerlilik süresi bitiş tarihi")
    last_used_at = Column(DateTime, nullable=True,
        comment="Son kullanım zamanı")

    # Üst veri
    tags = Column(JSON, default=lambda: [], nullable=True,
        comment="Etiketler (JSON array)")

    # İlişkiler
    workspace = relationship("Workspace", back_populates="credentials")
    owner = relationship("User", foreign_keys="[Credential.owner_id]")
