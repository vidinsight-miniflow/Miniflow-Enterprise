import re
import secrets
from typing import Dict, Any
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import relationship
from sqlalchemy import (
    Column, String, Integer, DateTime, Boolean, Text,
    UniqueConstraint, CheckConstraint, Index, event, JSON
)

from ..base_model import BaseModel


class User(BaseModel):
    """Kullanıcı hesapları"""
    __prefix__ = "USR"
    __tablename__ = "users"

    __table_args__ = (
        # Benzersizlik kısıtlamaları
        UniqueConstraint('username', name='_user_username_unique'),
        UniqueConstraint('email', name='_user_email_unique'),
        
        # Kontrol kısıtlamaları
        CheckConstraint('length(username) >= 3', name='_username_min_length'),
        CheckConstraint('length(username) <= 50', name='_username_max_length'),
        
        # İndeksler
        Index('idx_user_email', 'email'),
        Index('idx_user_username', 'username'),
        Index('idx_user_email_verification_token', 'email_verification_token'),
        Index('idx_user_reset_token', 'password_reset_token'),
    )

    # ====================================================================================================== TABLO KOLONLARI ==
    username = Column(String(50), nullable=False, unique=True, index=True,
        comment="Kullanıcı adı")
    name = Column(String(100), nullable=True,
        comment="Ad")
    surname = Column(String(100), nullable=True,
        comment="Soyad")
    email = Column(String(100), nullable=False, unique=True, index=True,
        comment="E-posta adresi")
    hashed_password = Column(String(255), nullable=True,
        comment="Hashlenmiş şifre")    
    password_changed_at = Column(DateTime, nullable=True,
        comment="Şifre değiştirilme zamanı")
    avatar_url = Column(String(500), nullable=True,
        comment="Avatar URL'i")
    
    # İletişim/Telefon Bilgileri
    country_code = Column(String(2), nullable=True, 
        comment="ISO ülke kodu")
    phone_number = Column(String(20), nullable=True, 
        comment="E.164 formatı: +905551234567")
    phone_verified_at = Column(DateTime, nullable=True,
        comment="Telefon doğrulama zamanı")

    # Hesap Durumu
    is_verified = Column(Boolean, default=False, nullable=False, index=True,
        comment="E-posta doğrulanmış")
    is_locked = Column(Boolean, default=False, nullable=False,
        comment="Hesap kilitli (detaylar için login_history'ye bakın)")
    locked_reason = Column(Text, nullable=True,
        comment="Kilitlenme nedeni")
    locked_until = Column(DateTime, nullable=True,
        comment="Geçici kilitler için otomatik açılma zamanı")

    # E-posta Doğrulama
    email_verified_at = Column(DateTime, nullable=True,
        comment="E-posta doğrulama zamanı")
    email_verification_token = Column(String(100), nullable=True, index=True,
        comment="E-posta doğrulama token'ı")
    email_verification_token_expires_at = Column(DateTime, nullable=True,
        comment="E-posta doğrulama token'ı son kullanma zamanı")

    # Şifre Sıfırlama
    password_reset_token = Column(String(100), nullable=True, index=True,
        comment="Şifre sıfırlama token'ı")
    password_reset_token_expires_at = Column(DateTime, nullable=True,
        comment="Şifre sıfırlama token'ı son kullanma zamanı")

    # Workspace Bilgileri
    current_workspace_count = Column(Integer, default=0, nullable=False,
        comment="Sahip olunan toplam workspace sayısı")
    current_free_workspace_count = Column(Integer, default=0, nullable=False,
        comment="ÜCRETSİZ plan workspace sayısı (maksimum 1 izin verilir)")

    # Marketing Consent (sözleşmelerden bağımsız opt-in)
    marketing_consent = Column(Boolean, default=False, nullable=False,
        comment="Pazarlama iletişimi için izin (sözleşme kabulünden bağımsız)")
    marketing_consent_at = Column(DateTime, nullable=True,
        comment="Pazarlama izni verilme zamanı")
    
    # Hesap silme (30 günlük bekleme süresi)
    deletion_requested_at = Column(DateTime, nullable=True,
        comment="Silme isteği zamanı")
    deletion_scheduled_for = Column(DateTime, nullable=True,
        comment="Silme için planlanan zaman")
    deletion_reason = Column(Text, nullable=True,
        comment="Silme nedeni")
    
    # Veri export takibi
    last_data_export_at = Column(DateTime, nullable=True,
        comment="Son veri export zamanı")

    # Üst veri
    is_superadmin = Column(Boolean, default=False, nullable=False,
        comment="Süper yönetici kullanıcı mı?")
    user_metadata = Column(JSON, default=dict, nullable=False,
        comment="Ek veri için esnek depolama")

    # ====================================================================================================== İLİŞKİLER ==
    login_history = relationship(
        "LoginHistory",
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="LoginHistory.created_at.desc()",
        lazy="noload"  # Prevent accidental loading of potentially large login history
    )

    password_history = relationship(
        "PasswordHistory",
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="PasswordHistory.created_at.desc()",
        lazy="noload"  # Use PasswordHistoryCRUD.get_user_password_history() instead
    )

    preferences = relationship(
        "UserPreference",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin"  # Small dataset, safe to eager load
    )

    auth_sessions = relationship(
        "AuthSession",
        foreign_keys="[AuthSession.user_id]",
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="AuthSession.created_at.desc()",
        lazy="noload"  # Use AuthSessionCRUD.get_user_sessions() instead
    )
    
    # Workspace relationships
    owned_workspaces = relationship(
        "Workspace",
        foreign_keys="[Workspace.owner_id]",
        back_populates="owner",
        cascade="all, delete-orphan",
        lazy="noload"  # Use WorkspaceCRUD to fetch workspaces
    )
    
    workspace_memberships = relationship(
        "WorkspaceMember",
        foreign_keys="[WorkspaceMember.user_id]",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="noload"  # Use WorkspaceMemberCRUD to fetch memberships
    )
    
    # Custom script relationships
    uploaded_scripts = relationship(
        "CustomScript",
        foreign_keys="[CustomScript.uploaded_by]",
        back_populates="uploader",
        lazy="noload"
    )
    
    reviewed_scripts = relationship(
        "CustomScript",
        foreign_keys="[CustomScript.reviewed_by]",
        back_populates="reviewer",
        lazy="noload"
    )
    
    # API Keys owned by user
    api_keys = relationship(
        "ApiKey",
        foreign_keys="[ApiKey.owner_id]",
        back_populates="owner",
        lazy="noload"
    )
    
    # Notifications for user
    notifications = relationship(
        "Notification",
        foreign_keys="[Notification.user_id]",
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="Notification.created_at.desc()",
        lazy="noload"  # Use NotificationService to fetch notifications
    )
    
    # Agreement acceptances (GDPR compliance)
    agreement_acceptances = relationship(
        "UserAgreementAcceptance",
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="UserAgreementAcceptance.accepted_at.desc()",
        lazy="noload"  # Use ComplianceService to fetch agreement history
    )

    @staticmethod
    def validate_email_format(email: str) -> bool:
        """E-posta formatını doğrula"""
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_regex, email))
    
    @staticmethod
    def validate_password_strength(password: str) -> Dict[str, any]:
        """Şifre gücünü politika karşısında doğrula"""
        errors = []
        
        if len(password) < 8:
            errors.append("Şifre en az 8 karakter olmalıdır")
        if not re.search(r'[A-Z]', password):
            errors.append("Şifre en az bir büyük harf içermelidir")
        if not re.search(r'[a-z]', password):
            errors.append("Şifre en az bir küçük harf içermelidir")
        if not re.search(r'\d', password):
            errors.append("Şifre en az bir rakam içermelidir")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/~`]', password):
            errors.append("Şifre en az bir özel karakter içermelidir")
        
        return {"valid": len(errors) == 0, "errors": errors}
    
    @staticmethod
    def validate_username(username: str) -> Dict[str, any]:
        """Kullanıcı adı formatını doğrula"""
        errors = []
        
        if len(username) < 3:
            errors.append("Kullanıcı adı en az 3 karakter olmalıdır")
        if len(username) > 50:
            errors.append("Kullanıcı adı en fazla 50 karakter olabilir")
        if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9_-]*[a-zA-Z0-9]$', username):
            errors.append("Kullanıcı adı sadece harf, rakam, alt çizgi ve tire içerebilir")
        
        return {"valid": len(errors) == 0, "errors": errors}

    def generate_email_verification_token(self) -> str:
        """E-posta doğrulama token'ı oluştur"""
        self.email_verification_token = secrets.token_urlsafe(32)
        self.email_verification_token_expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
        return self.email_verification_token
    
    def generate_password_reset_token(self) -> str:
        """Şifre sıfırlama token'ı oluştur"""
        self.password_reset_token = secrets.token_urlsafe(32)
        self.password_reset_token_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        return self.password_reset_token

    def is_email_verification_token_valid(self, token: str) -> bool:
        if not self.email_verification_token or self.email_verification_token != token:
            return False
        if not self.email_verification_token_expires_at:
            return False

        expires_at = self.email_verification_token_expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        return datetime.now(timezone.utc) < expires_at

    def is_password_reset_token_valid(self, token: str) -> bool:
        if not self.password_reset_token or self.password_reset_token != token:
            return False
        if not self.password_reset_token_expires_at:
            return False
        
        expires_at = self.password_reset_token_expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        
        return expires_at > datetime.now(timezone.utc)

    def is_account_locked(self) -> bool:
        if self.locked_until.tzinfo is None:
            self.locked_until = self.locked_until.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) < self.locked_until
