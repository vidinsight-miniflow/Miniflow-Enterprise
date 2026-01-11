"""
Database Models Package
======================

This package provides base model classes, mixins, and serialization utilities
for SQLAlchemy models.
"""

from .base import BaseModel
from .mixins import TimestampMixin, SoftDeleteMixin, AuditMixin
from .serializations import model_to_dict, models_to_list, model_to_json

# Metadata'yı merkezi olarak export et
# Tüm BaseModel'den türeyen modeller bu metadata'yı kullanır

metadata = BaseModel.metadata

__all__ = [
    # Base model
    "BaseModel",
    # Metadata (merkezi erişim)
    "metadata",
    # Mixins
    "TimestampMixin",
    "SoftDeleteMixin",
    "AuditMixin",
    # Serialization functions
    "model_to_dict",
    "models_to_list",
    "model_to_json",
]
