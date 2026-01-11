from typing import Optional, Dict, List, Any
from datetime import datetime, timezone

from miniflow.database import RepositoryRegistry, with_transaction, with_readonly_session
from miniflow.models import User
from miniflow.core.exceptions import (
    ResourceNotFoundError,
    ResourceAlreadyExistsError,
    BusinessRuleViolationError,
    InvalidInputError,
)
from miniflow.core.logger import get_logger, log_function_call
from miniflow.utils.helpers.encryption_helper import hash_password, hash_data
from miniflow.utils import MailTrapClient

# Logger instance
logger = get_logger(__name__)


class RegisterService:
    """
    Kullanıcı kayıt işlemleri servis katmanı.
    
    Yeni kullanıcı kaydı, email doğrulama işlemlerini yönetir.
    """
    _registry = RepositoryRegistry()
    _user_repo = _registry.user_repository()
    _agreement_version_repo = _registry.agreement_version_repository()
    _user_agreement_repo = _registry.user_agreement_acceptance_repository()
    _mailtrap_client = MailTrapClient()

    # ==================================================================================== REGISTER ==
    @classmethod
    @log_function_call
    @with_transaction(manager=None)
    def register_user(
        cls,
        session,
        *,
        username: str,
        email: str,
        password: str,
        name: Optional[str] = None,
        surname: Optional[str] = None,
        marketing_consent: bool = False,
        terms_accepted_version_id: str,
        privacy_policy_accepted_version_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Yeni kullanıcı kaydı oluşturur.
        
        Args:
            username: Kullanıcı adı
            email: E-posta adresi
            password: Şifre
            name: Ad (opsiyonel)
            surname: Soyad (opsiyonel)
            marketing_consent: Pazarlama izni
            terms_accepted_version_id: Kabul edilen kullanım şartları versiyon ID'si
            privacy_policy_accepted_version_id: Kabul edilen gizlilik politikası versiyon ID'si
            ip_address: IP adresi (opsiyonel)
            user_agent: User agent (opsiyonel)
            
        Returns:
            {
                "id": str,
                "username": str,
                "email": str,
                "is_verified": bool
            }
            
        Raises:
            InvalidInputError: Geçersiz email/şifre/kullanıcı adı formatı
            BusinessRuleViolationError: Sözleşme versiyonu bulunamadı
            ResourceAlreadyExistsError: Email veya kullanıcı adı zaten mevcut
        """
        logger.info(f"User registration attempt: username={username}, email={email}, ip: {ip_address}")
        
        # Validasyonlar
        if not User.validate_email_format(email):
            logger.warning(f"Registration failed: Invalid email format - email={email}")
            raise InvalidInputError(
                field_name="email",
                message="Invalid email format"
            )
        
        password_validation = User.validate_password_strength(password)
        if not password_validation["valid"]:
            errors = ", ".join(password_validation.get("errors", []))
            logger.warning(f"Registration failed: Password validation failed - username={username}, email={email}")
            raise InvalidInputError(
                field_name="password",
                message=f"Password requirements not met: {errors}"
            )
        
        username_validation = User.validate_username(username)
        if not username_validation["valid"]:
            errors = ", ".join(username_validation.get("errors", []))
            logger.warning(f"Registration failed: Username validation failed - username={username}, email={email}")
            raise InvalidInputError(
                field_name="username",
                message=f"Username validation failed: {errors}"
            )
        
        # Sözleşme versiyonlarını doğrula
        terms_version = cls._agreement_version_repo._get_by_id(
            session, 
            record_id=terms_accepted_version_id
        )
        if not terms_version:
            raise BusinessRuleViolationError(
                rule_name="invalid_terms_version",
                rule_detail=f"Terms version {terms_accepted_version_id} not found",
                message="Invalid terms of service version"
            )
        
        privacy_version = cls._agreement_version_repo._get_by_id(
            session, 
            record_id=privacy_policy_accepted_version_id
        )
        if not privacy_version:
            raise BusinessRuleViolationError(
                rule_name="invalid_privacy_version",
                rule_detail=f"Privacy policy version {privacy_policy_accepted_version_id} not found",
                message="Invalid privacy policy version"
            )
        
        # Email kontrolü - zaten kullanılıyor mu?
        existing_user_by_email = cls._user_repo._get_by_email(session, email=email, include_deleted=False)
        if existing_user_by_email:
            logger.warning(f"Registration failed: Email already exists - email={email}, ip: {ip_address}")
            raise ResourceAlreadyExistsError(
                resource_name="user",
                conflicting_field="email",
                message="Email address is already registered"
            )
        
        # Username kontrolü - zaten kullanılıyor mu?
        existing_user_by_username = cls._user_repo._get_by_username(session, username=username, include_deleted=False)
        if existing_user_by_username:
            logger.warning(f"Registration failed: Username already exists - username={username}, ip: {ip_address}")
            raise ResourceAlreadyExistsError(
                resource_name="user",
                conflicting_field="username",
                message="Username is already taken"
            )
        
        # Şifreyi hashle
        hashed_password = hash_password(password)
        
        # Kullanıcı oluştur
        user = cls._user_repo._create(
            session,
            username=username,
            email=email,
            hashed_password=hashed_password,
            password_changed_at=datetime.now(timezone.utc),
            name=name,
            surname=surname,
            marketing_consent=marketing_consent,
            marketing_consent_at=datetime.now(timezone.utc) if marketing_consent else None,
            created_by="SYSTEM"
        )
        
        # Email doğrulama token'ı oluştur
        user.generate_email_verification_token()
        
        logger.debug(f"User created: user_id={user.id}, username={username}, email={email}")
        
        # Sözleşme kabullerini kaydet
        ip_hash = hash_data(ip_address) if ip_address else None
        ua_hash = hash_data(user_agent) if user_agent else None
        
        for version_id in [terms_accepted_version_id, privacy_policy_accepted_version_id]:
            cls._user_agreement_repo._create(
                session,
                user_id=user.id,
                agreement_version_id=version_id,
                accepted_at=datetime.now(timezone.utc),
                ip_address_hash=ip_hash,
                user_agent_hash=ua_hash,
                acceptance_method="web",
                locale="tr-TR",
                acceptance_metadata={},
                created_by=user.id
            )
        
        # Doğrulama emaili gönder
        cls._send_verification_email(user.email, user.name, f"https://qbitra.vidinsight.com.tr/verify-email?token={user.email_verification_token}")
        
        logger.info(f"User registration successful: user_id={user.id}, username={username}, email={email}, ip: {ip_address}")
        
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_verified": user.is_verified
        }

    # ==================================================================================== EMAIL VERIFICATION ==
    @classmethod
    @with_transaction(manager=None)
    def verify_email(
        cls,
        session,
        *,
        verification_token: str
    ) -> Dict[str, Any]:
        """
        Email doğrulama token'ını kullanarak email'i doğrular.
        
        Args:
            verification_token: Doğrulama token'ı
            
        Returns:
            {
                "id": str,
                "username": str,
                "email": str,
                "is_verified": bool
            }
            
        Raises:
            BusinessRuleViolationError: Geçersiz/süresi dolmuş token, zaten doğrulanmış
        """
        user = cls._user_repo._get_by_email_verification_token(
            session, 
            token=verification_token
        )
        
        if not user:
            raise BusinessRuleViolationError(
                rule_name="invalid_verification_token",
                rule_detail="Verification token not found or invalid",
                message="Invalid or expired verification token"
            )
        
        if not user.is_email_verification_token_valid(verification_token):
            raise BusinessRuleViolationError(
                rule_name="verification_token_expired",
                rule_detail=f"Verification token expired at {user.email_verification_token_expires_at.isoformat() if user.email_verification_token_expires_at else 'unknown'}",
                message="Verification token has expired. Please request a new one"
            )
        
        if user.is_verified:
            raise BusinessRuleViolationError(
                rule_name="already_verified",
                rule_detail="Email address has already been verified",
                message="Email is already verified"
            )
        
        # Email'i doğrula
        cls._user_repo._update(
            session,
            record_id=user.id,
            is_verified=True,
            email_verified_at=datetime.now(timezone.utc),
            email_verification_token=None,
            email_verification_token_expires_at=None
        )
        
        # Hoş geldin emaili gönder
        cls._send_welcome_email(user.email, user.name)
        
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_verified": True
        }

    @classmethod
    @with_transaction(manager=None)
    def resend_verification_email(
        cls,
        session,
        *,
        email: str
    ) -> Dict[str, Any]:
        """
        Email doğrulama emailini yeniden gönderir.
        
        Güvenlik: Email enumeration saldırılarına karşı koruma sağlar.
        Kullanıcı bulunamazsa veya zaten doğrulanmışsa da başarılı response döner.
        
        Args:
            email: E-posta adresi
            
        Returns:
            {"email": str, "message": str}
        """
        user = cls._user_repo._get_by_email(session, email=email)
        
        # Güvenlik: Kullanıcı bulunamazsa bile aynı response
        if not user:
            return {
                "email": email,
                "message": "If an account exists, a verification email has been sent"
            }
        
        # Zaten doğrulanmış
        if user.is_verified:
            return {
                "email": email,
                "message": "If an account exists, a verification email has been sent"
            }
        
        # Yeni token oluştur
        user.generate_email_verification_token()
        
        # Doğrulama emaili gönder
        cls._send_verification_email(user.email, user.name, f"https://qbitra.vidinsight.com.tr/verify-email?token={user.email_verification_token}")
        
        return {
            "email": email,
            "message": "If an account exists, a verification email has been sent"
        }

    # ==================================================================================== HELPERS ==
    @classmethod
    def _send_verification_email(cls, email: str, name: Optional[str], token: str) -> None:
        """Email doğrulama emaili gönderir."""
        try:
            cls._mailtrap_client.send_verification_email(
                to_email=email,
                template_variables={
                    "name": name or "User",
                    "verification_token": token,
                    "token_plain": token,  # Test sürecinde email içeriğinden token'ı çıkarabilmek için
                    "company_info_name": "MiniFlow",
                    "company_info_address": "",
                    "company_info_city": "",
                    "company_info_zip_code": "",
                    "company_info_country": ""
                }
            )
        except Exception:
            # Email gönderim hatası kayıt işlemini engellememeli
            pass

    @classmethod
    def _send_welcome_email(cls, email: str, name: Optional[str]) -> None:
        """Hoş geldin emaili gönderir."""
        try:
            cls._mailtrap_client.send_welcome_email(
                to_email=email,
                template_variables={
                    "name": name or "User",
                    "company_info_name": "MiniFlow",
                    "company_info_address": "",
                    "company_info_city": "",
                    "company_info_zip_code": "",
                    "company_info_country": ""
                }
            )
        except Exception:
            pass
