from qbitra.infrastructure.database.config.database_type import DatabaseType
from qbitra.infrastructure.database.config.engine_config import EngineConfig


# Her veritabanı tipi için önerilen EngineConfig ayarları
DB_ENGINE_CONFIGS = {

    # SQLite - Dosya tabanlı, test ve küçük projeler için
    DatabaseType.SQLITE: EngineConfig(
        pool_size=1,
        max_overflow=0,
        pool_timeout=20,
        pool_recycle=0,
        pool_pre_ping=False,
        connect_args={
            'check_same_thread': False,
            'timeout': 20,
        },
    ),

    # PostgreSQL - Production ortamları için
    DatabaseType.POSTGRESQL: EngineConfig(
        pool_size=20,
        max_overflow=30,
        pool_timeout=60,
        pool_recycle=3600,
        pool_pre_ping=True,
        connect_args={
            'connect_timeout': 30,
            'sslmode': 'require',
            'application_name': 'miniflow_app',
        },
        isolation_level='READ_COMMITTED',
    ),

    # MySQL - Web uygulamaları ve API sistemleri için
    DatabaseType.MYSQL: EngineConfig(
        pool_size=15,
        max_overflow=25,
        pool_timeout=45,
        pool_recycle=7200,
        pool_pre_ping=True,
        connect_args={
            'connect_timeout': 30,
        },
        isolation_level='READ_COMMITTED',
    ),
}