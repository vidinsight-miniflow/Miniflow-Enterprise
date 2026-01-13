"""Bulk Repository - Toplu CRUD İşlemleri."""

from typing import Any, Dict, List, Set
from datetime import datetime, timezone

from sqlalchemy import update, delete
from sqlalchemy.orm import Session

from qbitra.core.exceptions import DatabaseValidationError
from .base import BaseRepository, handle_exceptions, T


class BulkRepository(BaseRepository[T]):
    """Toplu işlemler için repository."""

    def __init__(self, model: type[T]):
        super().__init__(model)
        # Bir kez hesapla, her yerde kullan - O(1)
        self._fields: Set[str] = {c.name for c in model.__table__.columns}
        self._has_soft_delete = 'is_deleted' in self._fields
        self._has_deleted_at = 'deleted_at' in self._fields
        self._has_updated_at = 'updated_at' in self._fields

    # ==================== CREATE ====================

    @handle_exceptions
    def bulk_create(
        self,
        session: Session,
        records: List[Dict[str, Any]],
        *,
        batch_size: int = 1000,
    ) -> List[T]:
        """Toplu oluşturma. O(n)"""
        if not records:
            return []

        created = []
        for i in range(0, len(records), batch_size):
            batch = [self.model(**r) for r in records[i:i + batch_size]]
            session.add_all(batch)
            session.flush()
            created.extend(batch)

        return created

    # ==================== UPDATE ====================

    @handle_exceptions
    def bulk_update(
        self,
        session: Session,
        updates: List[Dict[str, Any]],
        *,
        batch_size: int = 1000,
    ) -> int:
        """ID'li toplu güncelleme. O(n)"""
        if not updates:
            return 0

        total = 0

        for i in range(0, len(updates), batch_size):
            batch = updates[i:i + batch_size]
            ids = [u['id'] for u in batch if 'id' in u]

            if not ids:
                continue

            obj_map = {o.id: o for o in self.get_many(session, ids)}

            for data in batch:
                obj = obj_map.get(data.get('id'))
                if not obj:
                    continue

                for k, v in data.items():
                    if k != 'id' and k in self._fields:
                        setattr(obj, k, v)
                total += 1

            session.flush()

        return total

    @handle_exceptions
    def bulk_update_where(
        self,
        session: Session,
        values: Dict[str, Any],
        **filters: Any,
    ) -> int:
        """Koşullu toplu güncelleme. O(1)"""
        if not values:
            return 0

        stmt = update(self.model)

        if self._has_soft_delete:
            stmt = stmt.where(self.model.is_deleted.is_(False))

        for k, v in filters.items():
            if k in self._fields:
                stmt = stmt.where(getattr(self.model, k) == v)

        final = dict(values)
        if self._has_updated_at:
            final['updated_at'] = datetime.now(timezone.utc)

        result = session.execute(stmt.values(**final))
        session.flush()
        return result.rowcount

    # ==================== DELETE ====================

    @handle_exceptions
    def bulk_delete(
        self,
        session: Session,
        record_ids: List[Any],
        *,
        batch_size: int = 1000,
    ) -> int:
        """Toplu hard delete. O(n/batch)"""
        if not record_ids:
            return 0

        total = 0

        for i in range(0, len(record_ids), batch_size):
            stmt = delete(self.model).where(
                self.model.id.in_(record_ids[i:i + batch_size])
            )
            if self._has_soft_delete:
                stmt = stmt.where(self.model.is_deleted.is_(False))

            total += session.execute(stmt).rowcount

        session.flush()
        return total

    @handle_exceptions
    def bulk_soft_delete(
        self,
        session: Session,
        record_ids: List[Any],
        *,
        batch_size: int = 1000,
    ) -> int:
        """Toplu soft delete. O(n/batch)"""
        if not record_ids:
            return 0

        if not self._has_soft_delete:
            raise DatabaseValidationError(
                field_name="is_deleted",
                message=f"{self.model_name} does not support soft delete"
            )

        now = datetime.now(timezone.utc)
        values = {'is_deleted': True}
        if self._has_deleted_at:
            values['deleted_at'] = now

        total = 0

        for i in range(0, len(record_ids), batch_size):
            stmt = (
                update(self.model)
                .where(self.model.id.in_(record_ids[i:i + batch_size]))
                .where(self.model.is_deleted.is_(False))
                .values(**values)
            )
            total += session.execute(stmt).rowcount

        session.flush()
        return total

    @handle_exceptions
    def bulk_restore(
        self,
        session: Session,
        record_ids: List[Any],
        *,
        batch_size: int = 1000,
    ) -> int:
        """Toplu restore. O(n/batch)"""
        if not record_ids:
            return 0

        if not self._has_soft_delete:
            raise DatabaseValidationError(
                field_name="is_deleted",
                message=f"{self.model_name} does not support restore"
            )

        values = {'is_deleted': False}
        if self._has_deleted_at:
            values['deleted_at'] = None

        total = 0

        for i in range(0, len(record_ids), batch_size):
            stmt = (
                update(self.model)
                .where(self.model.id.in_(record_ids[i:i + batch_size]))
                .where(self.model.is_deleted.is_(True))
                .values(**values)
            )
            total += session.execute(stmt).rowcount

        session.flush()
        return total