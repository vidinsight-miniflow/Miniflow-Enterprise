"""
BASE MODEL - Tüm Veritabanı Modelleri İçin Temel Sınıf
=====================================================

Amaç:
    - Tüm veritabanı modelleri için ortak fonksiyonalite sağlar
    - ID üretimi, timestamp yönetimi, soft delete ve audit trail özelliklerini içerir
    - SQLAlchemy ORM ile veritabanı işlemlerini kolaylaştırır

Özellikler:
    - Otomatik ID Üretimi: Her model için prefix'li benzersiz ID (örn: USR-ABC123...)
    - Timestamps: created_at ve updated_at otomatik yönetimi
    - Audit Trail: created_by, updated_by ile değişiklik takibi
    - Soft Delete: is_deleted, deleted_at, deleted_by ile güvenli silme
    - Serialization: to_dict() metodu ile JSON'a dönüşüm

ID Format:
    - Prefix: 3 karakter (örn: USR, WSP, WFL)
    - Separator: 1 karakter (-)
    - UUID: 16 karakter (hexadecimal)
    - Toplam: 20 karakter (örn: USR-A1B2C3D4E5F6G7H8)

Kullanım:
    class MyModel(BaseModel):
        __prefix__ = "MDL"  # Model prefix'i (3 karakter zorunlu)
        __tablename__ = 'my_models'
        # ... diğer kolonlar

Not:
    - Bu sınıf abstract'tır, doğrudan kullanılmaz
    - Tüm model sınıfları bu sınıftan türetilmelidir
"""

import uuid
import enum
from typing import cast, Iterable, Any
from datetime import datetime, timezone
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, String, DateTime, Boolean

from miniflow.core.exceptions import InvalidInputError

# SQLAlchemy declarative base for all models
Base = declarative_base()


class BaseModel(Base):
    """Abstract base model with common functionality for all entities"""
    __abstract__ = True
    __allow_unmapped__ = True

    # =============================================================================== ID GENERATION METHOD FOR ALL =====
    @classmethod
    def _generate_id(cls):
        """
        Generate unique ID with class-specific prefix.
        
        Format: {PREFIX}-{UUID}
        - PREFIX: 3-character model identifier (e.g., USR, WSP, WFL)
        - UUID: 16-character hexadecimal string
        - Total: 20 characters
        
        Example: USR-A1B2C3D4E5F6G7H8
        
        Raises:
            InvalidInputError: If prefix is not exactly 3 characters
        """
        prefix = getattr(cls, '__prefix__', 'XXX')  # Get class prefix (e.g., 'USR' for User)
        
        # Validate prefix length (must be exactly 3 characters)
        if len(prefix) != 3:
            raise InvalidInputError(field_name="__prefix__")
        
        # Generate 16-character UUID suffix (uppercase hexadecimal)
        uuid_suffix = str(uuid.uuid4()).replace('-', '')[:16].upper()
        
        return f"{prefix}-{uuid_suffix}"

    # ============================================================================= DEFAULT COLUMNS FOR ALL TABLES =====
    # Primary key with auto-generated ID (3-char prefix + '-' + 16-char UUID = 20 chars)
    id = Column(
        String(20),  # Format: PREFIX-UUID (e.g., USR-A1B2C3D4E5F6G7H8)
        primary_key=True
    )

    # Timestamps with automatic updates
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Audit Trail - Track who created/updated records
    created_by = Column(
        String(20),
        nullable=True
    )

    updated_by = Column(
        String(20),
        nullable=True
    )

    # Soft Delete - Mark records as deleted without removing them
    is_deleted = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True
    )

    deleted_at = Column(
        DateTime,
        nullable=True
    )

    deleted_by = Column(
        String(20),
        nullable=True
    )

    restored_by = Column(
        String(20),
        nullable=True
    )

    restored_at = Column(
        DateTime,
        nullable=True
    )

    # ========================================================================================= CONSTRUCTOR METHOD =====
    def __init__(self, **kwargs):
        """Initialize the model with auto-generated ID if not provided"""
        # Auto-generate ID if not provided (uses class-specific prefix)
        if 'id' not in kwargs or kwargs['id'] is None:
            kwargs['id'] = self._generate_id()
        super().__init__(**kwargs)

    # ======================================================================================= BASE METHODS FOR ALL =====
    def __repr__(self) -> str:
        """Return string representation of the model instance"""
        return f"<{self.__class__.__name__}(id={self.id})>"

    def to_dict(self, exclude_fields=None, include_properties=False) -> dict:
        """
        Convert model instance to dictionary representation.
        
        Serializes ONLY table columns, NOT relationships.
        This prevents N+1 query problems and lazy loading issues.
        
        For serializing relationships, handle them explicitly in your
        service/controller layer where you have full control over
        the query strategy and can use proper eager loading.
        
        Args:
            exclude_fields: List of field names to exclude from serialization
            include_properties: If True, include @property attributes
        
        Returns:
            Dictionary with column values (no relationships)
            
        Examples:
            # Basic serialization (only columns)
            user_data = user.to_dict()
            
            # Exclude sensitive fields
            user_data = user.to_dict(exclude_fields=['hashed_password'])
            
            # Include computed properties
            user_data = user.to_dict(include_properties=True)
            
            # For relationships, handle explicitly:
            user_data = user.to_dict()
            user_data['auth_sessions'] = [
                session.to_dict() for session in user.auth_sessions
            ]
        """
        result = {}
        exclude_fields = exclude_fields or []

        # Process table columns - cast() helps type checker understand SQLAlchemy collections
        columns = cast(Iterable[Any], self.__table__.c)
        for column in columns:
            field_name = column.name
            if field_name in exclude_fields:
                continue

            try:
                # Get column value and serialize it
                value = getattr(self, field_name)
                result[field_name] = BaseModel._serialize_value(value)
            except (AttributeError, TypeError, ValueError):
                # Skip problematic fields silently
                continue

        # Process @property attributes if requested
        if include_properties:
            for name in dir(self.__class__):
                # Skip private attributes
                if name.startswith('_'):
                    continue

                if name in exclude_fields:
                    continue

                # Check if it's a property and serialize it
                attr = getattr(self.__class__, name, None)
                if isinstance(attr, property):
                    try:
                        value = getattr(self, name)
                        result[name] = BaseModel._serialize_value(value)
                    except (AttributeError, TypeError, ValueError):
                        # Skip problematic properties silently
                        continue

        return result

    @staticmethod
    def _serialize_value(value):
        """Serialize individual values to JSON-safe format"""
        if value is None:
            return None
        elif isinstance(value, datetime):
            # Convert datetime to ISO format string
            return value.isoformat()
        elif isinstance(value, enum.Enum):
            # Convert enum to its value
            return value.value
        elif isinstance(value, (int, float, str, bool, list, dict)):
            # Already JSON-safe types
            return value
        else:
            try:
                # Try to convert to string as fallback
                return str(value)
            except (TypeError, ValueError):
                # Return None if conversion fails
                return None