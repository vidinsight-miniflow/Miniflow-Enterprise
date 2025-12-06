from sqlalchemy.orm import relationship
from sqlalchemy import (
    Column, String, Boolean, DateTime, Text, ForeignKey, Integer, JSON,
    Index, Enum
)
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime, timezone
import enum

from ..base_model import BaseModel
from ..enums import *


class LoginHistory(BaseModel):
    """Giriş denemesi geçmişi"""
    __prefix__ = "LGH"
    __tablename__ = 'login_history'
    __table_args__ = (
        # Yaygın sorgular için indeksler
        Index('idx_login_user_created', 'user_id', 'created_at'),
        Index('idx_login_user_status', 'user_id', 'status'),
        Index('idx_login_status_created', 'status', 'created_at'),
        Index('idx_login_ip', 'ip_address'),
        Index('idx_login_session', 'session_id'),
        Index('idx_login_country', 'country_code'),
        Index('idx_login_suspicious', 'is_suspicious'),
    )

    # ====================================================================================================== TABLO KOLONLARI ==
    user_id = Column(String(20), ForeignKey('users.id', ondelete='CASCADE'), nullable=True, index=True,
        comment="Giriş yapmayı deneyen kullanıcı (bulunamazsa NULL)")
    session_id = Column(String(20), ForeignKey('auth_sessions.id', ondelete='SET NULL'), nullable=True, index=True,
        comment="Oluşturulan oturum ID'si (giriş başarılıysa)")
    status = Column(Enum(LoginStatus), nullable=False, index=True,
        comment="Giriş denemesi sonucu")
    login_method = Column(Enum(LoginMethod), nullable=False, default=LoginMethod.PASSWORD,
        comment="Giriş için kullanılan yöntem")
    failure_reason = Column(String(255), nullable=True,
        comment="Başarısızlık nedeni: invalid_password, account_locked, vb.")
    attempt_number = Column(Integer, default=1, nullable=False,
        comment="Bu kullanıcı için sıralı deneme numarası")
    ip_address = Column(String(45), nullable=True, index=True,
        comment="IPv4 veya IPv6 adresi")
    timezone = Column(String(50), nullable=True,
        comment="GeoIP'den IANA timezone")
    country_code = Column(String(2), nullable=True, index=True,
        comment="GeoIP'den ISO ülke kodu")
    city = Column(String(100), nullable=True,
        comment="GeoIP'den şehir")
    user_agent = Column(Text, nullable=True,
        comment="Tam kullanıcı aracısı string'i")
    device_type = Column(Enum(DeviceType), default=DeviceType.UNKNOWN, nullable=False,
        comment="Cihaz tipi (Desktop, Mobile, Tablet, Bot, Unknown)")
    browser = Column(String(100), nullable=True,
        comment="Tarayıcı adı ve versiyonu (örn: 'Chrome 120')")
    os = Column(String(100), nullable=True,
        comment="İşletim Sistemi (Windows 11, macOS 14, iOS 17, vb.)")
    is_suspicious = Column(Boolean, default=False, nullable=False, index=True,
        comment="Dolandırıcılık tespiti tarafından şüpheli olarak işaretlendi")
    login_metadata = Column(JSON, default=dict, nullable=False,
        comment="Ek bağlam verisi")
    
    # ====================================================================================================== İLİŞKİLER ==
    user = relationship("User", back_populates="login_history")
    session = relationship("AuthSession", foreign_keys="[LoginHistory.session_id]")