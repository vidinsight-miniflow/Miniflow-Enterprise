"""
QBitra Exception Classes
========================

This module provides exception classes for the QBitra application.
All exceptions inherit from QBitraException base class.
"""

from .base import QBitraException
from .database import (
    DatabaseException,
    DatabaseConfigurationError,
    DatabaseValidationError,
    DatabaseConnectionError,
    DatabaseQueryError,
    DatabaseTransactionError,
    DatabaseSessionError,
    DatabaseEngineError,
    DatabaseManagerNotInitializedError,
    DatabaseManagerAlreadyInitializedError,
    DatabaseDecoratorManagerError,
    DatabaseDecoratorSignatureError,
    DatabaseResourceNotFoundError,
)

__all__ = [
    # Base exception
    "QBitraException",
    # Database exceptions
    "DatabaseException",
    "DatabaseConfigurationError",
    "DatabaseValidationError",
    "DatabaseConnectionError",
    "DatabaseQueryError",
    "DatabaseTransactionError",
    "DatabaseSessionError",
    "DatabaseEngineError",
    "DatabaseManagerNotInitializedError",
    "DatabaseManagerAlreadyInitializedError",
    "DatabaseDecoratorManagerError",
    "DatabaseDecoratorSignatureError",
    "DatabaseResourceNotFoundError",
]
