"""Model Mixin'leri: Timestamp, Soft Delete ve Audit logging."""

from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Boolean, String
from sqlalchemy.orm import declared_attr


def _utc_now() -> datetime:
    """Mevcut UTC zamanını timezone-aware datetime olarak döndürür."""
    return datetime.now(timezone.utc)


class TimestampMixin:
    """Otomatik created_at ve updated_at yönetimi."""
    
    __allow_unmapped__ = True

    @declared_attr
    def created_at(cls):
        return Column(
            DateTime(timezone=True),
            default=_utc_now,
            nullable=False,
        )

    @declared_attr
    def updated_at(cls):
        return Column(
            DateTime(timezone=True),
            default=_utc_now,
            onupdate=_utc_now,
            nullable=False,
        )


class SoftDeleteMixin:
    """Soft delete işlevselliği: is_deleted ve deleted_at."""
    
    __allow_unmapped__ = True

    @declared_attr
    def is_deleted(cls):
        return Column(Boolean, default=False, nullable=False)

    @declared_attr
    def deleted_at(cls):
        return Column(DateTime(timezone=True), nullable=True)

    def soft_delete(self) -> None:
        """Kaydı soft-delete olarak işaretler."""
        self.is_deleted = True
        self.deleted_at = _utc_now()

    def restore(self) -> None:
        """Soft-delete edilmiş kaydı geri yükler."""
        self.is_deleted = False
        self.deleted_at = None


class AuditMixin:
    """Audit alanları: created_by ve updated_by."""
    
    __allow_unmapped__ = True

    @declared_attr
    def created_by(cls):
        return Column(String(255), nullable=True)

    @declared_attr
    def updated_by(cls):
        return Column(String(255), nullable=True)