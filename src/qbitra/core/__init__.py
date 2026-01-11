"""
QBitra Core Package
==================

This package provides core functionality for the QBitra application including:
- Exception handling
- Logging system
- Core utilities
"""

# Exceptions
from .exceptions import (
    QBitraException,
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

# Logger
from .logger import (
    setup_logger,
    configure_logger,
    setup_console_logger,
    setup_file_logger,
    HandlerConfig,
    TraceContextFilter,
    AsyncHandler,
    AsyncConsoleHandler,
    AsyncRotatingFileHandler,
    JSONFormatter,
    PrettyFormatter,
    CompactFormatter,
    create_formatter,
    TraceContext,
    trace,
    get_current_context,
    set_current_context,
    clear_current_context,
    create_trace,
    with_trace,
)

# Logger convenience functions
from .qbitra_logger import get_logger, shutdown_logger

__all__ = [
    # Exceptions
    "QBitraException",
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
    # Logger Core
    "setup_logger",
    "configure_logger",
    "setup_console_logger",
    "setup_file_logger",
    "HandlerConfig",
    "TraceContextFilter",
    # Logger Handlers
    "AsyncHandler",
    "AsyncConsoleHandler",
    "AsyncRotatingFileHandler",
    # Logger Formatters
    "JSONFormatter",
    "PrettyFormatter",
    "CompactFormatter",
    "create_formatter",
    # Logger Context
    "TraceContext",
    "trace",
    "get_current_context",
    "set_current_context",
    "clear_current_context",
    "create_trace",
    # Logger Decorators
    "with_trace",
    # Logger Convenience
    "get_logger",
    "shutdown_logger",
]
