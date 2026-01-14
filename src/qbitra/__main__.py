"""
QBitra Backend - Ana Başlatıcı

Tek komut ile uygulamayı başlatır:
1. Environment handler'ı başlatır
2. Configuration handler'ı başlatır
3. Veritabanını yapılandırır ve bağlanır
4. Tabloları otomatik oluşturur (yoksa)
5. Sunucuyu başlatır
"""
from qbitra.utils.handlers.environment_handler import EnvironmentHandler
from qbitra.utils.handlers.configuration_handler import ConfigurationHandler
from qbitra.infrastructure.database.config import DatabaseConfig, DatabaseType
from qbitra.infrastructure.database.engine.manager import DatabaseManager
from qbitra.core.qbitra.qbitra import QBitra
from qbitra.core.qbitra_logger import get_logger

# Çekirdek startup logger'ı (logs/core/startup/service.log)
logger = get_logger("startup", parent_folder="core")


def initialize_handlers():
    """Environment ve Configuration handler'ları başlatır."""
    logger.info("Environment handler başlatılıyor...")
    EnvironmentHandler.init()
    
    logger.info("Configuration handler başlatılıyor...")
    ConfigurationHandler.init()


def initialize_database():
    """Veritabanı bağlantısını kurar ve tabloları oluşturur."""
    logger.info("Veritabanı yapılandırması okunuyor...")
    
    # Config'den DB tipini oku
    db_type_str = ConfigurationHandler.get_value_as_str("Database", "db_type", fallback="sqlite")
    db_type = DatabaseType(db_type_str.lower())
    
    # DB config oluştur
    if db_type == DatabaseType.SQLITE:
        sqlite_path = ConfigurationHandler.get_value_as_str("Database", "sqlite_path", fallback="./qbitra.db")
        db_name = ConfigurationHandler.get_value_as_str("Database", "db_name", fallback="qbitra")
        
        db_config = DatabaseConfig(
            db_type=db_type,
            db_name=db_name,
            sqlite_path=sqlite_path
        )
        logger.info(f"SQLite veritabanı: {sqlite_path}")
    
    elif db_type == DatabaseType.POSTGRESQL:
        db_config = DatabaseConfig(
            db_type=db_type,
            db_name=ConfigurationHandler.get_value_as_str("Database", "db_name"),
            host=ConfigurationHandler.get_value_as_str("Database", "db_host", fallback="localhost"),
            port=ConfigurationHandler.get_value_as_int("Database", "db_port", fallback=5432),
            username=ConfigurationHandler.get_value_as_str("Database", "db_user"),
            password=ConfigurationHandler.get_value_as_str("Database", "db_password")
        )
        logger.info(f"PostgreSQL veritabanı: {db_config.host}:{db_config.port}/{db_config.db_name}")
    
    elif db_type == DatabaseType.MYSQL:
        db_config = DatabaseConfig(
            db_type=db_type,
            db_name=ConfigurationHandler.get_value_as_str("Database", "db_name"),
            host=ConfigurationHandler.get_value_as_str("Database", "db_host", fallback="localhost"),
            port=ConfigurationHandler.get_value_as_int("Database", "db_port", fallback=3306),
            username=ConfigurationHandler.get_value_as_str("Database", "db_user"),
            password=ConfigurationHandler.get_value_as_str("Database", "db_password")
        )
        logger.info(f"MySQL veritabanı: {db_config.host}:{db_config.port}/{db_config.db_name}")
    
    else:
        raise ValueError(f"Desteklenmeyen veritabanı tipi: {db_type_str}")
    
    # Database Manager'ı başlat ve tabloları oluştur
    logger.info("Veritabanı bağlantısı kuruluyor...")
    db_manager = DatabaseManager()
    db_manager.initialize(
        config=db_config,
        auto_start=True,
        auto_create_tables=True  # Tablolar otomatik oluşturulacak
    )
    
    logger.info("Veritabanı başarıyla başlatıldı ve tablolar kontrol edildi")


def setup_app(qbitra: QBitra):
    """Router, middleware ve handler'ları ekler."""
    logger.info("Router, middleware ve handler'lar ekleniyor...")
    
    # Exception handler ekle
    from qbitra.api.middleware.exception_middleware import qbitra_exception_handler
    from qbitra.core.exceptions import QBitraException
    
    qbitra.add_exception_handler(QBitraException, qbitra_exception_handler)
    logger.info("Exception handler eklendi")
    
    # Logging middleware ekle (trace, correlation, session için)
    from qbitra.api.middleware.logging_middleware import LoggingMiddleware
    qbitra.add_middleware(LoggingMiddleware, log_requests=True)
    logger.info("Logging middleware eklendi")
    
    # Router'ları ekle
    from qbitra.api.routes.auth import router as auth_router
    qbitra.include_router(auth_router, prefix="/api")
    
    logger.info("Tüm router, middleware ve handler'lar eklendi")


def start_server():
    """QBitra sunucusunu başlatır."""
    logger.info("QBitra sunucusu başlatılıyor...")
    
    # QBitra uygulamasını oluştur
    qbitra = QBitra()
    app = qbitra.create_app()
    
    # Router, middleware ve handler'ları ekle
    setup_app(qbitra)
    
    # Sunucuyu başlat
    qbitra.run(app=app)


def main():
    """Ana başlatma fonksiyonu."""
    try:
        banner = "=" * 60
        print(banner)
        print("QBitra Backend başlatılıyor...")
        print(banner)
        logger.info(banner)
        logger.info("QBitra Backend başlatılıyor...")
        logger.info(banner)
        
        # 1. Handler'ları başlat
        initialize_handlers()
        
        # 2. Veritabanını başlat
        initialize_database()
        
        # 3. Sunucuyu başlat
        print("[QBITRA] Sunucu başlatılıyor (API ve servisler ayağa kalkıyor)...")
        start_server()
        
    except KeyboardInterrupt:
        print("[QBITRA] Uygulama durduruldu (Ctrl+C)")
        logger.info("Uygulama durduruldu (Ctrl+C)")
    except Exception as e:
        logger.error(f"Başlatma hatası: {e}", exc_info=True)
        raise
    else:
        # Normal sonlanma
        print("[QBITRA] Uygulama normal şekilde sonlandı.")
        logger.info("Uygulama normal şekilde sonlandı")


if __name__ == "__main__":
    main()
