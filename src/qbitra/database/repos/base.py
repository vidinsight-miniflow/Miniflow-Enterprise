"""Base Repository - Minimal CRUD Operations."""

from typing import Any, Generic, List, Optional, TypeVar
from functools import wraps
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.orm import DeclarativeBase, Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from qbitra.core.exceptions import (
    DatabaseQueryError,
    DatabaseValidationError,
    DatabaseResourceNotFoundError,
)


T = TypeVar("T", bound=DeclarativeBase)


def handle_exceptions(func):
    """Database exception handler."""
    @wraps(func)
    def wrapper(self, session: Session, *args, **kwargs):
        try:
            return func(self, session, *args, **kwargs)
        except IntegrityError as e:
            session.rollback()
            raise DatabaseValidationError(
                field_name="constraint",
                message=f"Constraint violation: {e.orig}",
                cause=e
            ) from e
        except SQLAlchemyError as e:
            session.rollback()
            raise DatabaseQueryError(
                message=f"Database query error: {e}",
                cause=e
            ) from e
    return wrapper


class BaseRepository(Generic[T]):
    """Base CRUD repository."""

    def __init__(self, model: type[T]):
        self.model = model
        self.model_name = model.__name__

    def _not_found(self, record_id: Any) -> DatabaseResourceNotFoundError:
        return DatabaseResourceNotFoundError(
            resource_name=self.model_name,
            resource_id=str(record_id)
        )

    def _soft_delete_filter(self, query, include_deleted: bool = False):
        if not include_deleted and hasattr(self.model, 'is_deleted'):
            return query.where(self.model.is_deleted.is_(False))
        return query

    # ==================== CREATE ====================

    @handle_exceptions
    def create(self, session: Session, **data: Any) -> T:
        """Create a new record."""
        obj = self.model(**data)
        session.add(obj)
        session.flush()
        return obj

    # ==================== READ ====================

    @handle_exceptions
    def get(
        self,
        session: Session,
        record_id: Any,
        *,
        include_deleted: bool = False,
    ) -> Optional[T]:
        """Get record by ID. Returns None if not found."""
        obj = session.get(self.model, record_id)
        
        if obj and not include_deleted and getattr(obj, 'is_deleted', False):
            return None
        
        return obj

    @handle_exceptions
    def get_or_raise(
        self,
        session: Session,
        record_id: Any,
        *,
        include_deleted: bool = False,
    ) -> T:
        """Get record by ID. Raises if not found."""
        obj = self.get(session, record_id, include_deleted=include_deleted)
        if obj is None:
            raise self._not_found(record_id)
        return obj

    @handle_exceptions
    def get_many(
        self,
        session: Session,
        record_ids: List[Any],
        *,
        include_deleted: bool = False,
    ) -> List[T]:
        """Get multiple records by IDs."""
        if not record_ids:
            return []
        
        query = select(self.model).where(self.model.id.in_(record_ids))
        query = self._soft_delete_filter(query, include_deleted)
        return list(session.execute(query).scalars().all())

    @handle_exceptions
    def get_all(
        self,
        session: Session,
        *,
        include_deleted: bool = False,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[T]:
        """Get all records with optional pagination."""
        query = select(self.model)
        query = self._soft_delete_filter(query, include_deleted)
        
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        
        return list(session.execute(query).scalars().all())

    # ==================== UPDATE ====================

    @handle_exceptions
    def update(
        self,
        session: Session,
        record_id: Any,
        **data: Any,
    ) -> T:
        """Update a record."""
        obj = self.get_or_raise(session, record_id)
        
        for key, value in data.items():
            if hasattr(obj, key):
                setattr(obj, key, value)
        
        session.flush()
        return obj

    @handle_exceptions
    def bulk_update(
        self,
        session: Session,
        filters: dict[str, Any],
        **data: Any,
    ) -> int:
        """Update multiple records matching filters. Returns affected count."""
        stmt = update(self.model)
        
        for field, value in filters.items():
            if hasattr(self.model, field):
                stmt = stmt.where(getattr(self.model, field) == value)
        
        stmt = stmt.values(**data)
        result = session.execute(stmt)
        session.flush()
        return result.rowcount

    # ==================== DELETE ====================

    @handle_exceptions
    def delete(self, session: Session, record_id: Any) -> T:
        """Hard delete a record."""
        obj = self.get_or_raise(session, record_id)
        session.delete(obj)
        session.flush()
        return obj

    @handle_exceptions
    def soft_delete(self, session: Session, record_id: Any) -> T:
        """Soft delete a record."""
        obj = self.get_or_raise(session, record_id)
        
        if not hasattr(obj, 'is_deleted'):
            raise DatabaseValidationError(
                field_name="is_deleted",
                message=f"{self.model_name} does not support soft delete"
            )
        
        obj.is_deleted = True
        if hasattr(obj, 'deleted_at'):
            obj.deleted_at = datetime.now(timezone.utc)
        
        session.flush()
        return obj

    @handle_exceptions
    def restore(self, session: Session, record_id: Any) -> T:
        """Restore a soft-deleted record."""
        obj = self.get_or_raise(session, record_id, include_deleted=True)
        
        if not getattr(obj, 'is_deleted', False):
            raise DatabaseValidationError(
                field_name="is_deleted",
                message=f"{self.model_name} '{record_id}' is not deleted"
            )
        
        obj.is_deleted = False
        if hasattr(obj, 'deleted_at'):
            obj.deleted_at = None
        
        session.flush()
        return obj

    # ==================== UTILS ====================

    @handle_exceptions
    def count(
        self,
        session: Session,
        *,
        include_deleted: bool = False,
    ) -> int:
        """Count all records."""
        query = select(self.model)
        query = self._soft_delete_filter(query, include_deleted)
        return len(session.execute(query).scalars().all())

    @handle_exceptions
    def exists(self, session: Session, record_id: Any) -> bool:
        """Check if record exists."""
        return self.get(session, record_id) is not None