"""
Database Repositories Package
=============================

This package provides base repository classes for CRUD operations,
bulk operations, and advanced querying.
"""

from .base import BaseRepository, handle_exceptions
from .bulk import BulkRepository
from .extra import ExtraRepository

__all__ = [
    "BaseRepository",
    "BulkRepository",
    "ExtraRepository",
    "handle_exceptions",
]
