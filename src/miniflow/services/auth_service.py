import secrets
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone, timedelta

from src.miniflow.database import with_transaction, with_readonly_session
from src.miniflow.database import DatabaseManager, RepositoryRegistry
from ..database.models.enums import LoginStatus, LoginMethod
from src.miniflow.database.models import User

from src.miniflow.core.exceptions import BusinessRuleViolationError, InvalidInputError, DatabaseValidationError
from src.miniflow.utils.helpers.encryption_helper import hash_password, hash_data, verify_password
from src.miniflow.utils.helpers.jwt_helper import create_access_token, create_refresh_token, validate_access_token, validate_refresh_token, is_token_valid
from src.miniflow.utils import ConfigurationHandler, MailTrapClient


class AuthenticationService:
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
        self.max_active_sessions = ConfigurationHandler.get_int("AUTH", "max_active_sessions", 5)


    @with_transaction(manager=None)
    def register_user(
        self,
        session,
        *,
        username: str,
        email: str,
        password: str,
        name: str,
        surname: str,
        marketing_consent: bool = False,
        terms_accepted_version: str = None,
        privacy_policy_accepted_version: str = None,
        **kwargs: Any
    ) -> Dict[str, Any]:

        if not terms_accepted_version or not privacy_policy_accepted_version:
            raise BusinessRuleViolationError(
                rule_name="must_sign_acceptances",
                rule_detail="user must sign terms and privacy policy to register",
                message="You must accept the terms of service and privacy policy to register"
            )
        
        if not User.validate_email_format(email):
            raise InvalidInputError(
                field_name="email",
                message="Invalid email format. Please provide a valid email address"
            )
        
        password_validation = User.validate_password_strength(password)
        if not password_validation["valid"]:
            error_messages = ", ".join(password_validation.get("errors", []))
            raise InvalidInputError(
                field_name="password",
                message=f"Password does not meet requirements: {error_messages}"
            )
        
        username_validation = User.validate_username(username)
        if not username_validation["valid"]:
            error_messages = ", ".join(username_validation.get("errors", []))
            raise InvalidInputError(
                field_name="username",
                message=f"Username validation failed: {error_messages}"
            )
        
        hashed_password = hash_password(password)
        password_changed_at = datetime.now(timezone.utc)

        user = User(
            username=username,
            email=email,
            password=hashed_password,
            password_changed_at=password_changed_at,
            name=name,
            surname=surname,
            marketing_consent=marketing_consent,
            marketing_consent_at=datetime.now(timezone.utc) if marketing_consent else None,
            created_by="SYSTEM",
        )

        user.generate_email_verification_token()
        self._mailtrap_client.send_verification_email(
            to_email=email,
            template_variables={
                "company_info_name": "Test Company Info Name",
                "name": "Test_Name",
                "company_info_address": "Test Company Info Address",
                "company_info_city": "Test Company Info City",
                "company_info_zip_code": "Test Company Info Zip Code",
                "company_info_country": "Test Company Info Country"
            }
        )

        session.add(user)

        ip_hash = hash_data(kwargs.get("ip_address", "")) if kwargs.get("ip_address", "") else None
        ua_hash = hash_data(kwargs.get("user_agent", "")) if kwargs.get("user_agent", "") else None

        for agreement_type in ["terms", "privacy_policy"]:
            version_id = terms_accepted_version if agreement_type == "terms" else privacy_policy_accepted_version
            version = self._agreement_version_repo._get_by_id(session, record_id=version_id, include_deleted=False)
            if not version:
                raise BusinessRuleViolationError(
                    rule_name="agreement_version_not_found",
                    rule_detail="agreement version not found",
                    message=f"Invalid {agreement_type} version. Please accept the latest version"
                )
            self._user_agreement_repo._create(
                session=session,
                user_id=user.id,
                agreement_version_id=version.id,
                accepted_at=datetime.now(timezone.utc),
                ip_address_hash=ip_hash,
                user_agent_hash=ua_hash,
                acceptance_method="web",
                locale="tr-TR",
                acceptance_metadata={"device_type": "web", "app_version": "1.0.0", "os_version": "10.0", "geolocation": "Turkey", "referrer": "https://www.google.com"},
                created_by=user.id
            )

        return {
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "is_verified": user.is_verified,
        }

    @with_transaction(manager=None)
    def send_verification_email(
        self,
        session,
        *,
        user_id: str,
        email: str,
    ) -> Dict[str, Any]:
        user = self._user_repo._get_by_id(session, record_id=user_id, include_deleted=False)
        if not user:
            raise BusinessRuleViolationError(
                rule_name="user_not_found",
                rule_detail="user not found",
                message="User not found"
            )
        
        user.generate_email_verification_token()

        self._mailtrap_client.send_verification_email(
            to_email=email,
            template_variables={
                "company_info_name": "Test Company Info Name",
                "name": "Test_Name",
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
        }

    @with_transaction(manager=None)
    def verify_email(
        self,
        session,
        *,
        verification_token: str,
    ) -> Dict[str, Any]:

        user = self._user_repo._get_by_email_verification_token(session, verification_token, include_deleted=False)
        if not user:
            raise BusinessRuleViolationError(
                rule_name="verification_token_not_found",
                rule_detail="verification token not found",
                message="Verification token is invalid or expired"
            )
        
        # Token expiration kontrolü
        if not user.is_email_verification_token_valid(verification_token):
            raise BusinessRuleViolationError(
                rule_name="verification_token_expired",
                rule_detail="verification token expired",
                message="Verification token has expired. Please request a new verification email"
            )
        
        if user.is_verified:
            raise BusinessRuleViolationError(
                rule_name="user_already_verified",
                rule_detail="user already verified",
                message="User already verified"
            )

        user.is_verified = True
        user.email_verified_at = datetime.now(timezone.utc)
        user.email_verification_token = None
        user.email_verification_token_expires_at = None

        self._mailtrap_client.send_welcome_email(
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
            "is_verified": user.is_verified,
        }

    @with_transaction(manager=None)
    def login(
        self,
        session,
        *,
        email_or_username: str,
        password: str,
        **kwargs
    ) -> Dict[str, Any]:

        user = self._user_repo._get_by_email_or_username(session, email_or_username, include_deleted=False)
        if not user:
            raise BusinessRuleViolationError(
                rule_name="invalid_credentials",
                rule_detail="invalid credentials",
                message="Invalid credentials"
            )
            
        if not user.is_verified:
            self._login_history_repo._create(
                session,
                user_id=user.id,
                status=LoginStatus.FAILED_EMAIL_NOT_VERIFIED,
                failure_reason="Email not verified",
                created_by=user.id
            )

            if user.verification_token_is_valid(user.email_verification_token):
                raise BusinessRuleViolationError(
                    rule_name="email_not_verified",
                    rule_detail="email not verified",
                    message="Please verify your email address before logging in. Check your inbox for the verification email"
                )
            else:
                self.send_verification_email(session, user_id=user.id, email=user.email)
                raise BusinessRuleViolationError(
                    rule_name="email_not_verified",
                    rule_detail="email not verified",
                    message="Please verify your email address before logging in. Check your inbox for the verification email"
                )

        if user.is_locked:
            # locked_until None olabilir, bu durumda manuel unlock gerekir
            if user.locked_until and user.is_account_locked():
                self._login_history_repo._create(
                    session,
                    user_id=user.id,
                    status=LoginStatus.FAILED_ACCOUNT_LOCKED,
                    failure_reason="Account is locked",
                    created_by=user.id
                )
                raise BusinessRuleViolationError(
                    rule_name="account_locked",
                    rule_detail="account locked",
                    message="Your account has been temporarily locked due to security reasons. Please try again later or contact support"
                )
            
            # Lock süresi dolmuşsa otomatik unlock
            if user.locked_until and not user.is_account_locked():
                user.is_locked = False
                user.locked_reason = None
                user.locked_until = None
            
        if not verify_password(password, user.hashed_password):
            # Başarısız login denemesini kaydet
            self._login_history_repo._create(
                session,
                user_id=user.id,
                status=LoginStatus.FAILED_INVALID_CREDENTIALS,
                failure_reason="Invalid credentials",
                created_by=user.id
            )
            
            # Rate limit kontrolü (yeni kayıt dahil)
            if self._login_history_repo._check_user_rate_limit(session, user_id=user.id, max_attempts=self.max_failed_attempts, window_minutes=self.rate_limit_window_minutes):
                user.is_locked = True
                user.locked_reason = "Too many failed attempts"
                user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=self.lockout_duration_minutes)


                raise BusinessRuleViolationError(
                    rule_name="rate_limited",
                    rule_detail="rate limited",
                    message=f"Too many failed login attempts. Your account has been temporarily locked for {self.lockout_duration_minutes} minutes. Please try again later"
                )
            
            raise BusinessRuleViolationError(
                rule_name="invalid_credentials",
                rule_detail="invalid credentials",
                message="Invalid email/username or password. Please check your credentials and try again"
            )

        access_token_jti = secrets.token_urlsafe(32)
        refresh_token_jti = secrets.token_urlsafe(32)

        access_token, access_token_expires_at = create_access_token(user_id=user.id, access_token_jti=access_token_jti, additional_claims=kwargs)
        refresh_token, refresh_token_expires_at = create_refresh_token(user_id=user.id, refresh_token_jti=refresh_token_jti, additional_claims=kwargs)

        # Maksimum aktif session sayısını kontrol et, aşılıyorsa en eski session'ı revoke et
        active_sessions = self._auth_session_repo._get_all_active_user_sessions(session, user_id=user.id, include_deleted=False)
        if len(active_sessions) >= self.max_active_sessions:
            self._auth_session_repo._revoke_oldest_session(session, user_id=user.id)

        self._auth_session_repo._create(
            session, 
            user_id=user.id, 
            access_token_jti=access_token_jti, 
            access_token_expires_at=access_token_expires_at, 
            refresh_token_jti=refresh_token_jti, 
            refresh_token_expires_at=refresh_token_expires_at, 
            created_by=user.id
            )

        self._login_history_repo._create(
            session, 
            user_id=user.id, 
            status=LoginStatus.SUCCESS, 
            login_method=LoginMethod.PASSWORD, 
            created_by=user.id
            )

        return {
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "access_token": access_token,
            "refresh_token": refresh_token,
        }

    @with_transaction(manager=None)
    def logout(
        self,
        session,
        *,
        access_token: str
    ) -> Dict[str, Any]:

        try:
            _, payload = validate_access_token(access_token)
        except Exception as e:
            raise BusinessRuleViolationError(
                rule_name="invalid_access_token",
                rule_detail="invalid access token",
                message="Invalid or expired access token. Please log in again"
            )
        
        access_token_jti = payload['jti']
        auth_session = self._auth_session_repo._get_by_access_token_jti(session, access_token_jti=access_token_jti, include_deleted=False)

        if not auth_session:
            raise BusinessRuleViolationError(
                rule_name="invalid_access_token",
                rule_detail="invalid access token",
                message="Access token not found. The session may have been revoked or expired. Please log in again"
            )
        
        if auth_session.is_revoked:
            raise BusinessRuleViolationError(
                rule_name="invalid_access_token",
                rule_detail="invalid access token",
                message="This access token has been revoked. Please log in again to get a new token"
            )

        auth_session.is_revoked = True
        auth_session.revoked_at = datetime.now(timezone.utc)
        auth_session.revoked_by = payload['user_id']

        return {
            "success": True,
            "message": "Logged out successfully",
        }

    @with_transaction(manager=None)
    def logout_all(
        self,
        session,
        *,
        access_token: str,
    ) -> Dict[str, Any]:

        try:
            _, payload = validate_access_token(access_token)
        except Exception as e:
            raise BusinessRuleViolationError(
                rule_name="invalid_access_token",
                rule_detail="invalid access token",
                message="Invalid or expired access token. Please log in again"
            )
        
        access_token_jti = payload['jti']
        auth_session = self._auth_session_repo._get_by_access_token_jti(session, access_token_jti=access_token_jti, include_deleted=False)
        if not auth_session:
            raise BusinessRuleViolationError(
                rule_name="invalid_access_token",
                rule_detail="invalid access token",
                message="Access token not found. The session may have been revoked or expired. Please log in again"
            )

        if auth_session.is_revoked:
            raise BusinessRuleViolationError(
                rule_name="invalid_access_token",
                rule_detail="invalid access token",
                message="This access token has been revoked. Please log in again to get a new token"
            )

        user_id = payload['user_id']
        num_revoked = self._auth_session_repo._revoke_sessions(session, user_id=user_id)

        return {
            "success": True,
            "sessions_revoked": num_revoked,
        }

    @with_transaction(manager=None)
    def refresh_token(
        self,
        session,
        *,
        refresh_token: str
    ) -> Dict[str, Any]:
        try:
            _, payload = validate_refresh_token(refresh_token)
        except Exception as e:
            raise BusinessRuleViolationError(
                rule_name="invalid_refresh_token",
                rule_detail="invalid refresh token",
                message="Invalid or expired refresh token. Please log in again"
            )
        
        refresh_token_jti = payload['jti']
        auth_session = self._auth_session_repo._get_by_refresh_token_jti(session, refresh_token_jti=refresh_token_jti, include_deleted=False)
        if not auth_session:
            raise BusinessRuleViolationError(
                rule_name="refresh_token_not_found",
                rule_detail="refresh token session not found",
                message="Refresh token session not found. The session may have been revoked. Please log in again"
            )

        if auth_session.is_revoked:
            raise BusinessRuleViolationError(
                rule_name="refresh_token_revoked",
                rule_detail="refresh token revoked",
                message="This refresh token has been revoked. Please log in again"
            )

        # Ensure both datetimes are timezone-aware for comparison
        now = datetime.now(timezone.utc)
        expires_at = auth_session.refresh_token_expires_at
        if expires_at.tzinfo is None:
            # If timezone-naive, assume it's UTC
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        
        if expires_at < now:
            raise BusinessRuleViolationError(
                rule_name="refresh_token_expired",
                rule_detail="refresh token expired",
                message="Refresh token has expired. Please log in again"
            )

        user_id = payload['user_id']
        user = self._user_repo._get_by_id(session, record_id=user_id, include_deleted=False)
        if not user:
            raise BusinessRuleViolationError(
                rule_name="user_not_found",
                rule_detail="user not found",
                message="User account not found. Please contact support"
            )

        if not user.is_verified:
            raise BusinessRuleViolationError(
                rule_name="email_not_verified",
                rule_detail="email not verified",
                message="Your email address has not been verified. Please verify your email before using this service"
            )

        if user.is_locked:
            raise BusinessRuleViolationError(
                rule_name="account_locked",
                rule_detail="account locked",
                message="Your account has been locked. Please contact support or try again later"
            )

        new_access_token_jti = secrets.token_urlsafe(32)
        new_refresh_token_jti = secrets.token_urlsafe(32)

        new_access_token, new_access_token_expires_at = create_access_token(user_id=user.id, access_token_jti=new_access_token_jti)
        new_refresh_token, new_refresh_token_expires_at = create_refresh_token(user_id=user.id, refresh_token_jti=new_refresh_token_jti)

        auth_session.access_token_jti = new_access_token_jti
        auth_session.access_token_expires_at = new_access_token_expires_at
        auth_session.refresh_token_jti = new_refresh_token_jti
        auth_session.refresh_token_expires_at = new_refresh_token_expires_at
        auth_session.refresh_token_last_used_at = datetime.now(timezone.utc)
        auth_session.last_activity_at = datetime.now(timezone.utc)

        return {
            'user_id': user.id,
            'access_token': new_access_token,
            'refresh_token': new_refresh_token,
        }

    @with_readonly_session(manager=None)
    def validate_session(
        self,
        session,
        *,
        access_token: str
    ) -> Dict[str, Any]:
        try:
            _, payload = validate_access_token(access_token)
        except Exception as e:
            return {
                "valid": False,
                "error": str(e),
            }
                    
        access_token_jti = payload['jti']
        auth_session = self._auth_session_repo._get_by_access_token_jti(session, access_token_jti=access_token_jti, include_deleted=False)
        if not auth_session:
            return {
                "valid": False,
                "error": "Invalid access token",
            }

        if auth_session.is_revoked:
            return {
                "valid": False,
                "error": "Access token is revoked",
            }

        if not is_token_valid(access_token):
            return {
                "valid": False,
                "error": "Invalid access token",
            }

        # Ensure both datetimes are timezone-aware for comparison
        now = datetime.now(timezone.utc)
        expires_at = auth_session.access_token_expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        
        if expires_at < now:
            return {
                "valid": False,
                "error": "Access token has expired",
            }

        return {
            "valid": True,
            "user_id": auth_session.user_id,
        }