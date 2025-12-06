from typing import Optional, Any, List

from sqlalchemy import select, delete
from sqlalchemy.orm import Session

from ..base_repository import BaseRepository
from miniflow.models import UserPreference


class UserPreferenceRepository(BaseRepository[UserPreference]):
    def __init__(self):
        super().__init__(UserPreference)

    @BaseRepository._handle_db_exceptions
    def _get_by_user_id(self, session: Session, user_id: str, include_deleted: bool = False) -> List[UserPreference]:
        """Kullanıcının tüm tercihlerini getirir."""
        query = select(UserPreference).where(UserPreference.user_id == user_id)
        query = self._apply_soft_delete_filter(query, include_deleted)
        return list(session.execute(query).scalars().all())

    @BaseRepository._handle_db_exceptions
    def _get_by_user_and_key(self, session: Session, *, user_id: str, key: str, include_deleted: bool = False) -> Optional[UserPreference]:
        """Kullanıcının belirli bir tercihini getirir."""
        query = select(UserPreference).where(
            UserPreference.user_id == user_id,
            UserPreference.key == key
        )
        query = self._apply_soft_delete_filter(query, include_deleted)
        return session.execute(query).scalar_one_or_none()

    @BaseRepository._handle_db_exceptions
    def _get_by_user_and_category(self, session: Session, *, user_id: str, category: str, include_deleted: bool = False) -> List[UserPreference]:
        """Kullanıcının belirli bir kategorideki tercihlerini getirir."""
        query = select(UserPreference).where(
            UserPreference.user_id == user_id,
            UserPreference.category == category
        )
        query = self._apply_soft_delete_filter(query, include_deleted)
        return list(session.execute(query).scalars().all())

    @BaseRepository._handle_db_exceptions
    def _upsert_preference(self, session: Session, *, user_id: str, key: str, value: Any, category: Optional[str] = None, description: Optional[str] = None) -> UserPreference:
        """Tercih varsa günceller, yoksa oluşturur."""
        existing = self._get_by_user_and_key(session, user_id=user_id, key=key)
        
        if existing:
            existing.value = value
            if category is not None:
                existing.category = category
            if description is not None:
                existing.description = description
            return existing
        else:
            return self._create(
                session,
                user_id=user_id,
                key=key,
                value=value,
                category=category,
                description=description,
                created_by=user_id
            )

    @BaseRepository._handle_db_exceptions
    def _delete_by_user_and_key(self, session: Session, *, user_id: str, key: str) -> bool:
        """Kullanıcının belirli bir tercihini siler (hard delete)."""
        existing = self._get_by_user_and_key(session, user_id=user_id, key=key)
        if existing:
            session.delete(existing)
            return True
        return False

    @BaseRepository._handle_db_exceptions
    def _delete_all_user_preferences(self, session: Session, *, user_id: str) -> int:
        """Kullanıcının tüm tercihlerini siler (hard delete)."""
        query = delete(UserPreference).where(UserPreference.user_id == user_id)
        result = session.execute(query)
        return result.rowcount