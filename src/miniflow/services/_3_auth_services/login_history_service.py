from typing import Optional, Dict, List, Any

from miniflow.database import RepositoryRegistry, with_readonly_session
from miniflow.core.exceptions import ResourceNotFoundError


class LoginHistoryService:
    """
    Login geçmişi servis katmanı.
    
    Kullanıcı giriş denemelerinin geçmişini görüntüleme işlemlerini yönetir.
    """
    _registry = RepositoryRegistry()
    _login_history_repo = _registry.login_history_repository()

    # ==================================================================================== READ ==
    @classmethod
    @with_readonly_session(manager=None)
    def get_user_login_history(
        cls,
        session,
        *,
        user_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Kullanıcının son login denemelerini getirir.
        
        Args:
            user_id: Kullanıcı ID'si
            limit: Maksimum kayıt sayısı (varsayılan: 10)
            
        Returns:
            Login geçmişi listesi (en yeniden en eskiye)
        """
        history = cls._login_history_repo._get_by_user_id(
            session, 
            user_id=user_id, 
            last_n=limit
        )
        return [record.to_dict() for record in history] if history else []

    @classmethod
    @with_readonly_session(manager=None)
    def get_login_history_by_id(
        cls,
        session,
        *,
        history_id: str
    ) -> Dict[str, Any]:
        """
        ID ile login kaydını getirir.
        
        Args:
            history_id: Login history ID'si
            
        Returns:
            Login kaydı detayları
            
        Raises:
            ResourceNotFoundError: Kayıt bulunamazsa
        """
        record = cls._login_history_repo._get_by_id(
            session, 
            record_id=history_id, 
            raise_not_found=True
        )
        return record.to_dict()

    @classmethod
    @with_readonly_session(manager=None)
    def check_rate_limit(
        cls,
        session,
        *,
        user_id: str,
        max_attempts: int = 5,
        window_minutes: int = 5
    ) -> bool:
        """
        Kullanıcının rate limit'e ulaşıp ulaşmadığını kontrol eder.
        
        Args:
            user_id: Kullanıcı ID'si
            max_attempts: Maksimum deneme sayısı
            window_minutes: Zaman penceresi (dakika)
            
        Returns:
            True ise rate limit aşılmış
        """
        return cls._login_history_repo._check_user_rate_limit(
            session,
            user_id=user_id,
            max_attempts=max_attempts,
            window_minutes=window_minutes
        )
