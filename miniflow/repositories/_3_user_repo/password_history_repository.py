from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..base_repository import BaseRepository
from miniflow.models import PasswordHistory


class PasswordHistoryRepository(BaseRepository[PasswordHistory]):
    def __init__(self):
        super().__init__(PasswordHistory)

    @BaseRepository._handle_db_exceptions
    def _get_by_user_id(self, session: Session, user_id: str, last_n: int = 5, include_deleted: bool = False) -> List[PasswordHistory]:
        query = (
            select(PasswordHistory)
            .where(PasswordHistory.user_id == user_id)
            .order_by(PasswordHistory.created_at.desc())
            .limit(last_n)
        )
        query = self._apply_soft_delete_filter(query, include_deleted)
        return list(session.execute(query).scalars().all())

    @BaseRepository._handle_db_exceptions
    def _check_password_reuse(self, session: Session, *, user_id: str, password_hash: str, last_n: int = 5 ) -> bool:
        query = (
            select(PasswordHistory)
            .where(PasswordHistory.user_id == user_id)
            .where(PasswordHistory.password_hash == password_hash)
            .order_by(PasswordHistory.created_at.desc())
            .limit(last_n)
        )
        query = self._apply_soft_delete_filter(query, include_deleted=False)
        result = session.execute(query).scalar_one_or_none()
        return result is not None

    @BaseRepository._handle_db_exceptions
    def _cleanup_old_passwords(self, session: Session, *, user_id: str, max_count: int ) -> int:
        all_records = self._get_by_user_id(
            session,
            user_id=user_id,
            last_n=1000, 
            include_deleted=False
        )
        
        if len(all_records) > max_count:
            records_to_delete = all_records[max_count:]
            deleted_count = 0
            
            for record in records_to_delete:
                self._delete(session, record_id=record.id)
                deleted_count += 1
            
            return deleted_count
        return 0
