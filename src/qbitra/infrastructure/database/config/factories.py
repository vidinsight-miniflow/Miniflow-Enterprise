from typing import Optional
from dataclasses import replace

from qbitra.infrastructure.database.config.predefined_engine_configs import DB_ENGINE_CONFIGS
from qbitra.infrastructure.database.config.database_type import DatabaseType
from qbitra.infrastructure.database.config.database_config import DatabaseConfig
from qbitra.infrastructure.database.config.engine_config import EngineConfig
from qbitra.core.exceptions import DatabaseConfigurationError


def get_database_config(
    database_name: str,
    db_type: DatabaseType,
    host: Optional[str] = None,
    port: Optional[int] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    sqlite_path: Optional[str] = None,
    custom_engine_config: Optional[EngineConfig] = None,
) -> DatabaseConfig:
    """Veritabanı konfigürasyonu oluşturur."""
    # Engine config: custom veya preset
    if custom_engine_config is not None:
        engine_config = custom_engine_config
    else:
        preset = DB_ENGINE_CONFIGS.get(db_type)
        if preset is None:
            raise DatabaseConfigurationError(
                config_name="db_type",
                error_details={"db_type": db_type.value}
            )
        engine_config = replace(preset, connect_args=dict(preset.connect_args or {}))

    # SQLite için path ayarla
    final_sqlite_path = None
    if db_type == DatabaseType.SQLITE:
        final_sqlite_path = sqlite_path or database_name

    return DatabaseConfig(
        db_name=database_name,
        db_type=db_type,
        host=host or "localhost",
        port=port,
        username=username,
        password=password,
        sqlite_path=final_sqlite_path,
        engine_config=engine_config,
    )


def get_sqlite_config(database_name: str = "miniflow.db") -> DatabaseConfig:
    """SQLite konfigürasyonu oluşturur."""
    return get_database_config(db_type=DatabaseType.SQLITE, database_name=database_name)


def get_postgresql_config(
    database_name: str = "miniflow",
    host: str = "localhost",
    port: int = 5432,
    username: str = "postgres",
    password: str = "password",
) -> DatabaseConfig:
    """PostgreSQL konfigürasyonu oluşturur."""
    return get_database_config(
        db_type=DatabaseType.POSTGRESQL,
        database_name=database_name,
        host=host,
        port=port,
        username=username,
        password=password,
    )


def get_mysql_config(
    database_name: str = "miniflow",
    host: str = "localhost",
    port: int = 3306,
    username: str = "root",
    password: str = "password",
) -> DatabaseConfig:
    """MySQL konfigürasyonu oluşturur."""
    return get_database_config(
        db_type=DatabaseType.MYSQL,
        database_name=database_name,
        host=host,
        port=port,
        username=username,
        password=password,
    )