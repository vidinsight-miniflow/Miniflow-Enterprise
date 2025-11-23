from sqlalchemy.orm import relationship
from sqlalchemy import (
    Column, String, Boolean, DateTime, Text, Integer, ForeignKey, UniqueConstraint
)
from datetime import datetime, timezone

from ..base_model import BaseModel


class AuthSession(BaseModel):
    """Kimlik doğrulama oturumları - hem access hem refresh token'ları çift olarak tutar"""
    __prefix__ = "AUS"  # Auth Session (3 karakter gerekli)
    __tablename__ = 'auth_sessions'
    __table_args__ = (
        UniqueConstraint('access_token_jti', name='_access_token_jti_unique'),
        UniqueConstraint('refresh_token_jti', name='_refresh_token_jti_unique'),
    )

    # İlişkiler - Sahip kullanıcı
    user_id = Column(String(20), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)

    # Access Token - API erişimi için kısa ömürlü token
    access_token_jti = Column(String(100), nullable=False, unique=True, index=True)
    access_token_created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    access_token_expires_at = Column(DateTime, nullable=False, index=True)
    access_token_last_used_at = Column(DateTime, nullable=True)
    
    # Refresh Token - Yeni access token'lar almak için uzun ömürlü token
    refresh_token_jti = Column(String(100), nullable=False, unique=True, index=True)
    refresh_token_created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    refresh_token_expires_at = Column(DateTime, nullable=False, index=True)
    refresh_token_last_used_at = Column(DateTime, nullable=True)

    # İptal - Oturum geçersiz kılma
    is_revoked = Column(Boolean, default=False, nullable=False, index=True)
    revoked_at = Column(DateTime, nullable=True)
    revoked_by = Column(String(20), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    revocation_reason = Column(Text, nullable=True)
    
    # Oturum takibi - Cihaz ve konum bilgileri
    device_name = Column(String(100), nullable=True)  # örn: 'iPhone 13', 'Chrome on Windows'
    device_type = Column(String(50), nullable=True)  # 'mobile', 'desktop', 'tablet', 'api'
    user_agent = Column(String(500), nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 maksimum uzunluk

    # Coğrafi bilgiler
    country = Column(String(2), nullable=True)  # ISO ülke kodu
    city = Column(String(100), nullable=True)
    
    # Kullanım istatistikleri
    total_requests = Column(Integer, default=0, nullable=False)
    last_activity_at = Column(DateTime, nullable=True, index=True)
    
    # İlişkiler
    user = relationship("User", foreign_keys="[AuthSession.user_id]", back_populates="auth_sessions")