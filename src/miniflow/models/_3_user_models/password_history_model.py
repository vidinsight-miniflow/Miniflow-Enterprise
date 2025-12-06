from sqlalchemy.orm import relationship
from sqlalchemy import (
    Column, String, ForeignKey, DateTime, Index
)
from datetime import datetime, timezone

from ..base_model import BaseModel

class PasswordHistory(BaseModel):
    """Şifre değişiklik geçmişi"""
    __prefix__ = "PWH"
    __tablename__ = 'password_history'
    __table_args__ = (
        Index('idx_password_history_user', 'user_id'),
        Index('idx_password_history_created', 'created_at'),
    )

    # ====================================================================================================== TABLO KOLONLARI ==
    user_id = Column(String(20), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True, 
        comment="Hesap")
    password_hash = Column(String(255), nullable=False,
        comment="Eski şifre hash'i (tekrar kullanımı önlemek için)")
    change_reason = Column(String(50), nullable=True,
        comment="Neden: gönüllü, sıfırlama, süresi dolmuş, zorunlu, güvenlik ihlali")
    changed_from_ip = Column(String(45), nullable=True, 
        comment="Değişiklik yapılan IP adresi")
    changed_from_device = Column(String(255), nullable=True, 
        comment="Kullanıcı aracısı")

    user = relationship("User", back_populates="password_history", foreign_keys=[user_id])