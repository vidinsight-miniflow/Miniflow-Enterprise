import os
import sys
from contextlib import asynccontextmanager
from typing import Optional

from qbitra.core.qbitra_logger import get_logger
from qbitra.utils.handlers.environment_handler import EnvironmentHandler
from qbitra.utils.handlers.configuration_handler import ConfigurationHandler

# DatabaseType enum'ını import et
from qbitra.database.config.database_type import DatabaseType
from qbitra.database.config.factories import get_database_config
from qbitra.database.engine.manager import DatabaseManager
from qbitra.core.exceptions import DatabaseConfigurationError, DatabaseValidationError


class QBitraBootstrap:    
    _initialized = False
    _logger = get_logger("core")
    is_running = False

    _database_manager = None

    def _setup_environment_handler(self) -> bool:
        try:
            self._logger.debug("Environment Handler başlatılıyor...")
            if not EnvironmentHandler.is_initialized():
                EnvironmentHandler.init()
            self._logger.info("Environment Handler başarıyla başlatıldı")
            return True
        except Exception as e:
            self._logger.error(f"Environment Handler başlatılırken hata oluştu: {e}")
            return False

    def _setup_configuration_handler(self) -> bool:
        try:
            self._logger.debug("Configuration Handler başlatılıyor...")
            if not ConfigurationHandler.is_initialized():
                ConfigurationHandler.init()
            self._logger.info("Configuration Handler başarıyla başlatıldı")
            return True
        except Exception as e:
            self._logger.error(f"Configuration Handler başlatılırken hata oluştu: {e}")
            return False

    def _setup_database_manager(self) -> bool:
        try:
            self._logger.debug("Database Manager başlatılıyor...")

            # ConfigurationHandler'ın başlatıldığına emin ol
            if not ConfigurationHandler.is_initialized():
                self._logger.error("Önce Configuration Handler başlatılmalı!")
                raise DatabaseConfigurationError(
                    config_name="configuration_handler",
                    message="Configuration Handler başlatılmadan Database Manager başlatılamaz"
                )

            # Database tipini al (zorunlu)
            db_type_str = ConfigurationHandler.get_value_as_str("Database", "db_type")
            if not db_type_str:
                self._logger.error("Config dosyasında 'db_type' değeri bulunamadı")
                raise DatabaseConfigurationError(
                    config_name="db_type",
                    message="Config dosyasında [Database] bölümünde 'db_type' değeri zorunludur"
                )
            
            db_type_str = db_type_str.lower()
            self._logger.debug(f"Veritabanı tipi: {db_type_str}")

            # DatabaseType'ı belirle
            db_type_map = {
                "sqlite": DatabaseType.SQLITE,
                "postgresql": DatabaseType.POSTGRESQL,
                "postgres": DatabaseType.POSTGRESQL,
                "mysql": DatabaseType.MYSQL,
            }
            
            db_type = db_type_map.get(db_type_str)
            if not db_type:
                self._logger.error(f"Geçersiz veritabanı tipi: {db_type_str}. Desteklenen: sqlite, postgresql, mysql")
                raise DatabaseConfigurationError(
                    config_name="db_type",
                    message=f"Geçersiz veritabanı tipi: '{db_type_str}'. Desteklenen değerler: sqlite, postgresql, mysql"
                )

            # Database config oluştur
            db_config = None

            if db_type == DatabaseType.SQLITE:
                # SQLite için zorunlu alanlar
                sqlite_path = ConfigurationHandler.get_value_as_str("Database", "sqlite_path")
                if not sqlite_path:
                    self._logger.error("Config dosyasında 'sqlite_path' değeri bulunamadı")
                    raise DatabaseConfigurationError(
                        config_name="sqlite_path",
                        message="SQLite kullanımı için [Database] bölümünde 'sqlite_path' değeri zorunludur"
                    )
                
                db_name = ConfigurationHandler.get_value_as_str("Database", "db_name")
                if not db_name:
                    self._logger.error("Config dosyasında 'db_name' değeri bulunamadı")
                    raise DatabaseConfigurationError(
                        config_name="db_name",
                        message="[Database] bölümünde 'db_name' değeri zorunludur"
                    )
                
                self._logger.debug(f"SQLite dosya yolu: {sqlite_path}, DB adı: {db_name}")
                
                db_config = get_database_config(
                    database_name=db_name,
                    db_type=db_type,
                    sqlite_path=sqlite_path
                )

            elif db_type == DatabaseType.POSTGRESQL:
                # PostgreSQL için zorunlu alanlar
                host = ConfigurationHandler.get_value_as_str("Database", "db_host")
                if not host:
                    self._logger.error("Config dosyasında 'db_host' değeri bulunamadı")
                    raise DatabaseConfigurationError(
                        config_name="db_host",
                        message="PostgreSQL kullanımı için [Database] bölümünde 'db_host' değeri zorunludur"
                    )
                
                port = ConfigurationHandler.get_value_as_int("Database", "db_port")
                if port is None:
                    self._logger.error("Config dosyasında 'db_port' değeri bulunamadı")
                    raise DatabaseConfigurationError(
                        config_name="db_port",
                        message="PostgreSQL kullanımı için [Database] bölümünde 'db_port' değeri zorunludur"
                    )
                
                db_name = ConfigurationHandler.get_value_as_str("Database", "db_name")
                if not db_name:
                    self._logger.error("Config dosyasında 'db_name' değeri bulunamadı")
                    raise DatabaseConfigurationError(
                        config_name="db_name",
                        message="PostgreSQL kullanımı için [Database] bölümünde 'db_name' değeri zorunludur"
                    )
                
                username = ConfigurationHandler.get_value_as_str("Database", "db_user")
                if not username:
                    self._logger.error("Config dosyasında 'db_user' değeri bulunamadı")
                    raise DatabaseConfigurationError(
                        config_name="db_user",
                        message="PostgreSQL kullanımı için [Database] bölümünde 'db_user' değeri zorunludur"
                    )
                
                password = ConfigurationHandler.get_value_as_str("Database", "db_password")
                if password is None:
                    self._logger.error("Config dosyasında 'db_password' değeri bulunamadı")
                    raise DatabaseConfigurationError(
                        config_name="db_password",
                        message="PostgreSQL kullanımı için [Database] bölümünde 'db_password' değeri zorunludur (boş string olabilir)"
                    )
                
                self._logger.debug(f"PostgreSQL host: {host}, port: {port}, database: {db_name}, user: {username}")
                
                db_config = get_database_config(
                    database_name=db_name,
                    db_type=db_type,
                    host=host,
                    port=port,
                    username=username,
                    password=password
                )

            elif db_type == DatabaseType.MYSQL:
                # MySQL için zorunlu alanlar
                host = ConfigurationHandler.get_value_as_str("Database", "db_host")
                if not host:
                    self._logger.error("Config dosyasında 'db_host' değeri bulunamadı")
                    raise DatabaseConfigurationError(
                        config_name="db_host",
                        message="MySQL kullanımı için [Database] bölümünde 'db_host' değeri zorunludur"
                    )
                
                port = ConfigurationHandler.get_value_as_int("Database", "db_port")
                if port is None:
                    self._logger.error("Config dosyasında 'db_port' değeri bulunamadı")
                    raise DatabaseConfigurationError(
                        config_name="db_port",
                        message="MySQL kullanımı için [Database] bölümünde 'db_port' değeri zorunludur"
                    )
                
                db_name = ConfigurationHandler.get_value_as_str("Database", "db_name")
                if not db_name:
                    self._logger.error("Config dosyasında 'db_name' değeri bulunamadı")
                    raise DatabaseConfigurationError(
                        config_name="db_name",
                        message="MySQL kullanımı için [Database] bölümünde 'db_name' değeri zorunludur"
                    )
                
                username = ConfigurationHandler.get_value_as_str("Database", "db_user")
                if not username:
                    self._logger.error("Config dosyasında 'db_user' değeri bulunamadı")
                    raise DatabaseConfigurationError(
                        config_name="db_user",
                        message="MySQL kullanımı için [Database] bölümünde 'db_user' değeri zorunludur"
                    )
                
                password = ConfigurationHandler.get_value_as_str("Database", "db_password")
                if password is None:
                    self._logger.error("Config dosyasında 'db_password' değeri bulunamadı")
                    raise DatabaseConfigurationError(
                        config_name="db_password",
                        message="MySQL kullanımı için [Database] bölümünde 'db_password' değeri zorunludur (boş string olabilir)"
                    )
                
                self._logger.debug(f"MySQL host: {host}, port: {port}, database: {db_name}, user: {username}")
                
                db_config = get_database_config(
                    database_name=db_name,
                    db_type=db_type,
                    host=host,
                    port=port,
                    username=username,
                    password=password
                )

            if not db_config:
                self._logger.error("Database config oluşturulamadı")
                raise DatabaseConfigurationError(
                    config_name="database_config",
                    message="Database config oluşturulamadı"
                )

            # DatabaseManager'ı initialize et
            if self._database_manager is None:
                self._database_manager = DatabaseManager()
            
            # Eğer zaten initialize edilmişse, sadece log yaz
            if self._database_manager.is_initialized:
                self._logger.info("Database Manager zaten başlatılmış")
                return True

            # DatabaseManager'ı başlat
            # auto_create_tables: Setup modunda True, Run modunda False
            should_create = hasattr(self, '_should_create_tables') and self._should_create_tables
            
            self._database_manager.initialize(
                config=db_config,
                auto_start=True,
                auto_create_tables=should_create  # Manager içinde modeller yüklenip tablolar oluşturulur
            )

            self._logger.info(f"Database Manager başarıyla başlatıldı: {db_config}")
            return True

        except (DatabaseConfigurationError, DatabaseValidationError) as e:
            self._logger.error(
                f"Database Manager başlatılırken yapılandırma hatası: {e}",
                exc_info=True
            )
            raise  # Hata durumunda durdur
        except Exception as e:
            self._logger.error(
                f"Database Manager başlatılırken hata oluştu: {e}",
                exc_info=True
            )
            raise  # Hata durumunda durdur

    # ========================================================================
    # RUN MODE
    # ========================================================================

    def run(self):
        """Uygulamayı başlat"""
        self._print_header("QBITRA RUN MODE")

        if not self._is_database_ready():
            self._print_error("DATABASE NOT READY", "Please run setup first: python -m qbitra setup")
            sys.exit(1)

        app = self._create_fastapi_app()
        self._start_server(app)

    def _create_fastapi_app(self):
        """FastAPI uygulaması oluştur"""
        from fastapi import FastAPI

        is_dev = not self.is_production
        app = FastAPI(
            title=ConfigurationHandler.get_value_as_str("Server", "title", fallback="QBitra API"),
            description=ConfigurationHandler.get_value_as_str("Server", "description", fallback="QBitra Application"),
            version=ConfigurationHandler.get_value_as_str("Server", "version", fallback="1.0.0"),
            docs_url="/docs" if is_dev else None,
            redoc_url="/redoc" if is_dev else None,
            openapi_url="/openapi.json" if is_dev else None,
            lifespan=self._app_lifespan,
        )

        self._configure_middleware(app)
        self._configure_exception_handlers(app)
        self._configure_routes(app)
        return app

    @asynccontextmanager
    async def _app_lifespan(self, app):
        """App lifecycle yönetimi"""
        pid = os.getpid()
        state = {}
        try:
            state = self._worker_startup(pid)
            yield
        finally:
            self._worker_shutdown(pid, state)

    def _worker_startup(self, pid: int) -> dict:
        """Worker servisleri başlat"""
        state = {}
        services = [
            ("database", self._start_database),
            # QBitra'da engine, output_handler, input_handler yoksa bunları ekleyebiliriz
            # ("engine", self._start_engine),
            # ("output_handler", self._start_output_handler),
            # ("input_handler", self._start_input_handler),
        ]

        for name, starter in services:
            print(f"[WORKER-{pid}] Starting {name}...")
            if component := starter(state):
                state[name] = component

        self._start_scheduler(pid, state)
        print(f"[WORKER-{pid}] All services started\n")
        return state

    def _worker_shutdown(self, pid: int, state: dict, force: bool = False):
        """Worker servisleri kapat"""
        if not state:
            return

        prefix = "[FORCE] " if force else ""
        print(f"\n[WORKER-{pid}] {prefix}Stopping services...")

        for key in reversed(['database', 'engine', 'output_handler', 'input_handler', 'scheduler']):
            if service := state.get(key):
                try:
                    self._stop_service(service, key)
                except Exception as e:
                    print(f"[WORKER-{pid}] {prefix}Warning stopping {key}: {e}")

        print(f"[WORKER-{pid}] {prefix}Shutdown complete\n")

    def _start_database(self, state: dict):
        """Database başlat"""
        if not self._database_manager or not self._database_manager.is_initialized:
            # Database manager zaten _setup_database_manager'da başlatıldı
            # Burada sadece state'e ekliyoruz
            if not self._database_manager:
                self._database_manager = DatabaseManager()
        state['database'] = self._database_manager
        return self._database_manager

    def _start_scheduler(self, pid: int, state: dict):
        """Scheduler başlat (opsiyonel)"""
        # QBitra'da scheduler varsa buraya eklenebilir
        pass

    def _stop_service(self, service, service_key: str):
        """Servisi durdur"""
        if service_key == 'database':
            if hasattr(service, 'engine') and service.engine:
                if hasattr(service.engine, 'is_alive') and service.engine.is_alive:
                    if hasattr(service.engine, 'get_active_session_count'):
                        active = service.engine.get_active_session_count()
                        if active > 0:
                            service.engine.close_all_sessions()
                    service.engine.stop()
        elif hasattr(service, 'shutdown'):
            service.shutdown()
        elif hasattr(service, 'stop'):
            service.stop()

    def _start_server(self, app):
        """Uvicorn sunucu başlat"""
        import uvicorn

        host = ConfigurationHandler.get_value_as_str("Server", "host", fallback="0.0.0.0")
        port = ConfigurationHandler.get_value_as_int("Server", "port", fallback=8000)
        reload = ConfigurationHandler.get_value_as_bool("Server", "reload", fallback=False) and self.is_development
        workers = 1 if reload else ConfigurationHandler.get_value_as_int("Server", "workers", fallback=1)

        self._print_server_info(host, port, reload, workers)
        self.is_running = True

        if reload:
            uvicorn.run("qbitra.app:app", host=host, port=port, reload=True)
        else:
            uvicorn.run(app, host=host, port=port, workers=workers)

    # ========================================================================
    # MIDDLEWARE & ROUTES
    # ========================================================================

    def _configure_middleware(self, app):
        """Middleware yapılandırması"""
        from fastapi.middleware.cors import CORSMiddleware

        # CORS middleware
        origins = ConfigurationHandler.get_value_as_list("Server", "allowed_origins", fallback=["*"])
        
        if isinstance(origins, list) and origins and origins[0] == "*":
            cors_origins = None
        elif isinstance(origins, list) and origins:
            cors_origins = origins
        else:
            cors_origins = None
        
        if cors_origins is None:
            app.add_middleware(
                CORSMiddleware,
                allow_origin_regex=".*",
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )
        else:
            app.add_middleware(
                CORSMiddleware,
                allow_origins=cors_origins,
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )

    def _configure_exception_handlers(self, app):
        """Exception handler yapılandırması"""
        from qbitra.app.middleware.exception_handling import register_qbitra_handler
        register_qbitra_handler(app)

    def _configure_routes(self, app):
        """Route yapılandırması"""
        # Health endpoints
        @app.get("/", tags=["General"])
        async def root():
            return {
                "app": "QBitra",
                "status": "running",
                "environment": EnvironmentHandler.get_value_as_str("APP_ENV", default="unknown"),
                "docs": "/docs" if not self.is_production else None
            }

        @app.get("/health", tags=["Health"])
        async def health():
            db_type = ConfigurationHandler.get_value_as_str("Database", "db_type", fallback="unknown")
            return {
                "status": "healthy",
                "environment": EnvironmentHandler.get_value_as_str("APP_ENV", fallback="unknown"),
                "database_type": db_type
            }

        # API routers - QBitra'da routes varsa buraya eklenebilir
        # from qbitra.app.routes import router
        # app.include_router(router)

    # ========================================================================
    # HELPERS
    # ========================================================================

    def _is_database_ready(self) -> bool:
        """Veritabanı hazır mı kontrolü"""
        try:
            if not self._database_manager:
                return False
            if not self._database_manager.is_initialized:
                return False
            if not hasattr(self._database_manager, 'engine') or not self._database_manager.engine:
                return False
            return self._database_manager.engine.is_alive
        except Exception:
            return False

    @property
    def is_development(self) -> bool:
        """Development ortamı mı?"""
        app_env = EnvironmentHandler.get_value_as_str("APP_ENV", default="").lower()
        return 'dev' in app_env or 'local' in app_env

    @property
    def is_production(self) -> bool:
        """Production ortamı mı?"""
        app_env = EnvironmentHandler.get_value_as_str("APP_ENV", default="").lower()
        return 'prod' in app_env

    # ========================================================================
    # OUTPUT HELPERS
    # ========================================================================

    def _print_header(self, title: str):
        """Başlık yazdır"""
        print("\n" + "=" * 70)
        print(title.center(70))
        print("=" * 70 + "\n")

    def _print_error(self, title: str, message: str):
        """Hata mesajı"""
        print("\n" + "=" * 70)
        print(f"[ERROR] {title}".center(70))
        print("=" * 70)
        print(f"\n{message}\n")
        print("-" * 70 + "\n")

    def _print_server_info(self, host: str, port: int, reload: bool, workers: int):
        """Sunucu bilgileri"""
        print("-" * 70)
        print("WEB SERVER STARTING".center(70))
        print("-" * 70)
        app_env = EnvironmentHandler.get_value_as_str("APP_ENV", default="unknown")
        db_type = ConfigurationHandler.get_value_as_str("Database", "db_type", fallback="unknown")
        print(f"Environment       : {app_env.upper()}")
        print(f"Database Type     : {db_type.upper()}")
        print(f"Address           : http://{host}:{port}")
        if not self.is_production:
            print(f"Documentation     : http://{host}:{port}/docs")
        print(f"Reload            : {'[ACTIVE]' if reload else '[DISABLED]'}")
        print(f"Workers           : {workers}")
        print("-" * 70 + "\n")

    # ========================================================================
    # MAIN ENTRY POINT
    # ========================================================================

    def initialize(self) -> bool:
        """Tüm handler'ları başlat"""
        if self._initialized:
            self._logger.info("QBitra Bootstrap zaten başlatılmış")
            return True

        try:
            self._logger.info("QBitra Bootstrap başlatılıyor...")
            
            if not self._setup_environment_handler():
                return False
            if not self._setup_configuration_handler():
                return False
            if not self._setup_database_manager():
                return False

            self._initialized = True
            self._logger.info("QBitra Bootstrap başarıyla tamamlandı")
            return True
        except Exception as e:
            self._logger.error(f"QBitra Bootstrap başlatılırken hata: {e}", exc_info=True)
            raise


