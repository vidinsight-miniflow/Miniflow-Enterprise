from typing import Optional, Dict, Any
from datetime import datetime, timezone

from qbitra.domain.repositories import RepositoryRegistry
from qbitra.infrastructure.database import with_transaction
from qbitra.domain.models.user_models.user import User
from qbitra.core.qbitra_logger import get_logger
from qbitra.utils.helpers.crypto_helper import hash_password
from qbitra.utils.helpers.token_helper import is_token_expired, verify_hashed_token
from qbitra.core.exceptions.services import (
    RegistrationEmailAlreadyExistsError,
    RegistrationUsernameAlreadyExistsError,
    RegistrationInvalidEmailFormatError,
    RegistrationWeakPasswordError,
    RegistrationInvalidUsernameError,
    EmailVerificationTokenNotFoundError,
    EmailVerificationTokenInvalidError,
    EmailAlreadyVerifiedError,
)

# Domain servis logger'ı (logs/services/Auth Service/service.log)
logger = get_logger("Auth Service", parent_folder="services")


class RegistrationService:
    _user_repo = RepositoryRegistry().user_repository
    
    @classmethod
    @with_transaction(manager=None)
    def register_user(cls, session, *, username: str, email: str, password: str, name: str, surname: str,
                    country_code: Optional[str] = None, phone_number: Optional[str] = None ) -> Dict[str, Any]:
        
        logger.info("Kullanıcı kaydı başlatıldı", extra={"username": username, "email": email})

        if not User.validate_email_format(email):
            logger.warning("Geçersiz e-posta formatı", extra={"email": email})
            raise RegistrationInvalidEmailFormatError(email=email)

        password_validation = User.validate_password_strength(password)
        if not password_validation["valid"]:
            logger.warning("Zayıf şifre", extra={"username": username, "errors": password_validation["errors"]})
            raise RegistrationWeakPasswordError(errors=password_validation["errors"])

        username_validation = User.validate_username(username)
        if not username_validation["valid"]:
            logger.warning("Geçersiz kullanıcı adı", extra={"username": username, "errors": username_validation["errors"]})
            raise RegistrationInvalidUsernameError(username=username, errors=username_validation["errors"])

        existing_user_by_email = cls._user_repo.get_by_email(session, email=email,include_deleted=False)
        if existing_user_by_email:
            logger.warning("E-posta zaten kayıtlı", extra={"email": email})
            raise RegistrationEmailAlreadyExistsError(email=email)

        existing_user_by_username = cls._user_repo.get_by_username(session, username=username, include_deleted=False)
        if existing_user_by_username:
            logger.warning("Kullanıcı adı zaten kullanımda",extra={"username": username})
            raise RegistrationUsernameAlreadyExistsError(username=username)

        hashed_password = hash_password(password)
        user = cls._user_repo.create(
            session,
            username=username,
            email=email,
            password=hashed_password,
            name=name,
            surname=surname,
            country_code=country_code,
            phone_number=phone_number,
        )

        original_token = user.generate_email_verification_token()
        session.flush()

        # TODO: E-posta doğrulama e-postası gönder

        logger.info("Kullanıcı kaydı tamamlandı", extra={"user_id": user.id, "username": username, "email": email})

        return {
            "message": "User registered successfully",
            "data": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "email_verified": user.email_verified,
                "email_verification_token": original_token,
            }
        }

    @classmethod
    @with_transaction(manager=None)
    def verify_email(cls, session, *, verification_token: str) -> Dict[str, Any]:
        
        logger.info("E-posta doğrulama işlemi başlatıldı")
        
        user = cls._user_repo.get_by_email_verification_token(session, token=verification_token,include_deleted=False)
        if not user:
            logger.warning("Doğrulama tokeni bulunamadı")
            raise EmailVerificationTokenNotFoundError()

        if user.email_verified:
            logger.warning("E-posta zaten doğrulanmış", extra={"user_id": user.id, "email": user.email})
            raise EmailAlreadyVerifiedError(email=user.email)

        if not user.email_verification_token or not user.email_verification_token_expires_at:
            logger.warning("Token bilgisi eksik", extra={"user_id": user.id})
            raise EmailVerificationTokenInvalidError()

        if verify_hashed_token(verification_token, user.email_verification_token):
            if is_token_expired(user.email_verification_token_expires_at):
                logger.info("Token süresi dolmuş, yeni token otomatik gönderiliyor", extra={"user_id": user.id, "email": user.email})
                original_token = user.generate_email_verification_token()
                session.flush()

                # TODO: E-posta doğrulama e-postası gönder

                return {
                    "message": "Token expired. A new verification email has been sent to your email address.",
                    "data": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "email_verified": user.email_verified,
                        "email_verification_token": original_token
                    }
                }

            user.email_verified = True
            user.email_verified_at = datetime.now(timezone.utc)
            user.email_verification_token = None
            user.email_verification_token_expires_at = None
            session.flush()

            logger.info("E-posta doğrulama tamamlandı", extra={"user_id": user.id, "email": user.email})

            # TODO: Hoş geldin e-postası gönder

            return {
                "message": "Email verified successfully",
                "data": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "email_verified": user.email_verified,
                }
            }
            
        else:
            logger.warning("Token doğrulama başarısız (hash eşleşmedi)", extra={"user_id": user.id})
            raise EmailVerificationTokenInvalidError()

    @classmethod
    @with_transaction(manager=None)
    def resend_verification_email(cls, session, *, email: str) -> Dict[str, Any]:
        logger.info("E-posta doğrulama e-postası yeniden gönderimi başlatıldı", extra={"email": email})

        user = cls._user_repo.get_by_email(session, email=email, include_deleted=False) 
        if not user:
            logger.warning("E-posta bulunamadı (security: generic response)", extra={"email": email})
            return {
                "message": "E-posta bulunamadı, doğrulama e-postası yeniden gönderilmedi",
                "data": {
                    "email": email,
                    "email_verified": False,
                }
            }

        if user.email_verified:
            logger.warning("E-posta zaten doğrulanmış", extra={"user_id": user.id, "email": email})
            raise EmailAlreadyVerifiedError(email=email)

        original_token = user.generate_email_verification_token()
        session.flush()

        # TODO: Doğrulama e-postası yeniden gönder

        return {
            "message": "Verification email sent successfully",
            "data": {
                "email": email,
                "email_verified": user.email_verified,
                "email_verification_token": original_token
            }
        }
