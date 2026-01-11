from sqlalchemy.orm import relationship
from sqlalchemy import (
    Column, String, JSON, ForeignKey, Index, UniqueConstraint
)
from datetime import datetime, timezone

from ..base_model import BaseModel


class UserPreference(BaseModel):
    """Kullanıcı tercihleri"""
    __prefix__ = "PRF"
    __tablename__ = 'user_preferences'
    __table_args__ = (
              UniqueConstraint('user_id', 'key', name='_user_preference_key_unique'),
              Index('idx_preference_user_key', 'user_id', 'key'),
              Index('idx_preference_category', 'category'),
              )

    # ====================================================================================================== TABLO KOLONLARI ==
    user_id = Column(String(20), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True,
        comment="Kullanıcı")
    key = Column(String(100), nullable=False, index=True,
        comment="Tercih anahtarı (örn: 'email_notifications', 'theme', 'language')")
    value = Column(JSON, nullable=False,
        comment="Değer şunlardan biri olabilir: string, number, boolean, object, array")
    category = Column(String(50), nullable=True, index=True,
        comment="Kategori: ui, notifications, privacy, email, integrations, accessibility")
    description = Column(String(500), nullable=True,
        comment="Açıklama")
    
    user = relationship("User", back_populates="preferences")