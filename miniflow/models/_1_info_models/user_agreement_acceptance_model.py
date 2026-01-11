from sqlalchemy import Column, String, DateTime, ForeignKey, Index, JSON, Text
from sqlalchemy.orm import relationship

from ..base_model import BaseModel


class UserAgreementAcceptance(BaseModel):
    """
    Kullanıcı sözleşme kabulü kayıtları
    
    Bu model, kullanıcıların sözleşme kabullerini tam bir audit trail ile saklar.
    GDPR uyumluluğu için gerekli tüm bilgileri içerir.
    
    Attributes:
        user_id: Kullanıcı ID'si
        agreement_version_id: Kabul edilen sözleşme versiyonu ID'si
        accepted_at: Kabul zamanı
        ip_address_hash: IP adresi SHA-256 hash'i (GDPR için şifrelenmiş)
        user_agent_hash: User agent hash'i (cihaz bilgisi için)
        acceptance_method: Kabul yöntemi (web, mobile, api)
        locale: Kabul edildiği dil
        acceptance_metadata: Ek bilgiler (device_type, app_version, geolocation, vb)
    
    Legal Requirements:
        - IP adresi ve user agent hash'lenerek saklanır (GDPR Article 32)
        - Tam audit trail sağlar (GDPR Article 5)
        - Rıza kanıtı olarak mahkemede kullanılabilir
        - "Unutulma hakkı" için user_id ile silinebilir (GDPR Article 17)
    """
    __prefix__ = "UAA"
    __tablename__ = "user_agreement_acceptances"
    
    __table_args__ = (
        Index('idx_user_agreements', 'user_id', 'agreement_version_id'),
        Index('idx_user_accepted_at', 'user_id', 'accepted_at'),
        Index('idx_accepted_at', 'accepted_at'),
    )
    
    # ====================================================================================================== TABLO KOLONLARI ==
    user_id = Column(String(20), ForeignKey('users.id', ondelete='CASCADE'), 
        nullable=False,
        comment="Kullanıcı ID'si")
    agreement_version_id = Column(String(20), 
        ForeignKey('agreement_versions.id', ondelete='RESTRICT'), 
        nullable=False,
        comment="Kabul edilen sözleşme versiyonu ID'si (RESTRICT: Kullanılan versiyonlar silinemez)")
    accepted_at = Column(DateTime, nullable=False, index=True,
        comment="Kabul zamanı (UTC)")
    ip_address_hash = Column(String(64), nullable=True,
        comment="IP adresi SHA-256 hash'i (GDPR Article 32 - şifrelenmiş saklama)")
    user_agent_hash = Column(String(64), nullable=True,
        comment="User agent SHA-256 hash'i (cihaz/tarayıcı bilgisi)")
    acceptance_method = Column(String(50), nullable=False,
        comment="Kabul yöntemi: web, mobile_ios, mobile_android, api, admin_action")
    locale = Column(String(10), nullable=False,
        comment="Kabul edildiği dil kodu (tr-TR, en-US, vb)")
    acceptance_metadata = Column(JSON, default=dict, nullable=False,
        comment="Ek bilgiler: {device_type, app_version, os_version, geolocation, referrer, vb}")
    
    # Rıza geri çekme takibi (opsiyonel)
    revoked_at = Column(DateTime, nullable=True,
        comment="Rıza geri çekme zamanı (GDPR Article 7.3)")
    revoked_reason = Column(Text, nullable=True,
        comment="Rıza geri çekme nedeni")
    
    # ====================================================================================================== İLİŞKİLER ==
    user = relationship("User", back_populates="agreement_acceptances")
    agreement_version = relationship("AgreementVersion", back_populates="acceptances")
    
    def __repr__(self):
        return f"<UserAgreementAcceptance(id={self.id}, user_id={self.user_id}, accepted_at={self.accepted_at})>"
    
    @property
    def is_revoked(self) -> bool:
        """Rıza geri çekilmiş mi?"""
        return self.revoked_at is not None

