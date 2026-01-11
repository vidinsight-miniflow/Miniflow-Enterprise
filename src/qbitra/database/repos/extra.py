from typing import Any, Dict, List, Optional, Set, Tuple
from datetime import datetime, timezone

from sqlalchemy import select, update, func, asc, desc
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select

from qbitra.core.exceptions import DatabaseValidationError
from .base import BaseRepository, handle_exceptions, T


class ExtraRepository(BaseRepository[T]):
    """Pagination ve sayısal işlemler için repository."""

    def __init__(self, model: type[T]):
        super().__init__(model)
        self._fields: Set[str] = {c.name for c in model.__table__.columns}
        self._has_soft_delete = 'is_deleted' in self._fields
        self._has_updated_at = 'updated_at' in self._fields

    def _apply_filters(
        self,
        query: Select,
        filters: Dict[str, Any],
        include_deleted: bool = False,
    ) -> Select:
        """Filtreleri uygular. O(f) - f=filter sayısı."""
        if self._has_soft_delete and not include_deleted:
            query = query.where(self.model.is_deleted.is_(False))

        for k, v in filters.items():
            if k in self._fields:
                query = query.where(getattr(self.model, k) == v)

        return query

    # ==================== PAGINATION ====================

    @handle_exceptions
    def paginate(
        self,
        session: Session,
        *,
        page: int = 1,
        per_page: int = 20,
        order_by: Optional[str] = None,
        order_desc: bool = False,
        include_deleted: bool = False,
        **filters: Any,
    ) -> Dict[str, Any]:
        """Sayfalı listeleme. O(limit)"""
        page = max(1, page)
        per_page = max(1, per_page)

        # Count - O(1)
        count_query = select(func.count(self.model.id))
        count_query = self._apply_filters(count_query, filters, include_deleted)
        total = session.execute(count_query).scalar()

        # Items
        query = select(self.model)
        query = self._apply_filters(query, filters, include_deleted)

        if order_by and order_by in self._fields:
            col = getattr(self.model, order_by)
            query = query.order_by(desc(col) if order_desc else asc(col))

        offset = (page - 1) * per_page
        items = list(session.execute(query.offset(offset).limit(per_page)).scalars().all())

        pages = (total + per_page - 1) // per_page if total else 0

        return {
            'items': items,
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': pages,
            'has_next': page < pages,
            'has_prev': page > 1,
        }

    @handle_exceptions
    def find(
        self,
        session: Session,
        *,
        order_by: Optional[str] = None,
        order_desc: bool = False,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        include_deleted: bool = False,
        **filters: Any,
    ) -> List[T]:
        """Filtreli listeleme. O(limit)"""
        query = select(self.model)
        query = self._apply_filters(query, filters, include_deleted)

        if order_by and order_by in self._fields:
            col = getattr(self.model, order_by)
            query = query.order_by(desc(col) if order_desc else asc(col))

        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)

        return list(session.execute(query).scalars().all())

    @handle_exceptions
    def find_one(
        self,
        session: Session,
        *,
        include_deleted: bool = False,
        **filters: Any,
    ) -> Optional[T]:
        """Tek kayıt bul. O(1)"""
        query = select(self.model)
        query = self._apply_filters(query, filters, include_deleted)
        return session.execute(query.limit(1)).scalar()

    @handle_exceptions
    def count_where(
        self,
        session: Session,
        *,
        include_deleted: bool = False,
        **filters: Any,
    ) -> int:
        """Koşullu sayım. O(1)"""
        query = select(func.count(self.model.id))
        query = self._apply_filters(query, filters, include_deleted)
        return session.execute(query).scalar()

    # ==================== INCREMENT / DECREMENT ====================

    @handle_exceptions
    def increment(
        self,
        session: Session,
        record_id: Any,
        field: str,
        amount: int = 1,
    ) -> T:
        """Sayısal alan artırma. O(1)"""
        return self._adjust(session, record_id, field, abs(amount))

    @handle_exceptions
    def decrement(
        self,
        session: Session,
        record_id: Any,
        field: str,
        amount: int = 1,
        *,
        allow_negative: bool = False,
    ) -> T:
        """Sayısal alan azaltma. O(1)"""
        return self._adjust(session, record_id, field, -abs(amount), allow_negative)

    def _adjust(
        self,
        session: Session,
        record_id: Any,
        field: str,
        amount: int,
        allow_negative: bool = True,
    ) -> T:
        """Atomik alan ayarlama. O(1)"""
        if field not in self._fields:
            raise DatabaseValidationError(
                field_name=field,
                message=f"Field '{field}' not found"
            )

        col = getattr(self.model, field)
        values = {field: col + amount}

        if self._has_updated_at:
            values['updated_at'] = datetime.now(timezone.utc)

        stmt = update(self.model).where(self.model.id == record_id)

        if not allow_negative and amount < 0:
            stmt = stmt.where(col >= abs(amount))

        result = session.execute(stmt.values(**values))

        if result.rowcount == 0:
            # Neden 0? Kayıt yok mu, değer yetersiz mi?
            exists = self.exists(session, record_id)
            if not exists:
                raise self._not_found(record_id)
            raise DatabaseValidationError(
                field_name=field,
                message=f"Insufficient {field} value"
            )

        session.flush()
        session.expire_all()  # Cache temizle
        return session.get(self.model, record_id)

    # ==================== AGGREGATE ====================

    @handle_exceptions
    def sum(
        self,
        session: Session,
        field: str,
        *,
        include_deleted: bool = False,
        **filters: Any,
    ) -> float:
        """Alan toplamı. O(1)"""
        if field not in self._fields:
            raise DatabaseValidationError(
                field_name=field,
                message=f"Field '{field}' not found"
            )

        query = select(func.coalesce(func.sum(getattr(self.model, field)), 0))
        query = self._apply_filters(query, filters, include_deleted)
        return session.execute(query).scalar()

    @handle_exceptions
    def avg(
        self,
        session: Session,
        field: str,
        *,
        include_deleted: bool = False,
        **filters: Any,
    ) -> Optional[float]:
        """Alan ortalaması. O(1)"""
        if field not in self._fields:
            raise DatabaseValidationError(
                field_name=field,
                message=f"Field '{field}' not found"
            )

        query = select(func.avg(getattr(self.model, field)))
        query = self._apply_filters(query, filters, include_deleted)
        return session.execute(query).scalar()

    @handle_exceptions
    def min_max(
        self,
        session: Session,
        field: str,
        *,
        include_deleted: bool = False,
        **filters: Any,
    ) -> Tuple[Any, Any]:
        """Min/Max değerleri. O(1)"""
        if field not in self._fields:
            raise DatabaseValidationError(
                field_name=field,
                message=f"Field '{field}' not found"
            )

        col = getattr(self.model, field)
        query = select(func.min(col), func.max(col))
        query = self._apply_filters(query, filters, include_deleted)
        row = session.execute(query).one()
        return (row[0], row[1])