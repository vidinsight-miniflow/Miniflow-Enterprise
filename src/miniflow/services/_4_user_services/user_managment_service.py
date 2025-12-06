from typing import Optional, Dict, List, Any
from datetime import datetime, timezone, timedelta

from miniflow.database import RepositoryRegistry, with_transaction, with_readonly_session
from miniflow.core.exceptions import (
    ResourceNotFoundError,
    BusinessRuleViolationError,
)
from miniflow.utils import ConfigurationHandler


class UserManagementService:
    """
    Kullanıcı yönetim servisi.
    
    Kullanıcı detayları, tercihler ve hesap silme işlemlerini yönetir.
    NOT: user_exists kontrolü middleware'de yapılır.
    """
    _registry = RepositoryRegistry()
    _user_repo = _registry.user_repository()
    _user_preference_repo = _registry.user_preference_repository()
    _auth_session_repo = _registry.auth_session_repository()

    # Konfigürasyon
    _deletion_grace_period_days = ConfigurationHandler.get_int("USER", "deletion_grace_period_days", 30)

    # ==================================================================================== USER DETAILS ==
    @classmethod
    @with_readonly_session(manager=None)
    def get_user_details(
        cls,
        session,
        *,
        user_id: str,
    ) -> Dict[str, Any]:
        """
        Kullanıcı detaylarını getirir.
        
        Args:
            user_id: Kullanıcı ID'si
            
        Returns:
            Kullanıcı bilgileri (hassas alanlar hariç)
            
        Raises:
            ResourceNotFoundError: Kullanıcı bulunamadı
        """
        user = cls._user_repo._get_by_id(session, record_id=user_id)
        if not user:
            raise ResourceNotFoundError(
                resource_name="User",
                resource_id=user_id
            )
        
        return user.to_dict(exclude_fields=[
            "hashed_password",
            "password_reset_token",
            "password_reset_token_expires_at",
            "email_verification_token",
            "email_verification_token_expires_at",
            "is_superadmin"
        ])

    @classmethod
    @with_readonly_session(manager=None)
    def get_user_by_email(
        cls,
        session,
        *,
        email: str,
    ) -> Dict[str, Any]:
        """
        Email ile kullanıcı detaylarını getirir.
        
        Args:
            email: E-posta adresi
            
        Returns:
            Kullanıcı bilgileri (hassas alanlar hariç)
            
        Raises:
            ResourceNotFoundError: Kullanıcı bulunamadı
        """
        user = cls._user_repo._get_by_email(session, email=email)
        if not user:
            raise ResourceNotFoundError(
                resource_name="User",
                resource_id=email
            )
        
        return user.to_dict(exclude_fields=[
            "hashed_password",
            "password_reset_token",
            "password_reset_token_expires_at",
            "email_verification_token",
            "email_verification_token_expires_at",
            "is_superadmin"
        ])

    @classmethod
    @with_readonly_session(manager=None)
    def get_user_by_username(
        cls,
        session,
        *,
        username: str,
    ) -> Dict[str, Any]:
        """
        Username ile kullanıcı detaylarını getirir.
        
        Args:
            username: Kullanıcı adı
            
        Returns:
            Kullanıcı bilgileri (hassas alanlar hariç)
            
        Raises:
            ResourceNotFoundError: Kullanıcı bulunamadı
        """
        user = cls._user_repo._get_by_username(session, username=username)
        if not user:
            raise ResourceNotFoundError(
                resource_name="User",
                resource_id=username
            )
        
        return user.to_dict(exclude_fields=[
            "hashed_password",
            "password_reset_token",
            "password_reset_token_expires_at",
            "email_verification_token",
            "email_verification_token_expires_at",
            "is_superadmin"
        ])

    # ==================================================================================== USER PREFERENCES ==
    @classmethod
    @with_readonly_session(manager=None)
    def get_all_user_preferences(
        cls,
        session,
        *,
        user_id: str,
    ) -> Dict[str, Any]:
        """
        Kullanıcının tüm tercihlerini getirir.
        
        Args:
            user_id: Kullanıcı ID'si
            
        Returns:
            {"user_id": str, "preferences": List[Dict]}
        """
        preferences = cls._user_preference_repo._get_by_user_id(session, user_id=user_id)
        
        return {
            "user_id": user_id,
            "preferences": [
                {
                    "id": pref.id,
                    "key": pref.key,
                    "value": pref.value,
                    "category": pref.category,
                    "description": pref.description
                }
                for pref in preferences
            ]
        }

    @classmethod
    @with_readonly_session(manager=None)
    def get_user_preference(
        cls,
        session,
        *,
        user_id: str,
        preference_key: str,
    ) -> Dict[str, Any]:
        """
        Kullanıcının belirli bir tercihini getirir.
        
        Args:
            user_id: Kullanıcı ID'si
            preference_key: Tercih anahtarı
            
        Returns:
            Tercih detayları
            
        Raises:
            ResourceNotFoundError: Tercih bulunamadı
        """
        preference = cls._user_preference_repo._get_by_user_and_key(
            session, 
            user_id=user_id, 
            key=preference_key
        )
        
        if not preference:
            raise ResourceNotFoundError(
                resource_name="UserPreference",
                resource_id=preference_key
            )
        
        return {
            "id": preference.id,
            "user_id": preference.user_id,
            "key": preference.key,
            "value": preference.value,
            "category": preference.category,
            "description": preference.description
        }

    @classmethod
    @with_readonly_session(manager=None)
    def get_user_preferences_by_category(
        cls,
        session,
        *,
        user_id: str,
        category: str,
    ) -> Dict[str, Any]:
        """
        Kullanıcının belirli bir kategorideki tercihlerini getirir.
        
        Args:
            user_id: Kullanıcı ID'si
            category: Kategori (ui, notifications, privacy, email, integrations, accessibility)
            
        Returns:
            {"user_id": str, "category": str, "preferences": List[Dict]}
        """
        preferences = cls._user_preference_repo._get_by_user_and_category(
            session, 
            user_id=user_id, 
            category=category
        )
        
        return {
            "user_id": user_id,
            "category": category,
            "preferences": [
                {
                    "id": pref.id,
                    "key": pref.key,
                    "value": pref.value,
                    "description": pref.description
                }
                for pref in preferences
            ]
        }

    @classmethod
    @with_transaction(manager=None)
    def set_user_preference(
        cls,
        session,
        *,
        user_id: str,
        key: str,
        value: Any,
        category: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Kullanıcı tercihini ayarlar (varsa günceller, yoksa oluşturur).
        
        Args:
            user_id: Kullanıcı ID'si
            key: Tercih anahtarı
            value: Tercih değeri (string, number, boolean, object, array olabilir)
            category: Kategori (opsiyonel)
            description: Açıklama (opsiyonel)
            
        Returns:
            Güncellenen/oluşturulan tercih
        """
        preference = cls._user_preference_repo._upsert_preference(
            session,
            user_id=user_id,
            key=key,
            value=value,
            category=category,
            description=description
        )
        
        return {
            "id": preference.id,
            "user_id": preference.user_id,
            "key": preference.key,
            "value": preference.value,
            "category": preference.category,
            "description": preference.description
        }

    @classmethod
    @with_transaction(manager=None)
    def delete_user_preference(
        cls,
        session,
        *,
        user_id: str,
        preference_key: str,
    ) -> Dict[str, Any]:
        """
        Kullanıcının belirli bir tercihini siler.
        
        Args:
            user_id: Kullanıcı ID'si
            preference_key: Tercih anahtarı
            
        Returns:
            {"success": True, "deleted_key": str}
            
        Raises:
            ResourceNotFoundError: Tercih bulunamadı
        """
        deleted = cls._user_preference_repo._delete_by_user_and_key(
            session, 
            user_id=user_id, 
            key=preference_key
        )
        
        if not deleted:
            raise ResourceNotFoundError(
                resource_name="UserPreference",
                resource_id=preference_key
            )
        
        return {
            "success": True,
            "deleted_key": preference_key
        }

    # ==================================================================================== ACCOUNT DELETION ==
    @classmethod
    @with_transaction(manager=None)
    def request_account_deletion(
        cls,
        session,
        *,
        user_id: str,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Hesap silme talebi oluşturur.
        
        30 günlük bekleme süresi başlatır. Bu süre içinde iptal edilebilir.
        
        Args:
            user_id: Kullanıcı ID'si
            reason: Silme nedeni (opsiyonel)
            
        Returns:
            {
                "user_id": str,
                "deletion_requested_at": str,
                "deletion_scheduled_for": str,
                "deletion_reason": str
            }
            
        Raises:
            BusinessRuleViolationError: Zaten silme talebi var
        """
        user = cls._user_repo._get_by_id(session, record_id=user_id)
        if not user:
            raise ResourceNotFoundError(
                resource_name="User",
                resource_id=user_id
            )
        
        if user.deletion_requested_at:
            raise BusinessRuleViolationError(
                rule_name="deletion_already_requested",
                message="Account deletion has already been requested"
            )
        
        now = datetime.now(timezone.utc)
        scheduled_for = now + timedelta(days=cls._deletion_grace_period_days)
        
        cls._user_repo._update(
            session,
            record_id=user_id,
            deletion_requested_at=now,
            deletion_scheduled_for=scheduled_for,
            deletion_reason=reason
        )
        
        return {
            "user_id": user_id,
            "deletion_requested_at": now.isoformat(),
            "deletion_scheduled_for": scheduled_for.isoformat(),
            "deletion_reason": reason,
            "grace_period_days": cls._deletion_grace_period_days
        }

    @classmethod
    @with_transaction(manager=None)
    def cancel_account_deletion(
        cls,
        session,
        *,
        user_id: str,
    ) -> Dict[str, Any]:
        """
        Hesap silme talebini iptal eder.
        
        Args:
            user_id: Kullanıcı ID'si
            
        Returns:
            {"success": True, "message": str}
            
        Raises:
            BusinessRuleViolationError: Silme talebi yok
        """
        user = cls._user_repo._get_by_id(session, record_id=user_id)
        if not user:
            raise ResourceNotFoundError(
                resource_name="User",
                resource_id=user_id
            )
        
        if not user.deletion_requested_at:
            raise BusinessRuleViolationError(
                rule_name="no_deletion_request",
                message="No pending account deletion request found"
            )
        
        cls._user_repo._update(
            session,
            record_id=user_id,
            deletion_requested_at=None,
            deletion_scheduled_for=None,
            deletion_reason=None
        )
        
        return {
            "success": True,
            "message": "Account deletion request cancelled successfully"
        }

    @classmethod
    @with_readonly_session(manager=None)
    def get_deletion_status(
        cls,
        session,
        *,
        user_id: str,
    ) -> Dict[str, Any]:
        """
        Hesap silme durumunu getirir.
        
        Args:
            user_id: Kullanıcı ID'si
            
        Returns:
            {
                "has_pending_deletion": bool,
                "deletion_requested_at": str or None,
                "deletion_scheduled_for": str or None,
                "days_remaining": int or None
            }
        """
        user = cls._user_repo._get_by_id(session, record_id=user_id)
        if not user:
            raise ResourceNotFoundError(
                resource_name="User",
                resource_id=user_id
            )
        
        has_pending = user.deletion_requested_at is not None
        days_remaining = None
        
        if has_pending and user.deletion_scheduled_for:
            scheduled = user.deletion_scheduled_for
            if scheduled.tzinfo is None:
                scheduled = scheduled.replace(tzinfo=timezone.utc)
            delta = scheduled - datetime.now(timezone.utc)
            days_remaining = max(0, delta.days)
        
        return {
            "has_pending_deletion": has_pending,
            "deletion_requested_at": user.deletion_requested_at.isoformat() if user.deletion_requested_at else None,
            "deletion_scheduled_for": user.deletion_scheduled_for.isoformat() if user.deletion_scheduled_for else None,
            "days_remaining": days_remaining
        }

    # ==================================================================================== MARKETING CONSENT ==
    @classmethod
    @with_transaction(manager=None)
    def update_marketing_consent(
        cls,
        session,
        *,
        user_id: str,
        consent: bool,
    ) -> Dict[str, Any]:
        """
        Pazarlama izni günceller.
        
        Args:
            user_id: Kullanıcı ID'si
            consent: Pazarlama izni (True/False)
            
        Returns:
            {"success": True, "marketing_consent": bool, "marketing_consent_at": str}
        """
        user = cls._user_repo._get_by_id(session, record_id=user_id)
        if not user:
            raise ResourceNotFoundError(
                resource_name="User",
                resource_id=user_id
            )
        
        consent_at = datetime.now(timezone.utc) if consent else None
        
        cls._user_repo._update(
            session,
            record_id=user_id,
            marketing_consent=consent,
            marketing_consent_at=consent_at
        )
        
        return {
            "success": True,
            "marketing_consent": consent,
            "marketing_consent_at": consent_at.isoformat() if consent_at else None
        }
