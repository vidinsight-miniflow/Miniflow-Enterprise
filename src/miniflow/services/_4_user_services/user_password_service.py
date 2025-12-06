from typing import Optional, Dict, Any
from datetime import datetime, timezone

from miniflow.database import RepositoryRegistry, with_transaction, with_readonly_session
from miniflow.models import User
from miniflow.models.enums import PasswordChangeReason
from miniflow.core.exceptions import (
    ResourceNotFoundError,
    BusinessRuleViolationError,
    InvalidInputError,
)
from miniflow.utils.helpers.encryption_helper import hash_password, verify_password
from miniflow.utils import ConfigurationHandler, MailTrapClient


class UserPasswordService:
    """
    Kullanıcı şifre işlemleri servisi.
    
    Şifre değiştirme, sıfırlama ve şifre geçmişi yönetimini yönetir.
    NOT: user_exists kontrolü middleware'de yapılır.
    """
    _registry = RepositoryRegistry()
    _user_repo = _registry.user_repository()
    _password_history_repo = _registry.password_history_repository()
    _auth_session_repo = _registry.auth_session_repository()
    _mailtrap_client = MailTrapClient()
    
    # Konfigürasyon
    _max_password_history_count = ConfigurationHandler.get_int("AUTH", "max_password_history_count", 5)

    # ==================================================================================== CHANGE PASSWORD ==
    @classmethod
    @with_transaction(manager=None)
    def change_password(
        cls,
        session,
        *,
        user_id: str,
        old_password: str,
        new_password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Kullanıcı şifresini değiştirir (eski şifre doğrulaması ile).
        
        Args:
            user_id: Kullanıcı ID'si
            old_password: Mevcut şifre
            new_password: Yeni şifre
            ip_address: IP adresi (opsiyonel)
            user_agent: User agent (opsiyonel)
            
        Returns:
            {"success": True, "message": str}
            
        Raises:
            BusinessRuleViolationError: Eski şifre yanlış, şifre tekrar kullanımı
            InvalidInputError: Yeni şifre politikaya uymuyor
        """
        user = cls._user_repo._get_by_id(session, record_id=user_id)
        if not user:
            raise ResourceNotFoundError(
                resource_name="User",
                resource_id=user_id
            )
        
        # Eski şifre doğrulama
        if not verify_password(old_password, user.hashed_password):
            raise BusinessRuleViolationError(
                rule_name="invalid_password",
                message="Current password is incorrect"
            )
        
        # Yeni şifre validasyonu
        password_validation = User.validate_password_strength(new_password)
        if not password_validation["valid"]:
            errors = ", ".join(password_validation.get("errors", []))
            raise InvalidInputError(
                field_name="new_password",
                message=f"Password requirements not met: {errors}"
            )
        
        # Yeni şifreyi hash'le
        new_password_hash = hash_password(new_password)
        
        # Şifre tekrar kullanımı kontrolü
        if cls._password_history_repo._check_password_reuse(
            session, 
            user_id=user_id, 
            password_hash=new_password_hash, 
            last_n=cls._max_password_history_count
        ):
            raise BusinessRuleViolationError(
                rule_name="password_reuse_not_allowed",
                message=f"You cannot reuse any of your last {cls._max_password_history_count} passwords"
            )
        
        # Eski şifreyi history'ye kaydet
        old_password_hash = user.hashed_password
        if old_password_hash:
            cls._password_history_repo._create(
                session,
                user_id=user_id,
                password_hash=old_password_hash,
                change_reason=PasswordChangeReason.VOLUNTARY.value,
                changed_from_ip=ip_address,
                changed_from_device=user_agent,
                created_by=user_id
            )
            
            # Eski kayıtları temizle
            cls._password_history_repo._cleanup_old_passwords(
                session,
                user_id=user_id,
                max_count=cls._max_password_history_count
            )
        
        # Yeni şifreyi güncelle
        cls._user_repo._update(
            session,
            record_id=user_id,
            hashed_password=new_password_hash,
            password_changed_at=datetime.now(timezone.utc)
        )
        
        # Bildirim emaili gönder
        try:
            cls._mailtrap_client.send_notification_email(
                to_email=user.email,
                template_variables={
                    "name": user.name or "User",
                    "notification_title": "Password Changed",
                    "notification_body": "Your password has been changed successfully. If you did not make this change, please contact support immediately.",
                    "company_info_name": "MiniFlow",
                    "company_info_address": "",
                    "company_info_city": "",
                    "company_info_zip_code": "",
                    "company_info_country": ""
                }
            )
        except Exception:
            pass
        
        return {
            "success": True,
            "message": "Password changed successfully"
        }

    # ==================================================================================== FORGOT PASSWORD ==
    @classmethod
    @with_transaction(manager=None)
    def send_password_reset_email(
        cls,
        session,
        *,
        email: str,
    ) -> Dict[str, Any]:
        """
        Şifre sıfırlama emaili gönderir.
        
        Güvenlik: Email bulunamazsa da aynı response döner (enumeration koruması).
        
        Args:
            email: E-posta adresi
            
        Returns:
            {"success": True, "message": str}
        """
        user = cls._user_repo._get_by_email(session, email=email)
        
        if user:
            # Token oluştur
            user.generate_password_reset_token()
            
            # Email gönder
            try:
                cls._mailtrap_client.send_password_reset_email(
                    to_email=user.email,
                    template_variables={
                        "name": user.name or "User",
                        "password_reset_token": user.password_reset_token,
                        "company_info_name": "MiniFlow",
                        "company_info_address": "",
                        "company_info_city": "",
                        "company_info_zip_code": "",
                        "company_info_country": ""
                    }
                )
            except Exception:
                pass
        
        # Güvenlik: Her zaman aynı mesaj
        return {
            "success": True,
            "message": "If an account with that email exists, a password reset link has been sent."
        }

    @classmethod
    @with_readonly_session(manager=None)
    def validate_password_reset_token(
        cls,
        session,
        *,
        token: str,
    ) -> Dict[str, Any]:
        """
        Şifre sıfırlama token'ını doğrular.
        
        Args:
            token: Şifre sıfırlama token'ı
            
        Returns:
            {"valid": True}
            
        Raises:
            BusinessRuleViolationError: Geçersiz veya süresi dolmuş token
        """
        user = cls._user_repo._get_by_password_reset_token(session, token=token)
        
        if not user:
            raise BusinessRuleViolationError(
                rule_name="invalid_reset_token",
                message="Invalid or expired password reset token"
            )
        
        if not user.is_password_reset_token_valid(token):
            raise BusinessRuleViolationError(
                rule_name="reset_token_expired",
                message="Password reset token has expired"
            )
        
        return {
            "valid": True
        }

    @classmethod
    @with_transaction(manager=None)
    def reset_password(
        cls,
        session,
        *,
        token: str,
        new_password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Token kullanarak şifreyi sıfırlar.
        
        Args:
            token: Şifre sıfırlama token'ı
            new_password: Yeni şifre
            ip_address: IP adresi (opsiyonel)
            user_agent: User agent (opsiyonel)
            
        Returns:
            {"success": True, "message": str}
            
        Raises:
            BusinessRuleViolationError: Geçersiz token, şifre tekrar kullanımı
            InvalidInputError: Şifre politikaya uymuyor
        """
        user = cls._user_repo._get_by_password_reset_token(session, token=token)
        
        if not user:
            raise BusinessRuleViolationError(
                rule_name="invalid_reset_token",
                message="Invalid or expired password reset token"
            )
        
        if not user.is_password_reset_token_valid(token):
            raise BusinessRuleViolationError(
                rule_name="reset_token_expired",
                message="Password reset token has expired"
            )
        
        # Yeni şifre validasyonu
        password_validation = User.validate_password_strength(new_password)
        if not password_validation["valid"]:
            errors = ", ".join(password_validation.get("errors", []))
            raise InvalidInputError(
                field_name="new_password",
                message=f"Password requirements not met: {errors}"
            )
        
        # Yeni şifreyi hash'le
        new_password_hash = hash_password(new_password)
        
        # Şifre tekrar kullanımı kontrolü
        if cls._password_history_repo._check_password_reuse(
            session, 
            user_id=user.id, 
            password_hash=new_password_hash, 
            last_n=cls._max_password_history_count
        ):
            raise BusinessRuleViolationError(
                rule_name="password_reuse_not_allowed",
                message=f"You cannot reuse any of your last {cls._max_password_history_count} passwords"
            )
        
        # Eski şifreyi history'ye kaydet
        old_password_hash = user.hashed_password
        if old_password_hash:
            cls._password_history_repo._create(
                session,
                user_id=user.id,
                password_hash=old_password_hash,
                change_reason=PasswordChangeReason.RESET.value,
                changed_from_ip=ip_address,
                changed_from_device=user_agent,
                created_by=user.id
            )
            
            cls._password_history_repo._cleanup_old_passwords(
                session,
                user_id=user.id,
                max_count=cls._max_password_history_count
            )
        
        # Şifreyi güncelle ve token'ı temizle
        cls._user_repo._update(
            session,
            record_id=user.id,
            hashed_password=new_password_hash,
            password_changed_at=datetime.now(timezone.utc),
            password_reset_token=None,
            password_reset_token_expires_at=None
        )
        
        # Tüm session'ları iptal et (güvenlik için)
        cls._auth_session_repo._revoke_sessions(session, user_id=user.id)
        
        # Bildirim emaili gönder
        try:
            cls._mailtrap_client.send_notification_email(
                to_email=user.email,
                template_variables={
                    "name": user.name or "User",
                    "notification_title": "Password Reset Successful",
                    "notification_body": "Your password has been reset successfully. All active sessions have been logged out for security. If you did not make this change, please contact support immediately.",
                    "company_info_name": "MiniFlow",
                    "company_info_address": "",
                    "company_info_city": "",
                    "company_info_zip_code": "",
                    "company_info_country": ""
                }
            )
        except Exception:
            pass
        
        return {
            "success": True,
            "message": "Password reset successfully. Please login with your new password."
        }

    # ==================================================================================== PASSWORD HISTORY ==
    @classmethod
    @with_readonly_session(manager=None)
    def get_password_history(
        cls,
        session,
        *,
        user_id: str,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """
        Kullanıcının şifre değişiklik geçmişini getirir.
        
        Args:
            user_id: Kullanıcı ID'si
            limit: Maksimum kayıt sayısı
            
        Returns:
            {
                "user_id": str,
                "total_records": int,
                "history": List[Dict]
            }
        """
        user = cls._user_repo._get_by_id(session, record_id=user_id)
        if not user:
            raise ResourceNotFoundError(
                resource_name="User",
                resource_id=user_id
            )
        
        password_history = cls._password_history_repo._get_by_user_id(
            session,
            user_id=user_id,
            last_n=limit
        )
        
        return {
            "user_id": user_id,
            "total_records": len(password_history),
            "history": [
                {
                    "id": record.id,
                    "change_reason": record.change_reason,
                    "changed_from_ip": record.changed_from_ip,
                    "changed_from_device": record.changed_from_device,
                    "created_at": record.created_at.isoformat() if record.created_at else None
                }
                for record in password_history
            ]
        }
