from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Boolean, Text, Enum, Index, UniqueConstraint
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

from qbitra.database.models import BaseModel
from qbitra.database.models.mixins import TimestampMixin
from qbitra.models.enums import LoginStatus, LoginMethod

class LoginHistory(BaseModel, TimestampMixin):
    """Kullanıcı giriş geçmişi modeli"""
    __prefix__ = "LGH"
    __tablename__ = "login_history"
    
    # ---- Table Args ---- #
    __table_args__ = (
        UniqueConstraint('session_id', name='_session_id_unique'),
        Index('idx_login_history_user_date', 'user_id', 'login_at'),
    )

    # ---- Login History  ---- #
    user_id = Column(String(20), ForeignKey("users.id", ondelete="CASCADE"), nullable=False,
    comment="Kullanıcı id'si (otomatik oturum yönetimi için)")
    session_id = Column(String(20), ForeignKey("auth_sessions.id", ondelete="CASCADE"), nullable=True, index=True,
    comment="Oturum id'si (otomatik oturum yönetimi için)")

    # ---- Login History Information ---- #
    login_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True,
    comment="Giriş tarihi (otomatik oturum yönetimi için)")
    status = Column(Enum(LoginStatus), nullable=False, index=True,
    comment="Giriş denemesi sonucu (success, failed, locked, suspended)")
    login_method = Column(Enum(LoginMethod), nullable=False, default=LoginMethod.PASSWORD, index=True,
    comment="Giriş için kullanılan yöntem (password, google, other)")

    # ---- Relations ---- #
    user = relationship("User", back_populates="login_history")
    session = relationship("AuthSession", back_populates="login_history")