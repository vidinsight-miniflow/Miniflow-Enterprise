from typing import Optional
from dataclasses import replace

from .engine_config_presets import DB_ENGINE_CONFIGS
from .database_type import DatabaseType
from .database_config import DatabaseConfig
from .engine_config import EngineConfig
from miniflow.core.exceptions import DatabaseConfigurationError


def get_database_config(
        database_name: str,
        db_type: DatabaseType,
        host: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        sqlite_path: Optional[str] = None,
        custom_engine_config: Optional[EngineConfig] = None
) -> DatabaseConfig:
    """Genel veritabanı konfigürasyon oluşturucu.

    Diğer `get_*_config` fonksiyonları bu fonksiyon üzerine kuruludur.

    Algoritma:
      1) Engine konfigürasyonunu belirle (custom varsa onu, yoksa preset)
      2) DatabaseConfig örneğini oluştur ve döndür

    Args:
        database_name: Veritabanı adı
        db_type: Veritabanı tipi
        host: Sunucu adresi (MySQL/PostgreSQL için zorunlu)
        port: Sunucu portu (MySQL/PostgreSQL için zorunlu)
        username: Kullanıcı adı (MySQL/PostgreSQL için zorunlu)
        password: Şifre (MySQL/PostgreSQL için zorunlu)
        sqlite_path: SQLite dosya yolu (opsiyonel)
        custom_engine_config: Özel engine konfigürasyonu (opsiyonel)

    Returns:
        Belirtilen parametrelerle oluşturulmuş `DatabaseConfig` örneği

    Raises:
        DatabaseConfigurationError: Desteklenmeyen veritabanı tipi için preset bulunamazsa
    """
    # 1) Engine konfigürasyonunu belirle
    if custom_engine_config is not None:
        engine_config = custom_engine_config
    else:
        preset = DB_ENGINE_CONFIGS.get(db_type)
        if preset is None:
            raise DatabaseConfigurationError(config_name={"db_type": db_type.value})
        # Copy preset to avoid shared state mutations between callers
        engine_config = replace(preset, connect_args=dict(preset.connect_args or {}))

    # 2) DatabaseConfig örneğini oluştur
    # SQLite için db_name ve sqlite_path aynı olmalı
    final_db_name = database_name if db_type == DatabaseType.SQLITE else database_name
    final_sqlite_path = None
    if db_type == DatabaseType.SQLITE:
        final_sqlite_path = sqlite_path if sqlite_path is not None else database_name
        final_db_name = final_sqlite_path  # SQLite için db_name=sqlite_path
    
    return DatabaseConfig(
        db_name=final_db_name,
        db_type=db_type,
        host=host if host is not None else "localhost",
        port=port,
        username=username,
        password=password,
        sqlite_path=final_sqlite_path,
        engine_config=engine_config,
    )


# =========================================================================================== SQLITE FACTORY FUNCTION ==

def get_sqlite_config(database_name: str = "miniflow") -> DatabaseConfig:
    """SQLite için optimize konfigürasyon oluşturur.

    SQLite için ideal kullanım:
      - Development ve testing
      - Küçük uygulamalar / prototipler / embedded sistemler

    Args:
        database_name: SQLite veritabanı dosya adı (uzantı gerekmez)

    Returns:
        `DatabaseConfig` (SQLite)
    """
    return get_database_config(db_type=DatabaseType.SQLITE, database_name=database_name)


# ======================================================================================= POSTGRESQL FACTORY FUNCTION ==

def get_postgresql_config(
        database_name: str = "miniflow",
        host: str = "localhost",
        port: int = 5432,
        username: str = "postgres",
        password: str = "password"
) -> DatabaseConfig:
    """PostgreSQL için optimize konfigürasyon oluşturur.

    PostgreSQL ideal kullanım:
      - Enterprise uygulamalar
      - Yüksek eşzamanlılık
      - Karmaşık sorgular
      - ACID gerektiren sistemler

    Args:
        database_name: Veritabanı adı
        host: Sunucu adresi
        port: Sunucu portu (varsayılan: 5432)
        username: Kullanıcı adı
        password: Şifre

    Returns:
        `DatabaseConfig` (PostgreSQL)
    """
    return get_database_config(
        db_type=DatabaseType.POSTGRESQL,
        database_name=database_name,
        host=host,
        port=port,
        username=username,
        password=password,
    )


# ============================================================================================ MYSQL FACTORY FUNCTION ==

def get_mysql_config(
        database_name: str = "miniflow",
        host: str = "localhost",
        port: int = 3306,
        username: str = "root",
        password: str = "password"
) -> DatabaseConfig:
    """MySQL için optimize konfigürasyon oluşturur.

    MySQL ideal kullanım:
      - Web uygulamaları / CMS
      - E-commerce platformları
      - Blog ve forum sistemleri

    Args:
        database_name: Veritabanı adı
        host: Sunucu adresi
        port: Sunucu portu (varsayılan: 3306)
        username: Kullanıcı adı
        password: Şifre

    Returns:
        `DatabaseConfig` (MySQL)
    """
    return get_database_config(
        db_type=DatabaseType.MYSQL,
        database_name=database_name,
        host=host,
        port=port,
        username=username,
        password=password,
    )
