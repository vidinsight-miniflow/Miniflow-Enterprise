import secrets
from typing import Optional, Dict, List, Any
from datetime import datetime, timezone, timedelta

from miniflow.database import RepositoryRegistry, with_transaction, with_readonly_session
from miniflow.models.enums import LoginStatus, LoginMethod
from miniflow.core.exceptions import (
    ResourceNotFoundError,
    BusinessRuleViolationError,
)
from miniflow.utils.helpers.encryption_helper import verify_password
from miniflow.utils.helpers.jwt_helper import (
    create_access_token, 
    create_refresh_token, 
    validate_access_token, 
    validate_refresh_token,
    is_token_valid
)
from miniflow.utils import ConfigurationHandler


class LoginService:
    """
    Kullanıcı giriş/çıkış işlemleri servis katmanı.
    
    Login, logout, token yenileme ve hesap kilitleme işlemlerini yönetir.
    """
    _registry = RepositoryRegistry()
    _user_repo = _registry.user_repository()
    _auth_session_repo = _registry.auth_session_repository()
    _login_history_repo = _registry.login_history_repository()

    # Konfigürasyon - Rate limiting
    _max_failed_attempts = ConfigurationHandler.get_int("AUTH", "max_failed_attempts", 5)
    _rate_limit_window_minutes = ConfigurationHandler.get_int("AUTH", "rate_limit_window_minutes", 5)
    
    # Konfigürasyon - Kademeli kilitleme
    _lockout_base_duration_minutes = ConfigurationHandler.get_int("AUTH", "lockout_base_duration_minutes", 15)
    _max_lockouts_before_permanent = ConfigurationHandler.get_int("AUTH", "max_lockouts_before_permanent", 3)
    _lockout_history_window_hours = ConfigurationHandler.get_int("AUTH", "lockout_history_window_hours", 24)
    
    # Konfigürasyon - Session & History
    _max_active_sessions = ConfigurationHandler.get_int("AUTH", "max_active_sessions", 5)
    _max_login_history_per_user = ConfigurationHandler.get_int("AUTH", "max_login_history_per_user", 10)

    # ==================================================================================== LOGIN ==
    @classmethod
    @with_transaction(manager=None)
    def login(
        cls,
        session,
        *,
        email_or_username: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        device_type: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Kullanıcı girişi yapar.
        
        Args:
            email_or_username: E-posta veya kullanıcı adı
            password: Şifre
            ip_address: IP adresi (opsiyonel)
            user_agent: User agent (opsiyonel)
            device_type: Cihaz tipi (opsiyonel)
            
        Returns:
            {
                "id": str,
                "username": str,
                "email": str,
                "access_token": str,
                "refresh_token": str
            }
            
        Raises:
            BusinessRuleViolationError: Geçersiz kimlik, hesap kilitli, email doğrulanmamış
        """
        # Kullanıcıyı bul
        user = cls._user_repo._get_by_email_or_username(session, email_or_username, include_deleted=False)
        if not user:
            raise BusinessRuleViolationError(
                rule_name="invalid_credentials",
                rule_detail="User not found with provided email/username",
                message="Invalid email/username or password"
            )
        
        # Email doğrulanmış mı?
        if not user.is_verified:
            cls._login_history_repo._create(
                session,
                user_id=user.id,
                status=LoginStatus.FAILED_EMAIL_NOT_VERIFIED,
                failure_reason="Email not verified",
                ip_address=ip_address,
                user_agent=user_agent,
                created_by=user.id
            )
            raise BusinessRuleViolationError(
                rule_name="email_not_verified",
                rule_detail="Email verification required before login",
                message="Please verify your email address before logging in"
            )
        
        # Hesap kilitli mi?
        if user.is_locked:
            if user.locked_until:
                # locked_until kontrolü
                locked_until = user.locked_until
                if locked_until.tzinfo is None:
                    locked_until = locked_until.replace(tzinfo=timezone.utc)
                
                if datetime.now(timezone.utc) < locked_until:
                    cls._login_history_repo._create(
                        session,
                        user_id=user.id,
                        status=LoginStatus.FAILED_ACCOUNT_LOCKED,
                        failure_reason="Account is locked",
                        ip_address=ip_address,
                        user_agent=user_agent,
                        created_by=user.id
                    )
                    raise BusinessRuleViolationError(
                        rule_name="account_locked",
                        rule_detail=f"Account locked until {locked_until.isoformat()}",
                        message="Your account has been temporarily locked. Please try again later"
                    )
                else:
                    # Lock süresi dolmuş, otomatik unlock
                    cls._user_repo._update(
                        session, 
                        record_id=user.id, 
                        is_locked=False, 
                        locked_reason=None, 
                        locked_until=None
                    )
            else:
                # Manuel lock (locked_until yok)
                raise BusinessRuleViolationError(
                    rule_name="account_locked",
                    rule_detail="Account manually locked by administrator",
                    message="Your account has been locked. Please contact support"
                )
        
        # Şifre doğrulama
        if not verify_password(password, user.hashed_password):
            cls._login_history_repo._create(
                session,
                user_id=user.id,
                status=LoginStatus.FAILED_INVALID_CREDENTIALS,
                failure_reason="Invalid password",
                ip_address=ip_address,
                user_agent=user_agent,
                created_by=user.id
            )
            
            # Rate limit kontrolü
            if cls._login_history_repo._check_user_rate_limit(
                session, 
                user_id=user.id, 
                max_attempts=cls._max_failed_attempts, 
                window_minutes=cls._rate_limit_window_minutes
            ):
                # Kademeli kilitleme: Son N saat içindeki kilitleme sayısını kontrol et
                recent_lockouts = cls._login_history_repo._count_recent_lockouts(
                    session,
                    user_id=user.id,
                    window_hours=cls._lockout_history_window_hours
                )
                
                # Kalıcı mı yoksa geçici mi kilitleme yapılacak?
                if recent_lockouts >= cls._max_lockouts_before_permanent:
                    # KALICI KİLİTLEME - Sadece admin açabilir
                    cls._user_repo._update(
                        session,
                        record_id=user.id,
                        is_locked=True,
                        locked_reason=f"Permanent lock: Too many lockouts ({recent_lockouts + 1}) in {cls._lockout_history_window_hours}h",
                        locked_until=None  # None = kalıcı kilit
                    )
                    # Tüm aktif session'ları iptal et
                    cls._auth_session_repo._revoke_sessions(session, user_id=user.id)
                    
                    # Kilitleme kaydı oluştur (kademeli kilitleme için sayılır)
                    cls._login_history_repo._create(
                        session,
                        user_id=user.id,
                        status=LoginStatus.FAILED_ACCOUNT_LOCKED,
                        failure_reason=f"Permanent lock #{recent_lockouts + 1}",
                        ip_address=ip_address,
                        user_agent=user_agent,
                        created_by=user.id
                    )
                    
                    raise BusinessRuleViolationError(
                        rule_name="account_permanently_locked",
                        rule_detail=f"Permanent lock due to {recent_lockouts + 1} lockouts in {cls._lockout_history_window_hours} hours",
                        message="Your account has been permanently locked due to repeated security violations. Please contact support."
                    )
                else:
                    # GEÇİCİ KİLİTLEME - Kademeli süre: base * (2 ^ lockout_count)
                    # 1. kilit: 15dk, 2. kilit: 30dk, 3. kilit: 60dk
                    lockout_duration = cls._lockout_base_duration_minutes * (2 ** recent_lockouts)
                    
                    cls._user_repo._update(
                        session,
                        record_id=user.id,
                        is_locked=True,
                        locked_reason=f"Temporary lock: Too many failed attempts (lockout #{recent_lockouts + 1})",
                        locked_until=datetime.now(timezone.utc) + timedelta(minutes=lockout_duration)
                    )
                    
                    # Kilitleme kaydı oluştur (kademeli kilitleme için sayılır)
                    cls._login_history_repo._create(
                        session,
                        user_id=user.id,
                        status=LoginStatus.FAILED_ACCOUNT_LOCKED,
                        failure_reason=f"Temporary lock #{recent_lockouts + 1} for {lockout_duration} minutes",
                        ip_address=ip_address,
                        user_agent=user_agent,
                        created_by=user.id
                    )
                    
                    raise BusinessRuleViolationError(
                        rule_name="rate_limited",
                        rule_detail=f"Account locked for {lockout_duration} minutes due to {recent_lockouts + 1} failed attempts",
                        message=f"Too many failed attempts. Account locked for {lockout_duration} minutes"
                    )
            
            raise BusinessRuleViolationError(
                rule_name="invalid_credentials",
                rule_detail="Password verification failed",
                message="Invalid email/username or password"
            )
        
        # Token'lar oluştur
        access_token_jti = secrets.token_urlsafe(32)
        refresh_token_jti = secrets.token_urlsafe(32)
        
        access_token, access_token_expires_at = create_access_token(
            user_id=user.id, 
            access_token_jti=access_token_jti
        )
        refresh_token, refresh_token_expires_at = create_refresh_token(
            user_id=user.id, 
            refresh_token_jti=refresh_token_jti
        )
        
        # Maksimum aktif session kontrolü
        active_sessions = cls._auth_session_repo._get_all_active_user_sessions(session, user_id=user.id)
        if len(active_sessions) >= cls._max_active_sessions:
            cls._auth_session_repo._revoke_oldest_session(session, user_id=user.id)
        
        # Session oluştur
        cls._auth_session_repo._create(
            session,
            user_id=user.id,
            access_token_jti=access_token_jti,
            access_token_expires_at=access_token_expires_at,
            refresh_token_jti=refresh_token_jti,
            refresh_token_expires_at=refresh_token_expires_at,
            device_type=device_type,
            user_agent=user_agent,
            ip_address=ip_address,
            created_by=user.id
        )
        
        # Login history kaydet
        cls._login_history_repo._create(
            session,
            user_id=user.id,
            status=LoginStatus.SUCCESS,
            login_method=LoginMethod.PASSWORD,
            ip_address=ip_address,
            user_agent=user_agent,
            created_by=user.id
        )
        
        # Eski login history kayıtlarını temizle (max_login_history_per_user'dan fazlası silinir)
        cls._login_history_repo._cleanup_old_history(
            session, 
            user_id=user.id, 
            max_records=cls._max_login_history_per_user
        )
        
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "access_token": access_token,
            "refresh_token": refresh_token,
        }

    # ==================================================================================== LOGOUT ==
    @classmethod
    @with_transaction(manager=None)
    def logout(
        cls,
        session,
        *,
        access_token: str
    ) -> Dict[str, Any]:
        """
        Kullanıcı çıkışı yapar (mevcut session'ı iptal eder).
        
        Args:
            access_token: Access token
            
        Returns:
            {"success": True, "message": str}
            
        Raises:
            BusinessRuleViolationError: Geçersiz token
        """
        try:
            _, payload = validate_access_token(access_token)
        except Exception:
            raise BusinessRuleViolationError(
                rule_name="invalid_access_token",
                rule_detail="Token validation failed or token expired",
                message="Invalid or expired access token"
            )
        
        access_token_jti = payload['jti']
        auth_session = cls._auth_session_repo._get_by_access_token_jti(
            session, 
            access_token_jti=access_token_jti
        )
        
        if not auth_session:
            raise BusinessRuleViolationError(
                rule_name="session_not_found",
                rule_detail=f"Session not found for access_token_jti: {access_token_jti}",
                message="Session not found"
            )
        
        if auth_session.is_revoked:
            raise BusinessRuleViolationError(
                rule_name="session_already_revoked",
                rule_detail=f"Session {auth_session.id} has already been revoked",
                message="Session already revoked"
            )
        
        # Session'ı iptal et
        cls._auth_session_repo._revoke_specific_session(
            session, 
            session_id=auth_session.id, 
            user_id=payload['user_id']
        )
        
        return {
            "success": True,
            "message": "Logged out successfully"
        }

    @classmethod
    @with_transaction(manager=None)
    def logout_all(
        cls,
        session,
        *,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Kullanıcının tüm session'larını iptal eder.
        
        Args:
            user_id: Kullanıcı ID'si
            
        Returns:
            {"success": True, "sessions_revoked": int}
        """
        num_revoked = cls._auth_session_repo._revoke_sessions(session, user_id=user_id)
        
        return {
            "success": True,
            "sessions_revoked": num_revoked
        }

    # ==================================================================================== TOKEN ==
    @classmethod
    @with_readonly_session(manager=None)
    def validate_access_token(
        cls,
        session,
        *,
        access_token: str
    ) -> Dict[str, Any]:
        """
        Access token'ı doğrular.
        
        Args:
            access_token: Access token
            
        Returns:
            {"valid": bool, "user_id": str (if valid), "error": str (if invalid)}
        """
        try:
            _, payload = validate_access_token(access_token)
        except Exception as e:
            return {"valid": False, "error": str(e)}
        
        access_token_jti = payload['jti']
        auth_session = cls._auth_session_repo._get_by_access_token_jti(
            session, 
            access_token_jti=access_token_jti
        )
        
        if not auth_session:
            return {"valid": False, "error": "Session not found"}
        
        if auth_session.is_revoked:
            return {"valid": False, "error": "Session revoked"}
        
        # Token expiry kontrolü
        expires_at = auth_session.access_token_expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        
        if expires_at < datetime.now(timezone.utc):
            return {"valid": False, "error": "Token expired"}
        
        # Kullanıcı kontrolü
        user = cls._user_repo._get_by_id(session, record_id=auth_session.user_id)
        if not user:
            return {"valid": False, "error": "User not found"}
        
        if not user.is_verified:
            return {"valid": False, "error": "Email not verified"}
        
        if user.is_locked:
            return {"valid": False, "error": "Account locked"}
        
        return {
            "valid": True,
            "user_id": auth_session.user_id
        }

    @classmethod
    @with_transaction(manager=None)
    def refresh_tokens(
        cls,
        session,
        *,
        refresh_token: str
    ) -> Dict[str, Any]:
        """
        Refresh token kullanarak yeni access ve refresh token alır.
        
        Args:
            refresh_token: Refresh token
            
        Returns:
            {
                "id": str,
                "access_token": str,
                "refresh_token": str
            }
            
        Raises:
            BusinessRuleViolationError: Geçersiz token, session iptal edilmiş, vb.
        """
        try:
            _, payload = validate_refresh_token(refresh_token)
        except Exception:
            raise BusinessRuleViolationError(
                rule_name="invalid_refresh_token",
                rule_detail="Refresh token validation failed or token expired",
                message="Invalid or expired refresh token"
            )
        
        refresh_token_jti = payload['jti']
        auth_session = cls._auth_session_repo._get_by_refresh_token_jti(
            session, 
            refresh_token_jti=refresh_token_jti
        )
        
        if not auth_session:
            raise BusinessRuleViolationError(
                rule_name="session_not_found",
                rule_detail=f"Session not found for refresh_token_jti: {refresh_token_jti}",
                message="Session not found"
            )
        
        if auth_session.is_revoked:
            raise BusinessRuleViolationError(
                rule_name="session_revoked",
                rule_detail=f"Session {auth_session.id} has been revoked",
                message="Session has been revoked"
            )
        
        # Refresh token expiry kontrolü
        expires_at = auth_session.refresh_token_expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        
        if expires_at < datetime.now(timezone.utc):
            raise BusinessRuleViolationError(
                rule_name="refresh_token_expired",
                rule_detail=f"Refresh token expired at {expires_at.isoformat()}",
                message="Refresh token has expired"
            )
        
        # Kullanıcı kontrolü
        user_id = payload['user_id']
        user = cls._user_repo._get_by_id(session, record_id=user_id)
        if not user:
            raise BusinessRuleViolationError(
                rule_name="user_not_found",
                rule_detail=f"User {user_id} not found in database",
                message="User not found"
            )
        
        if not user.is_verified:
            raise BusinessRuleViolationError(
                rule_name="email_not_verified",
                rule_detail="Email verification required before token refresh",
                message="Email not verified"
            )
        
        if user.is_locked:
            raise BusinessRuleViolationError(
                rule_name="account_locked",
                rule_detail=f"User account {user_id} is currently locked",
                message="Account is locked"
            )
        
        # Yeni token'lar oluştur
        new_access_token_jti = secrets.token_urlsafe(32)
        new_refresh_token_jti = secrets.token_urlsafe(32)
        
        new_access_token, new_access_token_expires_at = create_access_token(
            user_id=user.id, 
            access_token_jti=new_access_token_jti
        )
        new_refresh_token, new_refresh_token_expires_at = create_refresh_token(
            user_id=user.id, 
            refresh_token_jti=new_refresh_token_jti
        )
        
        # Session'ı güncelle
        cls._auth_session_repo._update(
            session,
            record_id=auth_session.id,
            access_token_jti=new_access_token_jti,
            access_token_expires_at=new_access_token_expires_at,
            refresh_token_jti=new_refresh_token_jti,
            refresh_token_expires_at=new_refresh_token_expires_at,
            refresh_token_last_used_at=datetime.now(timezone.utc),
            last_activity_at=datetime.now(timezone.utc)
        )
        
        return {
            "id": user.id,
            "access_token": new_access_token,
            "refresh_token": new_refresh_token
        }

    # ==================================================================================== LOCK ==
    @classmethod
    @with_transaction(manager=None)
    def lock_account(
        cls,
        session,
        *,
        user_id: str,
        reason: Optional[str] = None,
        duration_minutes: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Kullanıcı hesabını kilitler.
        
        Args:
            user_id: Kullanıcı ID'si
            reason: Kilitleme nedeni
            duration_minutes: Kilit süresi (dakika). None ise manuel unlock gerekir.
            
        Returns:
            {"success": True, "locked_until": datetime or None}
        """
        locked_until = None
        if duration_minutes:
            locked_until = datetime.now(timezone.utc) + timedelta(minutes=duration_minutes)
        
        cls._user_repo._update(
            session,
            record_id=user_id,
            is_locked=True,
            locked_reason=reason,
            locked_until=locked_until
        )
        
        # Tüm aktif session'ları iptal et
        cls._auth_session_repo._revoke_sessions(session, user_id=user_id)
        
        return {
            "success": True,
            "locked_until": locked_until
        }

    @classmethod
    @with_transaction(manager=None)
    def unlock_account(
        cls,
        session,
        *,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Kullanıcı hesabını açar.
        
        Args:
            user_id: Kullanıcı ID'si
            
        Returns:
            {"success": True}
        """
        cls._user_repo._update(
            session,
            record_id=user_id,
            is_locked=False,
            locked_reason=None,
            locked_until=None
        )
        
        return {"success": True}
