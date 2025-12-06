from typing import Optional, Dict, List, Any
from datetime import datetime, timezone

from miniflow.database import RepositoryRegistry, with_transaction, with_readonly_session
from miniflow.core.exceptions import ResourceNotFoundError


class SessionManagementService:
    """
    Oturum yönetimi servis katmanı.
    
    Aktif oturumları görüntüleme, iptal etme işlemlerini yönetir.
    """
    _registry = RepositoryRegistry()
    _auth_session_repo = _registry.auth_session_repository()

    # ==================================================================================== READ ==
    @classmethod
    @with_readonly_session(manager=None)
    def get_session_by_id(
        cls,
        session,
        *,
        session_id: str
    ) -> Dict[str, Any]:
        """
        ID ile session detaylarını getirir.
        
        Args:
            session_id: Session ID'si
            
        Returns:
            Session detayları
            
        Raises:
            ResourceNotFoundError: Session bulunamazsa
        """
        auth_session = cls._auth_session_repo._get_by_id(
            session, 
            record_id=session_id, 
            raise_not_found=True
        )
        return auth_session.to_dict()

    @classmethod
    @with_readonly_session(manager=None)
    def get_session_by_access_token_jti(
        cls,
        session,
        *,
        access_token_jti: str
    ) -> Optional[Dict[str, Any]]:
        """
        Access token JTI ile session detaylarını getirir.
        
        Args:
            access_token_jti: Access token JTI
            
        Returns:
            Session detayları veya None
        """
        auth_session = cls._auth_session_repo._get_by_access_token_jti(
            session, 
            access_token_jti=access_token_jti
        )
        if not auth_session:
            return None
        return auth_session.to_dict()

    @classmethod
    @with_readonly_session(manager=None)
    def get_session_by_refresh_token_jti(
        cls,
        session,
        *,
        refresh_token_jti: str
    ) -> Optional[Dict[str, Any]]:
        """
        Refresh token JTI ile session detaylarını getirir.
        
        Args:
            refresh_token_jti: Refresh token JTI
            
        Returns:
            Session detayları veya None
        """
        auth_session = cls._auth_session_repo._get_by_refresh_token_jti(
            session, 
            refresh_token_jti=refresh_token_jti
        )
        if not auth_session:
            return None
        return auth_session.to_dict()

    @classmethod
    @with_readonly_session(manager=None)
    def get_user_active_sessions(
        cls,
        session,
        *,
        user_id: str
    ) -> List[Dict[str, Any]]:
        """
        Kullanıcının tüm aktif session'larını getirir.
        
        Args:
            user_id: Kullanıcı ID'si
            
        Returns:
            Aktif session listesi
        """
        sessions = cls._auth_session_repo._get_all_active_user_sessions(
            session, 
            user_id=user_id
        )
        return [s.to_dict() for s in sessions]

    # ==================================================================================== REVOKE ==
    @classmethod
    @with_transaction(manager=None)
    def revoke_session(
        cls,
        session,
        *,
        session_id: str,
        user_id: str,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Belirtilen session'ı iptal eder.
        
        Args:
            session_id: Session ID'si
            user_id: İşlemi yapan kullanıcı ID'si
            reason: İptal nedeni (opsiyonel)
            
        Returns:
            {"success": bool, "session_id": str}
            
        Raises:
            ResourceNotFoundError: Session bulunamazsa
        """
        auth_session = cls._auth_session_repo._revoke_specific_session(
            session, 
            session_id=session_id, 
            user_id=user_id
        )
        
        if not auth_session:
            raise ResourceNotFoundError(
                resource_name="auth_session",
                message="Session not found or already revoked"
            )
        
        # Reason güncelle
        if reason:
            cls._auth_session_repo._update(
                session,
                record_id=auth_session.id,
                revocation_reason=reason
            )
        
        return {
            "success": True,
            "session_id": auth_session.id
        }

    @classmethod
    @with_transaction(manager=None)
    def revoke_all_user_sessions(
        cls,
        session,
        *,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Kullanıcının tüm aktif session'larını iptal eder.
        
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

    @classmethod
    @with_transaction(manager=None)
    def revoke_oldest_session(
        cls,
        session,
        *,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Kullanıcının en eski aktif session'ını iptal eder.
        
        Args:
            user_id: Kullanıcı ID'si
            
        Returns:
            İptal edilen session detayları veya None
        """
        auth_session = cls._auth_session_repo._revoke_oldest_session(session, user_id=user_id)
        
        if not auth_session:
            return None
        
        return auth_session.to_dict()
