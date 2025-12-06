from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta

from sqlalchemy import select, func, delete
from sqlalchemy.orm import Session

from ..base_repository import BaseRepository
from miniflow.models import LoginHistory
from miniflow.models.enums import LoginStatus


class LoginHistoryRepository(BaseRepository[LoginHistory]):
    def __init__(self):
        super().__init__(LoginHistory)

    @BaseRepository._handle_db_exceptions
    def _get_by_user_id(self, session: Session, user_id: str, last_n: int = 10, include_deleted: bool = False) -> Optional[List[LoginHistory]]:
        query = select(LoginHistory).where(LoginHistory.user_id == user_id).order_by(LoginHistory.created_at.desc()).limit(last_n)
        query = self._apply_soft_delete_filter(query, include_deleted)
        return session.execute(query).scalars().all()

    @BaseRepository._handle_db_exceptions
    def _check_user_rate_limit(self, session: Session, *, user_id: str, max_attempts: int = 5, window_minutes: int = 5) -> bool:
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)

        query = select(func.count()).select_from(LoginHistory).where(
            LoginHistory.user_id == user_id,
            LoginHistory.created_at > cutoff_time,
            LoginHistory.status != LoginStatus.SUCCESS
        )
        query = self._apply_soft_delete_filter(query, include_deleted=False)
        return session.execute(query).scalar() >= max_attempts

    @BaseRepository._handle_db_exceptions
    def _count_recent_lockouts(self, session: Session, *, user_id: str, window_hours: int = 24) -> int:
        """
        Son N saat içindeki hesap kilitleme sayısını hesaplar.
        FAILED_ACCOUNT_LOCKED kayıtları sayılır (her kilitleme sonrası oluşur).
        
        Args:
            session: Database session
            user_id: Kullanıcı ID'si
            window_hours: Kilitleme geçmişi penceresi (saat)
            
        Returns:
            Kilitleme sayısı
        """
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=window_hours)
        
        query = select(func.count()).select_from(LoginHistory).where(
            LoginHistory.user_id == user_id,
            LoginHistory.created_at > cutoff_time,
            LoginHistory.status == LoginStatus.FAILED_ACCOUNT_LOCKED
        )
        query = self._apply_soft_delete_filter(query, include_deleted=False)
        return session.execute(query).scalar() or 0

    @BaseRepository._handle_db_exceptions
    def _cleanup_old_history(self, session: Session, user_id: str, max_records: int = 10) -> int:
        """
        Kullanıcının login history'sini max_records ile sınırlar.
        En eski kayıtlar silinir (hard delete).
        
        Args:
            session: Database session
            user_id: Kullanıcı ID'si
            max_records: Tutulacak maksimum kayıt sayısı
            
        Returns:
            Silinen kayıt sayısı
        """
        # Önce kullanıcının toplam kayıt sayısını al
        count_query = select(func.count()).select_from(LoginHistory).where(
            LoginHistory.user_id == user_id
        )
        total_count = session.execute(count_query).scalar()
        
        if total_count <= max_records:
            return 0
        
        # max_records'tan fazlaysa, en yeni max_records kaydı hariç kalanları sil
        # Saklanacak kayıtların ID'lerini bul
        keep_query = (
            select(LoginHistory.id)
            .where(LoginHistory.user_id == user_id)
            .order_by(LoginHistory.created_at.desc())
            .limit(max_records)
        )
        keep_ids = [row[0] for row in session.execute(keep_query).fetchall()]
        
        # Saklanmayacak kayıtları sil
        if keep_ids:
            delete_query = (
                delete(LoginHistory)
                .where(LoginHistory.user_id == user_id)
                .where(LoginHistory.id.not_in(keep_ids))
            )
            result = session.execute(delete_query)
            return result.rowcount
        
        return 0