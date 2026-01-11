"""
QBitra Database Package
=======================

This package provides database functionality including:
- Configuration management
- Database engine and manager
- Repository patterns
- Model utilities
"""

from .config import (
    DatabaseConfig,
    DatabaseType,
    EngineConfig,
    get_database_config,
    get_sqlite_config,
    get_postgresql_config,
    get_mysql_config,
)
from .engine import (
    DatabaseEngine,
    DatabaseManager,
    get_database_manager,
    with_retry,
    with_session,
    with_transaction_session,
    with_readonly_session,
    with_retry_session,
)

with_transaction = with_transaction_session
from .models import (
    BaseModel,
    TimestampMixin,
    SoftDeleteMixin,
    AuditMixin,
    model_to_dict,
    models_to_list,
    model_to_json,
)
from .repos import (
    BaseRepository,
    BulkRepository,
    ExtraRepository,
    handle_exceptions,
)

__all__ = [
    # Config
    "DatabaseConfig",
    "DatabaseType",
    "EngineConfig",
    "get_database_config",
    "get_sqlite_config",
    "get_postgresql_config",
    "get_mysql_config",
    # Engine
    "DatabaseEngine",
    "DatabaseManager",
    "get_database_manager",
    "with_retry",
    # Decorators
    "with_session",
    "with_transaction",
    "with_transaction_session",
    "with_readonly_session",
    "with_retry_session",
    # Models
    "BaseModel",
    "TimestampMixin",
    "SoftDeleteMixin",
    "AuditMixin",
    "model_to_dict",
    "models_to_list",
    "model_to_json",
    # Repositories
    "BaseRepository",
    "BulkRepository",
    "ExtraRepository",
    "handle_exceptions",
]
