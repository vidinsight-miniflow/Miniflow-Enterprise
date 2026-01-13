import re
from typing import Dict
from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, Index, UniqueConstraint

from qbitra.infrastructure.database.models import BaseModel
from qbitra.utils.helpers.token_helper import (
    generate_email_verification_token,
    get_email_verification_expires_at,
    verify_hashed_token,
    is_token_expired,
    generate_password_reset_token,
    get_password_reset_expires_at,
)


class User(BaseModel):
    __prefix__ = "USR"
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint('username', name='_user_username_unique'),
        UniqueConstraint('email', name='_user_email_unique'),
        Index('idx_user_email', 'email'),
        Index('idx_user_username', 'username'),
    )

    # ---- User Authentication Information ---- #
    username = Column(String(100), nullable=False, unique=True, index=True, 
    comment="Kullanıcı adı")
    email = Column(String(100), nullable=False, unique=True, index=True, 
    comment="E-posta adresi")
    password = Column(String(100), nullable=False, 
    comment="Kullanıcı şifresi")
    is_admin = Column(Boolean, default=False, nullable=False, index=True,
    comment="Kullanıcı admin mi?")

    # ---- User Information ---- #
    name = Column(String(100), nullable=False, 
    comment="Kullanıcı adı")
    surname = Column(String(100), nullable=False, 
    comment="Kullanıcı soyadı")
    country_code = Column(String(2), nullable=True, 
    comment="ISO ülke kodu")
    phone_number = Column(String(20), nullable=True, unique=True, index=True,
    comment="E.164 formatı: +905551234567")

    # ---- User Information Verification Status ---- #
    email_verified = Column(Boolean, default=False, nullable=False, index=True,
    comment="E-posta doğrulanmış mı?")
    email_verified_at = Column(DateTime(timezone=True), nullable=True, 
    comment="E-posta doğrulama tarihi")
    phone_verified = Column(Boolean, default=False, nullable=False, index=True,
    comment="Telefon doğrulanmış mı?")
    phone_verified_at = Column(DateTime(timezone=True), nullable=True, 
    comment="Telefon doğrulama tarihi")

    # ---- User Information Verification Tokens ---- #
    email_verification_token = Column(String(100), nullable=True, index=True,
    comment="E-posta doğrulama tokeni")
    email_verification_token_expires_at = Column(DateTime(timezone=True), nullable=True, 
    comment="E-posta doğrulama tokeni süresi")
    phone_verification_token = Column(String(100), nullable=True, 
    comment="Telefon doğrulama tokeni")
    phone_verification_token_expires_at = Column(DateTime(timezone=True), nullable=True, 
    comment="Telefon doğrulama tokeni süresi")
    password_reset_token = Column(String(100), nullable=True, index=True,
    comment="Şifre sıfırlama tokeni")
    password_reset_token_expires_at = Column(DateTime(timezone=True), nullable=True, 
    comment="Şifre sıfırlama tokeni süresi")

    # ---- User Account Suspension Status ---- #
    is_suspended = Column(Boolean, default=False, nullable=False, index=True,
    comment="Kullanıcı hesabı askıya alındı mı?")
    suspended_at = Column(DateTime(timezone=True), nullable=True, 
    comment="Kullanıcı hesabı askıya alındığı tarih")
    suspended_reason = Column(Text, nullable=True, 
    comment="Kullanıcı hesabı askıya alındığı nedeni")
    suspension_expires_at = Column(DateTime(timezone=True), nullable=True, 
    comment="Kullanıcı hesabı askıya alındığı süre sonu")

    # ---- User Account Lock Status ---- #
    is_locked = Column(Boolean, default=False, nullable=False, index=True,
    comment="Kullanıcı hesabı kilitlendi mi?")
    locked_at = Column(DateTime(timezone=True), nullable=True, 
    comment="Kullanıcı hesabı kilitlendiği tarih")
    locked_reason = Column(Text, nullable=True, 
    comment="Kullanıcı hesabı kilitlendiği nedeni")
    lock_expires_at = Column(DateTime(timezone=True), nullable=True, 
    comment="Kullanıcı hesabı kilitlendiği süre sonu")

    # ---- Relationships ---- #
    auth_sessions = relationship("AuthSession", foreign_keys="AuthSession.user_id", back_populates="user")
    login_history = relationship("LoginHistory", back_populates="user")

    # ---- Helper Methods ---- #
    @property
    def full_name(self) -> str:
        return f"{self.name} {self.surname}"

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

    # ============================================================================
    # Token Generation and Verification Methods
    # ============================================================================

    def generate_email_verification_token(self) -> str:
        """
        Generate email verification token and store hashed version in database.
        
        Returns:
            str: Original token to be sent via email (not hashed)
        """
        original_token, hashed_token = generate_email_verification_token()
        self.email_verification_token = hashed_token
        self.email_verification_token_expires_at = get_email_verification_expires_at()
        return original_token

    def generate_password_reset_token(self) -> str:
        """
        Generate password reset token and store hashed version in database.
        
        Returns:
            str: Original token to be sent via email (not hashed)
        """
        original_token, hashed_token = generate_password_reset_token()
        self.password_reset_token = hashed_token
        self.password_reset_token_expires_at = get_password_reset_expires_at()
        return original_token

    def verify_password_reset_token(self, token: str) -> bool:
        """Verify password reset token."""
        if not self.password_reset_token:
            return False
        
        if not self.password_reset_token_expires_at:
            return False
        
        if is_token_expired(self.password_reset_token_expires_at):
            return False
        
        return verify_hashed_token(token, self.password_reset_token)