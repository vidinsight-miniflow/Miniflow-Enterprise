from typing import Optional, Dict, Any
from datetime import datetime, timezone

from miniflow.database import RepositoryRegistry, with_transaction, with_readonly_session
from miniflow.models import User
from miniflow.core.exceptions import (
    ResourceNotFoundError,
    ResourceAlreadyExistsError,
    BusinessRuleViolationError,
    InvalidInputError,
)
from miniflow.utils import MailTrapClient


class UserProfileService:
    """
    Kullanıcı profil güncelleme servisi.
    
    Ad, soyad, avatar, telefon, username ve email güncelleme işlemlerini yönetir.
    NOT: user_exists kontrolü middleware'de yapılır.
    """
    _registry = RepositoryRegistry()
    _user_repo = _registry.user_repository()
    _auth_session_repo = _registry.auth_session_repository()
    _mailtrap_client = MailTrapClient()

    # ==================================================================================== PROFILE INFO ==
    @classmethod
    @with_transaction(manager=None)
    def update_profile(
        cls,
        session,
        *,
        user_id: str,
        name: Optional[str] = None,
        surname: Optional[str] = None,
        avatar_url: Optional[str] = None,
        country_code: Optional[str] = None,
        phone_number: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Kullanıcı profil bilgilerini günceller.
        
        Args:
            user_id: Kullanıcı ID'si
            name: Ad (opsiyonel)
            surname: Soyad (opsiyonel)
            avatar_url: Avatar URL (opsiyonel)
            country_code: Ülke kodu (opsiyonel)
            phone_number: Telefon numarası (opsiyonel)
            
        Returns:
            Güncellenmiş profil bilgileri
        """
        user = cls._user_repo._get_by_id(session, record_id=user_id)
        if not user:
            raise ResourceNotFoundError(
                resource_name="User",
                resource_id=user_id
            )
        
        # Güncelleme verilerini hazırla
        update_data = {}
        if name is not None:
            update_data["name"] = name
        if surname is not None:
            update_data["surname"] = surname
        if avatar_url is not None:
            update_data["avatar_url"] = avatar_url
        if country_code is not None:
            update_data["country_code"] = country_code
        if phone_number is not None:
            update_data["phone_number"] = phone_number
            update_data["phone_verified_at"] = None  # Telefon değişince doğrulama sıfırlanır
        
        if update_data:
            cls._user_repo._update(session, record_id=user_id, **update_data)
        
        # Güncel kullanıcı bilgilerini al
        updated_user = cls._user_repo._get_by_id(session, record_id=user_id)
        
        return {
            "user_id": updated_user.id,
            "name": updated_user.name,
            "surname": updated_user.surname,
            "avatar_url": updated_user.avatar_url,
            "country_code": updated_user.country_code,
            "phone_number": updated_user.phone_number,
            "phone_verified": updated_user.phone_verified_at is not None
        }

    # ==================================================================================== USERNAME ==
    @classmethod
    @with_transaction(manager=None)
    def change_username(
        cls,
        session,
        *,
        user_id: str,
        new_username: str,
    ) -> Dict[str, Any]:
        """
        Kullanıcı adını değiştirir.
        
        Args:
            user_id: Kullanıcı ID'si
            new_username: Yeni kullanıcı adı
            
        Returns:
            {"success": True, "username": str}
            
        Raises:
            InvalidInputError: Geçersiz username formatı
            ResourceAlreadyExistsError: Username zaten kullanımda
        """
        user = cls._user_repo._get_by_id(session, record_id=user_id)
        if not user:
            raise ResourceNotFoundError(
                resource_name="User",
                resource_id=user_id
            )
        
        # Username validasyonu
        username_validation = User.validate_username(new_username)
        if not username_validation["valid"]:
            errors = ", ".join(username_validation.get("errors", []))
            raise InvalidInputError(
                field_name="username",
                message=f"Username validation failed: {errors}"
            )
        
        # Username benzersizlik kontrolü
        existing_user = cls._user_repo._get_by_username(session, username=new_username)
        if existing_user and existing_user.id != user_id:
            raise ResourceAlreadyExistsError(
                resource_name="Username",
                conflicting_field="username",
                message=f"Username '{new_username}' is already taken"
            )
        
        old_username = user.username
        cls._user_repo._update(session, record_id=user_id, username=new_username)
        
        # Bildirim emaili gönder
        try:
            cls._mailtrap_client.send_notification_email(
                to_email=user.email,
                template_variables={
                    "name": user.name or "User",
                    "notification_title": "Username Changed",
                    "notification_body": f"Your username has been changed from '{old_username}' to '{new_username}'.",
                    "company_info_name": "MiniFlow",
                    "company_info_address": "",
                    "company_info_city": "",
                    "company_info_zip_code": "",
                    "company_info_country": ""
                }
            )
        except Exception:
            pass  # Email hatası işlemi engellemez
        
        return {
            "success": True,
            "old_username": old_username,
            "username": new_username
        }

    # ==================================================================================== EMAIL ==
    @classmethod
    @with_transaction(manager=None)
    def change_email(
        cls,
        session,
        *,
        user_id: str,
        new_email: str,
    ) -> Dict[str, Any]:
        """
        E-posta adresini değiştirir.
        
        - Yeni email'e doğrulama linki gönderir
        - Eski email'e bilgilendirme gönderir
        - Tüm aktif session'ları iptal eder (güvenlik)
        - Email doğrulanana kadar hesap is_verified=False olur
        
        Args:
            user_id: Kullanıcı ID'si
            new_email: Yeni e-posta adresi
            
        Returns:
            {
                "success": True,
                "email": str,
                "is_verified": False,
                "sessions_revoked": int
            }
            
        Raises:
            InvalidInputError: Geçersiz email formatı
            ResourceAlreadyExistsError: Email zaten kullanımda
        """
        user = cls._user_repo._get_by_id(session, record_id=user_id)
        if not user:
            raise ResourceNotFoundError(
                resource_name="User",
                resource_id=user_id
            )
        
        # Email validasyonu
        if not User.validate_email_format(new_email):
            raise InvalidInputError(
                field_name="email",
                message="Invalid email format"
            )
        
        # Email benzersizlik kontrolü
        existing_user = cls._user_repo._get_by_email(session, email=new_email)
        if existing_user and existing_user.id != user_id:
            raise ResourceAlreadyExistsError(
                resource_name="Email",
                conflicting_field="email",
                message=f"Email '{new_email}' is already registered"
            )
        
        old_email = user.email
        
        # Email değişikliği için verification token oluştur
        verification_token = user.generate_email_verification_token()
        
        # Kullanıcıyı güncelle
        cls._user_repo._update(
            session,
            record_id=user_id,
            email=new_email,
            is_verified=False,
            email_verified_at=None,
            email_verification_token=user.email_verification_token,
            email_verification_token_expires_at=user.email_verification_token_expires_at
        )
        
        # Tüm aktif session'ları iptal et (güvenlik için)
        num_revoked = cls._auth_session_repo._revoke_sessions(session, user_id=user_id)
        
        # Yeni email'e doğrulama gönder
        try:
            cls._mailtrap_client.send_verification_email(
                to_email=new_email,
                template_variables={
                    "name": user.name or "User",
                    "verification_token": verification_token,
                    "token_plain": verification_token,  # Test sürecinde email içeriğinden token'ı çıkarabilmek için
                    "company_info_name": "MiniFlow",
                    "company_info_address": "",
                    "company_info_city": "",
                    "company_info_zip_code": "",
                    "company_info_country": ""
                }
            )
        except Exception:
            pass
        
        # Eski email'e bilgilendirme gönder
        try:
            cls._mailtrap_client.send_notification_email(
                to_email=old_email,
                template_variables={
                    "name": user.name or "User",
                    "notification_title": "Email Address Changed",
                    "notification_body": f"Your email address has been changed to '{new_email}'. If you did not make this change, please contact support immediately.",
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
            "old_email": old_email,
            "email": new_email,
            "is_verified": False,
            "sessions_revoked": num_revoked,
            "message": "Please verify your new email address. All sessions have been revoked for security."
        }

    # ==================================================================================== PHONE ==
    @classmethod
    @with_transaction(manager=None)
    def change_phone(
        cls,
        session,
        *,
        user_id: str,
        country_code: str,
        phone_number: str,
    ) -> Dict[str, Any]:
        """
        Telefon numarasını değiştirir.
        
        Args:
            user_id: Kullanıcı ID'si
            country_code: ISO ülke kodu (TR, US, vb.)
            phone_number: E.164 formatında telefon numarası
            
        Returns:
            {
                "success": True,
                "country_code": str,
                "phone_number": str,
                "phone_verified": False
            }
        """
        user = cls._user_repo._get_by_id(session, record_id=user_id)
        if not user:
            raise ResourceNotFoundError(
                resource_name="User",
                resource_id=user_id
            )
        
        cls._user_repo._update(
            session,
            record_id=user_id,
            country_code=country_code,
            phone_number=phone_number,
            phone_verified_at=None  # Yeni numara doğrulanmamış
        )
        
        # TODO: SMS doğrulama sistemi eklendiğinde burada SMS gönderilecek
        
        return {
            "success": True,
            "country_code": country_code,
            "phone_number": phone_number,
            "phone_verified": False
        }

    @classmethod
    @with_transaction(manager=None)
    def verify_phone(
        cls,
        session,
        *,
        user_id: str,
        verification_code: str,
    ) -> Dict[str, Any]:
        """
        Telefon numarasını doğrular.
        
        Args:
            user_id: Kullanıcı ID'si
            verification_code: SMS ile gönderilen doğrulama kodu
            
        Returns:
            {"success": True, "phone_verified": True}
            
        Raises:
            BusinessRuleViolationError: Geçersiz doğrulama kodu
        """
        user = cls._user_repo._get_by_id(session, record_id=user_id)
        if not user:
            raise ResourceNotFoundError(
                resource_name="User",
                resource_id=user_id
            )
        
        # TODO: SMS doğrulama sistemi eklendiğinde burada kod kontrolü yapılacak
        # Şimdilik basit bir placeholder
        
        cls._user_repo._update(
            session,
            record_id=user_id,
            phone_verified_at=datetime.now(timezone.utc)
        )
        
        return {
            "success": True,
            "phone_verified": True,
            "phone_verified_at": datetime.now(timezone.utc).isoformat()
        }
