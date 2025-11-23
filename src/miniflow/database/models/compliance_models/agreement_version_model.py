from sqlalchemy import Column, String, Text, DateTime, Boolean, Index
from sqlalchemy.orm import relationship

from ..base_model import BaseModel


class AgreementVersion(BaseModel):
    """
    Sözleşme versiyonları
    
    Bu model, platform üzerindeki tüm sözleşme ve politika versiyonlarını saklar.
    Her sözleşme tipi için birden fazla versiyon olabilir ve sadece biri aktif olabilir.
    
    Attributes:
        agreement_type: Sözleşme tipi (terms, privacy_policy, cookie_policy, vb)
        version: Sözleşme versiyonu (1.0, 2.1, vb)
        content: Sözleşme içeriği (Markdown formatında)
        content_hash: İçerik SHA-256 hash'i (değişiklik tespiti için)
        effective_date: Yürürlüğe giriş tarihi
        is_active: Aktif versiyon mu?
        locale: Dil kodu (tr-TR, en-US, vb)
        created_by: Oluşturan admin kullanıcının ID'si
    """
    __prefix__ = "AGV"
    __tablename__ = "agreement_versions"
    
    __table_args__ = (
        Index('idx_agreement_active', 'agreement_type', 'is_active'),
        Index('idx_agreement_type_version', 'agreement_type', 'version'),
        Index('idx_effective_date', 'effective_date'),
    )
    
    # ====================================================================================================== TABLO KOLONLARI ==
    agreement_type = Column(String(50), nullable=False,
        comment="Sözleşme tipi: terms, privacy_policy, cookie_policy, data_processing, vb")
    version = Column(String(20), nullable=False,
        comment="Sözleşme versiyonu: 1.0, 2.1, vb")
    content = Column(Text, nullable=False,
        comment="Sözleşme içeriği (Markdown formatında)")
    content_hash = Column(String(64), nullable=False,
        comment="İçerik SHA-256 hash'i (değişiklik tespiti ve bütünlük kontrolü için)")
    effective_date = Column(DateTime, nullable=False,
        comment="Yürürlüğe giriş tarihi")
    is_active = Column(Boolean, default=False, nullable=False, index=True,
        comment="Aktif versiyon mu? (Her tip için sadece bir aktif versiyon olabilir)")
    locale = Column(String(10), default='tr-TR', nullable=False,
        comment="Dil kodu: tr-TR, en-US, de-DE, vb")
    created_by = Column(String(20), nullable=True,
        comment="Oluşturan admin kullanıcının ID'si")
    notes = Column(Text, nullable=True,
        comment="Versiyon notları ve değişiklik açıklaması")
    
    # ====================================================================================================== İLİŞKİLER ==
    acceptances = relationship(
        "UserAgreementAcceptance",
        back_populates="agreement_version",
        lazy="noload",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<AgreementVersion(id={self.id}, type={self.agreement_type}, version={self.version}, locale={self.locale})>"