def main():
    """Main entry point"""
    import sys
    
    try:
        command = sys.argv[1].lower() if len(sys.argv) > 1 else "run"
        
        bootstrap = QBitraBootstrap()
        
        if command == "setup":
            # Setup modu - tabloları oluştur
            bootstrap._should_create_tables = True
            bootstrap.initialize()
            
            # Database dosyası kontrolü
            try:
                db_type = ConfigurationHandler.get_value_as_str("Database", "db_type", fallback="")
                if db_type.lower() == "sqlite":
                    sqlite_path = ConfigurationHandler.get_value_as_str("Database", "sqlite_path", fallback="")
                    if sqlite_path:
                        from pathlib import Path
                        db_file = Path(sqlite_path)
                        if db_file.exists():
                            file_size = db_file.stat().st_size
                            print(f"✅ Database file: {db_file.absolute()} ({file_size} bytes)")
                
                # Tablo sayısını kontrol et
                if bootstrap._database_manager and bootstrap._database_manager.is_initialized:
                    from qbitra.database.models import metadata
                    table_count = len(metadata.tables)
                    print(f"✅ Created {table_count} database table(s)")
            except Exception as e:
                print(f"⚠️  Database check: {e}")
            
            print("\n✅ Setup completed successfully!")
            print("   Database tables have been created.\n")
        elif command == "run":
            # Run modu
            bootstrap.initialize()
            bootstrap.run()
        else:
            print(f"\nUnknown command: {command}")
            print("Available commands: setup, run\n")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n[INFO] Application interrupted by user\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n[FATAL] {type(e).__name__}: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main() 