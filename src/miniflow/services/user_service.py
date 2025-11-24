from typing import Dict, Optional, Any
from datetime import datetime, timezone, timedelta

from src.miniflow.database import with_transaction, with_readonly_session
from src.miniflow.database import DatabaseManager, RepositoryRegistry
from ..database.models.enums import PasswordChangeReason
from src.miniflow.database.models import User

from src.miniflow.core.exceptions import BusinessRuleViolationError, InvalidInputError, DatabaseValidationError
from src.miniflow.utils.helpers.encryption_helper import hash_password, hash_data, verify_password
from src.miniflow.utils.helpers.jwt_helper import create_access_token, create_refresh_token, validate_access_token, validate_refresh_token, is_token_valid
from src.miniflow.utils import ConfigurationHandler, MailTrapClient


class UserService:
    def __init__(self):
        self._db_manager: DatabaseManager = DatabaseManager()
        self._registry: RepositoryRegistry = RepositoryRegistry()
        self._mailtrap_client: MailTrapClient = MailTrapClient()
        
        self._user_repo = self._registry.user_repository
        self._auth_session_repo = self._registry.auth_session_repository
        self._login_history_repo = self._registry.login_history_repository
        self._password_history_repo = self._registry.password_history_repository
        self._agreement_version_repo = self._registry.agreement_version_repository
        self._user_agreement_repo = self._registry.user_agreement_acceptance_repository

        self.max_failed_attempts = ConfigurationHandler.get_int("AUTH", "max_failed_attempts", 5)
        self.lockout_duration_minutes = ConfigurationHandler.get_int("AUTH", "lockout_duration_minutes", 15)
        self.rate_limit_window_minutes = ConfigurationHandler.get_int("AUTH", "rate_limit_window_minutes", 5)
        self.max_password_history_count = ConfigurationHandler.get_int("AUTH", "max_password_history_count", 3)


    @with_readonly_session(manager=None)
    def get_user(
        self,
        session,
        *,
        user_id: str,
    ) -> Dict[str, Any]:
        user = self._user_repo._get_by_id(session, record_id=user_id, include_deleted=False)
        if not user:
            raise BusinessRuleViolationError(
                rule_name="user_not_found",
                rule_detail="user not found",
                message="User not found"
            )
        
        return user.to_dict(exclude_fields=[
            "hashed_password", 
            "password_reset_token",
            "password_reset_token_expires_at", 
            "email_verification_token", 
            "email_verification_token_expires_at",
            "is_superadmin"
        ])


    @with_readonly_session(manager=None)
    def get_active_user_sessions(
        self,
        session,
        *,
        user_id: str,
    ) -> Dict[str, Any]:
        user = self._user_repo._get_by_id(session, record_id=user_id, include_deleted=False)
        if not user:
            raise BusinessRuleViolationError(
                rule_name="user_not_found",
                rule_detail="user not found",
                message="User not found"
            )
        
        active_sessions = self._auth_session_repo._get_all_active_user_sessions(session, user_id=user_id, include_deleted=False)
        
        payload = {
            "user_id": user_id,
            "active_sessions": len(active_sessions),
            "sessions": {}
        }

        for auth_session in active_sessions:
            payload["sessions"][auth_session.id] = {
                "device_name": auth_session.device_name,
                "device_type": auth_session.device_type,
                "user_agent": auth_session.user_agent,
                "ip_address": auth_session.ip_address,
                "country": auth_session.country,
                "city": auth_session.city,
                "last_activity_at": auth_session.last_activity_at.isoformat() if auth_session.last_activity_at else None,
                "total_requests": auth_session.total_requests,
            }

        return payload

    @with_transaction(manager=None)
    def revoke_specific_session(
        self,
        session,
        *,
        user_id: str,
        session_id: str,
    ) -> Dict[str, Any]:
        user = self._user_repo._get_by_id(session, record_id=user_id, include_deleted=False)
        if not user:
            raise BusinessRuleViolationError(
                rule_name="user_not_found",
                rule_detail="user not found",
                message="User not found"
            )
        
        revoked_session = self._auth_session_repo._revoke_specific_session(
            session,
            session_id=session_id,
            user_id=user_id
        )
        
        if not revoked_session:
            raise BusinessRuleViolationError(
                rule_name="session_not_found_or_already_revoked",
                rule_detail="session not found or already revoked",
                message="Session not found or already revoked"
            )
        
        return {
            "user_id": user_id,
            "session_id": session_id,
            "success": True,
            "message": "Session revoked successfully",
        }

    @with_readonly_session(manager=None)
    def get_login_history(
        self,
        session,
        *,
        user_id: str,
        limit: int = 20,
    ) -> Dict[str, Any]:
        user = self._user_repo._get_by_id(session, record_id=user_id, include_deleted=False)
        if not user:
            raise BusinessRuleViolationError(
                rule_name="user_not_found",
                rule_detail="user not found",
                message="User not found"
            )
        
        login_history = self._login_history_repo._get_by_user_id(
            session,
            user_id=user_id,
            last_n=limit,
            include_deleted=False
        )
        
        history_list = []
        for login in login_history:
            history_list.append({
                "id": login.id,
                "status": login.status.value if login.status else None,
                "login_method": login.login_method.value if login.login_method else None,
                "failure_reason": login.failure_reason,
                "ip_address": login.ip_address,
                "country_code": login.country_code,
                "city": login.city,
                "device_type": login.device_type.value if login.device_type else None,
                "browser": login.browser,
                "os": login.os,
                "is_suspicious": login.is_suspicious,
                "created_at": login.created_at.isoformat() if login.created_at else None,
            })
        
        return {
            "user_id": user_id,
            "total_records": len(history_list),
            "history": history_list,
        }

    @with_readonly_session(manager=None)
    def get_password_history(
        self,
        session,
        *,
        user_id: str,
        limit: int = 10,
    ) -> Dict[str, Any]:
        user = self._user_repo._get_by_id(session, record_id=user_id, include_deleted=False)
        if not user:
            raise BusinessRuleViolationError(
                rule_name="user_not_found",
                rule_detail="user not found",
                message="User not found"
            )
        
        password_history = self._password_history_repo._get_by_user_id(
            session,
            user_id=user_id,
            last_n=limit,
            include_deleted=False
        )
        
        history_list = []
        for pwd_history in password_history:
            history_list.append({
                "id": pwd_history.id,
                "change_reason": pwd_history.change_reason,
                "changed_from_ip": pwd_history.changed_from_ip,
                "changed_from_device": pwd_history.changed_from_device,
                "created_at": pwd_history.created_at.isoformat() if pwd_history.created_at else None,
            })
        
        return {
            "user_id": user_id,
            "total_records": len(history_list),
            "history": history_list,
        }
    
    @with_transaction(manager=None)
    def change_username(
        self,
        session,
        *,
        user_id: str,
        new_user_name: str,
    ) -> Dict[str, Any]:
        user = self._user_repo._get_by_id(session, record_id=user_id, include_deleted=False)
        if not user:
            raise BusinessRuleViolationError(
                rule_name="user_not_found",
                rule_detail="user not found",
                message="User not found"
            )
        
        if self._user_repo._get_by_username(session, username=new_user_name, include_deleted=False):
            raise BusinessRuleViolationError(
                rule_name="username_already_exists",
                rule_detail="username already exists",
                message="Username already exists"
            )

        user.username = new_user_name

        self._mailtrap_client.send_notification_email(
            to_email=user.email,
            template_variables={
                "company_info_name": "Test Company Info Name",
                "name": user.name or "User",
                "company_info_address": "Test Company Info Address",
                "company_info_city": "Test Company Info City",
                "company_info_zip_code": "Test Company Info Zip Code",
                "company_info_country": "Test Company Info Country"
            }
        )
        
        return {
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "success": True,
        }
    
    @with_transaction(manager=None)
    def change_email(
        self,
        session,
        *,
        user_id: str,
        new_email: str,
    ) -> Dict[str, Any]:
        user = self._user_repo._get_by_id(session, record_id=user_id, include_deleted=False)
        if not user:
            raise BusinessRuleViolationError(
                rule_name="user_not_found",
                rule_detail="user not found",
                message="User not found"
            )
        
        if self._user_repo._get_by_email(session, email=new_email, include_deleted=False):
            raise BusinessRuleViolationError(
                rule_name="email_already_exists",
                rule_detail="email already exists",
                message="Email already exists"
            )
        
        # Email değişikliği için verification token oluştur
        old_email = user.email
        user.email = new_email
        user.is_verified = False  # Yeni email doğrulanana kadar verified değil
        user.email_verified_at = None
        verification_token = user.generate_email_verification_token()

        # Yeni email'e verification token gönder
        self._mailtrap_client.send_verification_email(
            to_email=new_email,
            template_variables={
                "company_info_name": "Test Company Info Name",
                "name": user.name or "User",
                "verification_token": verification_token,
                "company_info_address": "Test Company Info Address",
                "company_info_city": "Test Company Info City",
                "company_info_zip_code": "Test Company Info Zip Code",
                "company_info_country": "Test Company Info Country"
            }
        )

        # Eski email'e bilgilendirme gönder (güvenlik için)
        self._mailtrap_client.send_notification_email(
            to_email=old_email,
            template_variables={
                "company_info_name": "Test Company Info Name",
                "name": user.name or "User",
                "company_info_address": "Test Company Info Address",
                "company_info_city": "Test Company Info City",
                "company_info_zip_code": "Test Company Info Zip Code",
                "company_info_country": "Test Company Info Country"
            }
        )
        
        return {
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "is_verified": user.is_verified,
            "success": True,
            "message": "Email updated successfully. Please verify your new email address.",
        }

    @with_transaction(manager=None)
    def update_user_info(
        self,
        session,
        *,
        user_id: str,
        avatar_url: str,
        name: Optional[str] = None,
        surname: Optional[str] = None,
        country_code: Optional[str] = None,
        phone_number: Optional[str] = None,
    ) -> Dict[str, Any] :
        user = self._user_repo._get_by_id(session, record_id=user_id, include_deleted=False)
        if not user:
            raise BusinessRuleViolationError(
                rule_name="user_not_found",
                rule_detail="user not found",
                message="User not found"
            )

        if avatar_url:
            user.avatar_url = avatar_url
        if name:
            user.name = name
        if surname:
            user.surname = surname
        if country_code:
            user.country_code = country_code
        if phone_number:
            user.phone_number = phone_number

        return {
            "user_id": user.id,
            "avatar_url": user.avatar_url,
            "name": user.name,
            "surname": user.surname,
            "country_code": user.country_code,
            "phone_number": user.phone_number,
            "success": True,
        }

    @with_transaction(manager=None)
    def request_user_deletion(
        self,
        session,
        *,
        user_id: str,
        reason: str,
    ) -> Dict[str, Any]:
        user = self._user_repo._get_by_id(session, record_id=user_id, include_deleted=False)
        if not user:
            raise BusinessRuleViolationError(
                rule_name="user_not_found",
                rule_detail="user not found",
                message="User not found"
            )
        
        user.deletion_requested_at = datetime.now(timezone.utc)
        user.deletion_scheduled_for = datetime.now(timezone.utc) + timedelta(days=30)
        user.deletion_reason = reason

        # DateTime'ları ISO formatına çevir
        return {
            "user_id": user.id,
            "deletion_requested_at": user.deletion_requested_at.isoformat() if user.deletion_requested_at else None,
            "deletion_scheduled_for": user.deletion_scheduled_for.isoformat() if user.deletion_scheduled_for else None,
            "deletion_reason": user.deletion_reason,
            "success": True,
        }

    @with_transaction(manager=None)
    def cancel_user_deletion(
        self,
        session,
        *,
        user_id: str,
    ) -> Dict[str, Any]:
        user = self._user_repo._get_by_id(session, record_id=user_id, include_deleted=False)
        if not user:
            raise BusinessRuleViolationError(
                rule_name="user_not_found",
                rule_detail="user not found",
                message="User not found"
            )
        
        user.deletion_requested_at = None
        user.deletion_scheduled_for = None
        user.deletion_reason = None

        return {
            "user_id": user.id,
            "success": True,
        }

    @with_transaction(manager=None)
    def change_password(
        self,
        session,
        *,
        user_id: str,
        old_password: str,
        new_password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Dict[str, Any]:
        user = self._user_repo._get_by_id(session, record_id=user_id, include_deleted=False)
        if not user:
            raise BusinessRuleViolationError(
                rule_name="user_not_found",
                rule_detail="user not found",
                message="User not found"
            )
        
        if not verify_password(old_password, user.hashed_password):
            raise BusinessRuleViolationError(
                rule_name="invalid_password",
                rule_detail="invalid password",
                message="Old password is incorrect"
            )
        
        # Yeni şifreyi hash'le
        new_password_hash = hash_password(new_password)
        
        # Şifre tekrar kullanımı kontrolü: Son 5 şifre içinde kullanılmış mı?
        if self._password_history_repo._check_password_reuse(session,  user_id=user_id,  password_hash=new_password_hash,  last_n=self.max_password_history_count):
            raise BusinessRuleViolationError(
                rule_name="password_reuse_not_allowed",
                rule_detail="password reuse not allowed",
                message="You cannot reuse any of your last 5 passwords. Please choose a different password."
            )
        
        # Eski şifreyi password history'ye kaydet
        old_password_hash = user.hashed_password
        if old_password_hash:  # İlk kayıt olabilir, şifre olmayabilir
            self._password_history_repo._create(
                session,
                user_id=user.id,
                password_hash=old_password_hash,
                change_reason=PasswordChangeReason.VOLUNTARY.value,
                changed_from_ip=ip_address,
                changed_from_device=user_agent,
                created_by=user.id
            )
            
            # Maksimum password history sayısını aşan eski kayıtları sil
            self._password_history_repo._cleanup_old_passwords(
                session,
                user_id=user.id,
                max_count=self.max_password_history_count
            )
        
        # Yeni şifreyi güncelle
        user.hashed_password = new_password_hash
        user.password_changed_at = datetime.now(timezone.utc)

        return {
            "user_id": user.id,
            "success": True,
            "message": "Password changed successfully",
        }

    @with_transaction(manager=None)
    def send_password_reset_email(
        self,
        session,
        *,
        email: str,
    ) -> Dict[str, Any]:

        user = self._user_repo._get_by_email(session, email=email, include_deleted=False)
        
        if user:
            user.generate_password_reset_token()
            self._mailtrap_client.send_password_reset_email(
                to_email=user.email,
                template_variables={
                    "company_info_name": "Test Company Info Name",
                    "name": user.name or "User",
                    "company_info_address": "Test Company Info Address",
                    "company_info_city": "Test Company Info City",
                    "company_info_zip_code": "Test Company Info Zip Code",
                    "company_info_country": "Test Company Info Country"
                }
            )
        
        return {
            "success": True,
            "message": "If an account with that email exists, a password reset link has been sent.",
        }

    @with_transaction(manager=None)
    def validate_password_reset_token(
        self,
        session,
        *,
        password_reset_token: str,
    ) -> Dict[str, Any]:
        user = self._user_repo._get_by_password_reset_token(session, password_reset_token=password_reset_token, include_deleted=False)
        if not user:
            raise BusinessRuleViolationError(
                rule_name="password_reset_token_not_found",
                rule_detail="password reset token not found",
                message="Password reset token not found"
            )
        
        if not user.is_password_reset_token_valid(password_reset_token):
            raise BusinessRuleViolationError(
                rule_name="password_reset_token_expired",
                rule_detail="password reset token expired",
                message="Password reset token has expired"
            )
        
        # Token zaten yeterli bilgiyi taşıyor, gereksiz bilgi döndürmeyin
        return {
            "success": True,
            "valid": True,
        }

    @with_transaction(manager=None)
    def reset_password(
        self,
        session,
        *,
        password_reset_token: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Dict[str, Any]:
        
        user = self._user_repo._get_by_password_reset_token(session, password_reset_token=password_reset_token, include_deleted=False)
        if not user:
            raise BusinessRuleViolationError(
                rule_name="password_reset_token_not_found",
                rule_detail="password reset token not found",
                message="Password reset token not found"
            )
        
        if not user.is_password_reset_token_valid(password_reset_token):
            raise BusinessRuleViolationError(
                rule_name="password_reset_token_expired",
                rule_detail="password reset token expired",
                message="Password reset token has expired"
            )
        
        # Yeni şifreyi hash'le
        new_password_hash = hash_password(password)
        
        # Şifre tekrar kullanımı kontrolü: Son 5 şifre içinde kullanılmış mı?
        if self._password_history_repo._check_password_reuse(session, user_id=user.id, password_hash=new_password_hash, last_n=5):
            raise BusinessRuleViolationError(
                rule_name="password_reuse_not_allowed",
                rule_detail="password reuse not allowed",
                message="You cannot reuse any of your last 5 passwords. Please choose a different password."
            )
        
        # Eski şifreyi password history'ye kaydet
        old_password_hash = user.hashed_password
        if old_password_hash:  
            self._password_history_repo._create(
                session,
                user_id=user.id,
                password_hash=old_password_hash,
                change_reason=PasswordChangeReason.RESET.value,
                changed_from_ip=ip_address,
                changed_from_device=user_agent,
                created_by=user.id
            )
            
            
            self._password_history_repo._cleanup_old_passwords(
                session,
                user_id=user.id,
                max_count=self.max_password_history_count
            )
        
        # Yeni şifreyi güncelle
        user.hashed_password = new_password_hash
        user.password_changed_at = datetime.now(timezone.utc)
        user.password_reset_token = None
        user.password_reset_token_expires_at = None

        return {
            "user_id": user.id,
            "success": True,
            "message": "Password reset successfully",
        }