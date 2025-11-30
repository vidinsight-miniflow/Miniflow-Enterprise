"""
MiniFlow Enterprise - Main Entry Point

Terminal üzerinden sunucuyu yönetmek için iki mod:
- setup: İlk kurulum (dosya yapısı, veritabanı, seed, handler testleri)
- run: Uygulamayı başlat (FastAPI app, middleware, routes, server)
"""
import sys
import os

# Help komutunu import'lardan önce kontrol et
if len(sys.argv) > 1 and sys.argv[1].lower() in ("help", "--help", "-h"):
    print("\n" + "=" * 70)
    print("MINIFLOW ENTERPRISE - Available Commands".center(70))
    print("=" * 70)
    print("\n  setup      Initial setup (create database, seed data, test handlers)")
    print("  run        Start the application (default)")
    print("  help       Show this help message")
    print("\nExamples:")
    print("  python -m src.miniflow setup")
    print("  python -m src.miniflow run")
    print("  python -m src.miniflow        # 'run' command (default)\n")
    sys.exit(0)

from typing import Optional
from contextlib import asynccontextmanager
from pathlib import Path
from sqlalchemy import text, inspect

from seeds.workflow_plan_seeds import WORKSPACE_PLANS_SEED
from seeds.user_role_seeds import USER_ROLES_SEED
from seeds.agreement_seeds import AGREEMENT_SEEDS

from src.miniflow.utils import EnvironmentHandler, ConfigurationHandler, RedisClient
from src.miniflow.core.exceptions import InvalidInputError, ResourceNotFoundError, InternalError
from src.miniflow.database import get_sqlite_config, get_postgresql_config, get_mysql_config
from src.miniflow.database import DatabaseManager
from src.miniflow.utils.helpers.file_helper import create_resources_folder
from src.miniflow.services.info_services.user_roles_service import UserRolesService
from src.miniflow.services.info_services.workspace_plans_service import WorkspacePlansService
from src.miniflow.services.info_services.agreement_service import AgreementService


class MiniFlow:
    """
    MiniFlow Enterprise uygulama yöneticisi.
    
    İki mod destekler:
    - setup: İlk kurulum ve hazırlık
    - run: Uygulamayı başlat
    """
    
    def __init__(self):
        """Temel initialization"""
        # Ortam ve veritabanı tipi (henüz initialize edilmemiş)
        self._app_env: Optional[str] = None
        self._db_type: Optional[str] = None

        # Database Manager
        self._db_manager: Optional[DatabaseManager] = None

        # Çalışma Durumu
        self.is_running = False

        # Seed Services (lazy initialization)
        self._user_role_service: Optional[UserRolesService] = None
        self._workspace_plan_service: Optional[WorkspacePlansService] = None
        self._agreement_service: Optional[AgreementService] = None

        # Başlatma işlemleri
        self._startup_initialization()

    def _startup_initialization(self):
        """Uygulama başlatma işlemlerini yürütür"""
        # 1. Configuration'ları yükle
        self._setup_config()
        
        # 2. Ortam ve veritabanı tipini ayarla
        self._app_env = EnvironmentHandler.get("APP_ENV", "").lower()
        self._db_type = EnvironmentHandler.get("DB_TYPE", "").lower()
        
        if not self._app_env:
            raise InternalError(
                component_name="miniflow",
                message="APP_ENV environment variable is not set."
            )
        
        if not self._db_type:
            raise InternalError(
                component_name="miniflow",
                message="DB_TYPE environment variable is not set."
            )

    @property
    def _env(self):
        """EnvironmentHandler'a erişim için property"""
        return EnvironmentHandler

    @property
    def _config(self):
        """ConfigurationHandler'a erişim için property"""
        return ConfigurationHandler

    def _setup_config(self):
        """Initialize application configuration, environment, and external services."""
        print("\n" + "=" * 70)
        print("MINIFLOW STARTUP INITIALIZATION".center(70))
        print("=" * 70 + "\n")

        try:
            # 1. Load environment variables
            print("[1/4] Loading environment variables...", end=" ", flush=True)
            EnvironmentHandler.load_env()
            print("✓ OK")
            
            # 2. Load configuration files
            print("[2/4] Loading configuration files...", end=" ", flush=True)
            ConfigurationHandler.load_config()
            print("✓ OK")
            
            # 3. Initialize Redis connection
            print("[3/4] Initializing Redis connection...", end=" ", flush=True)
            RedisClient.initialize()
            print("✓ OK")

            # 4. Create resources folder
            print("[4/4] Creating resources folder...", end=" ", flush=True)
            create_resources_folder()
            print("✓ OK")
            
            print("\n" + "=" * 70)
            print("STARTUP INITIALIZATION COMPLETED SUCCESSFULLY".center(70))
            print("=" * 70 + "\n")
            
        except ResourceNotFoundError as e:
            self._print_error_header("RESOURCE NOT FOUND")
            print(f"Error: {e.error_message}")
            resource_info = f"{e.resource_name}"
            if e.resource_id:
                resource_info += f" (ID: {e.resource_id})"
            print(f"Resource: {resource_info}")
            if e.error_details:
                print(f"Details: {e.error_details}")
            print("\n" + "-" * 70)
            print("Troubleshooting:")
            print("  • Verify the resource path and file permissions")
            print("  • Check if the resource exists in the expected location")
            print("  • Ensure proper file/directory access rights")
            print("-" * 70)
            sys.exit(1)
        
        except InternalError as e:
            self._print_error_header("INITIALIZATION ERROR")
            print(f"Component: {e.component_name}")
            print(f"Error: {e.error_message}")
            
            if e.error_details:
                if isinstance(e.error_details, dict):
                    if 'host' in e.error_details and 'port' in e.error_details:
                        print(f"Redis Address: {e.error_details['host']}:{e.error_details['port']}")
                    elif 'original_error' in e.error_details:
                        print(f"Original Error: {e.error_details['original_error']}")
                    else:
                        print(f"Details: {e.error_details}")
                else:
                    print(f"Details: {e.error_details}")
            
            print("\n" + "-" * 70)
            print("Troubleshooting:")
            
            if e.component_name == "environment_handler":
                print("  • Verify environment variables are correctly set")
                print("  • Check .env file exists in the project root")
                print("  • Ensure TEST_KEY is set to 'ThisKeyIsForConfigTest'")
                print("  • Verify environment file path is correct")
            elif e.component_name == "configuration_handler":
                print("  • Verify configuration files exist in 'configurations/' directory")
                print("  • Check configuration file format (INI format)")
                print("  • Ensure [Test] section with value='ThisKeyIsForConfigTest' exists")
                print("  • Verify APP_ENV matches available config files (dev/prod/local/test)")
            elif e.component_name == "redis_client":
                print("  • Verify Redis server is running (redis-server)")
                print("  • Check Redis host and port settings in configuration")
                print("  • Ensure firewall allows Redis port access")
                print("  • Test connection: redis-cli ping")
            elif e.component_name == "database_manager":
                print("  • Verify database configuration settings")
                print("  • Check database server is running and accessible")
                print("  • Ensure database credentials are correct")
                print("  • Verify database connection string format")
            else:
                print("  • Review application logs for detailed error information")
                print("  • Contact system administrator if issue persists")
            
            print("-" * 70)
            sys.exit(1)
        
        except Exception as e:
            self._print_error_header("UNEXPECTED ERROR")
            print(f"Error Type: {type(e).__name__}")
            print(f"Error Message: {str(e)}")
            print("\n" + "-" * 70)
            print("An unexpected error occurred during startup initialization.")
            print("Please review the application logs and contact system administrator.")
            print("-" * 70)
            sys.exit(1)

    @property
    def is_development(self) -> bool:
        """Development ortamında mı?"""
        return 'dev' in self._app_env

    @property
    def is_production(self) -> bool:
        """Production ortamında mı?"""
        return 'prod' in self._app_env
    
    def _get_db_config(self):
        """Veritabanı yapılandırmasını oluştur"""
        if self._db_type == "sqlite":
            sqlite_path = self._config.get("Database", "db_path", "./miniflow.db")
            return get_sqlite_config(database_name=sqlite_path)
        
        elif self._db_type == "postgresql":
            params = {
                'database_name': self._config.get("Database", "db_name", "miniflow"),
                'host': self._config.get("Database", "db_host", "localhost"),
                'port': self._config.get_int("Database", "db_port", 5432),
                'username': self._config.get("Database", "db_user", "postgres"),
                'password': self._config.get("Database", "db_password", ""),
            }
            return get_postgresql_config(**params)
        
        elif self._db_type == "mysql":
            params = {
                'database_name': self._config.get("Database", "db_name", "miniflow"),
                'host': self._config.get("Database", "db_host", "localhost"),
                'port': self._config.get_int("Database", "db_port", 3306),
                'username': self._config.get("Database", "db_user", "root"),
                'password': self._config.get("Database", "db_password", ""),
            }
            return get_mysql_config(**params)
        else:
            raise InvalidInputError(field_name="DB_TYPE")
        
    def _print_error_header(self, error_type: str):
        """Print formatted error header."""
        print("\n" + "=" * 70)
        print(f"❌ {error_type}".center(70))
        print("=" * 70)

    # ============================================================================
    # SETUP MODE
    # ============================================================================

    def setup(self):
        """
        İlk kurulum: Tüm gerekli kontrolleri yapar ve sistemi hazırlar.
        - Dosya yapısı kontrolü
        - Veritabanı oluşturma
        - Seed veriler
        - Handler testleri
        """
        print("\n" + "=" * 70)
        print("MINIFLOW SETUP MODE".center(70))
        print("=" * 70 + "\n")
        
        try:
            # 1. Dosya yapısı kontrolü
            self._check_file_structure()
            
            # 2. Veritabanı oluşturma
            self._setup_database()
            
            # 3. Seed veriler
            self._seed_initial_data()
            
            # 4. Handler testleri
            self._test_handlers()
            
            print("\n" + "=" * 70)
            print("✅ SETUP COMPLETED SUCCESSFULLY".center(70))
            print("=" * 70)
            print("\nArtık uygulamayı başlatabilirsiniz:")
            print("  python -m src.miniflow run\n")
            
        except Exception as e:
            self._print_error_header("SETUP ERROR")
            print(f"Error Type: {type(e).__name__}")
            print(f"Error Message: {str(e)}")
            print("\n" + "-" * 70)
            print("Setup işlemi başarısız oldu. Lütfen yukarıdaki hataları kontrol edin.")
            print("-" * 70)
            raise
        finally:
            # Setup sonrası bağlantıyı kapat
            if self._db_manager and self._db_manager.is_started:
                self._db_manager.engine.stop()
                print("[SETUP] Database connection closed")

    def _check_file_structure(self):
        """
        Gerekli dosya ve klasörlerin varlığını kontrol eder.
        """
        print("[1/4] Checking file structure...", end=" ", flush=True)
        
        # Resources klasörü oluştur
        create_resources_folder()
        
        # Diğer kontroller
        required_paths = [
            Path("configurations"),
            Path("seeds"),
        ]
        
        missing = [p for p in required_paths if not p.exists()]
        if missing:
            raise ResourceNotFoundError(
                resource_name="required_directories",
                message=f"Missing required directories: {', '.join(str(p) for p in missing)}"
            )
        
        # .env dosyası kontrolü (opsiyonel, sadece warning)
        if not Path(".env").exists():
            print("\n⚠ WARNING: .env file not found. Make sure environment variables are set.")
        
            print("✓ OK")

    def _setup_database(self):
        """
        Veritabanını oluşturur ve tabloları hazırlar.
        """
        print("[2/4] Setting up database...", end=" ", flush=True)
        
        db_config = self._get_db_config()
        self._db_manager = DatabaseManager()
        self._db_manager.initialize(db_config, auto_start=True, create_tables=True)
        
        # Bağlantı testi
        if not self._test_database_connection():
                    raise InternalError(
                        component_name="database_manager",
                message="Database connection test failed"
            )
        
        print("✓ OK")
            
    def _test_database_connection(self) -> bool:
        """Test database connection and verify tables exist."""
        if not self._db_manager or not self._db_manager.is_initialized:
            return False
        
        engine = self._db_manager.engine._engine
        try: 
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
                inspector = inspect(engine)
                tables = inspector.get_table_names()
                return len(tables) > 0
        except Exception:
            return False
    
    def _seed_initial_data(self):
        """
        Başlangıç verilerini ekler (roller, planlar, sözleşmeler).
        """
        print("[3/4] Seeding initial data...", end=" ", flush=True)
        
        if not self._db_manager or not self._db_manager.is_initialized:
            raise RuntimeError("Database Manager is not initialized. Call _setup_database() first.")
        
        self._initialize_seed_services()
        
        # Kullanıcı rolleri
        role_stats = self._user_role_service.seed_role(roles_data=USER_ROLES_SEED)
        
        # Çalışma alanı planları
        plan_stats = self._workspace_plan_service.seed_plan(plans_data=WORKSPACE_PLANS_SEED)
        
        # Sözleşmeler
        agreement_stats = self._agreement_service.seed_agreement(agreements_data=AGREEMENT_SEEDS)
        
        print("✓ OK")
        print(f"   - Roles: {role_stats['created']} created, {role_stats['skipped']} skipped")
        print(f"   - Plans: {plan_stats['created']} created, {plan_stats['skipped']} skipped")
        print(f"   - Agreements: {agreement_stats['created']} created, {agreement_stats['updated']} updated, {agreement_stats['skipped']} skipped")

    def _test_handlers(self):
        """
        External handler'ları test eder (Redis, Mail).
        """
        print("[4/4] Testing handlers...", end=" ", flush=True)
        
        # Redis testi
        try:
            RedisClient._client.ping()
            print("✓ Redis OK", end=" ")
        except Exception as e:
            raise InternalError(
                component_name="redis_client",
                message=f"Redis test failed: {str(e)}",
                error_details={"original_error": str(e)}
            )
        
        # Mail testi (opsiyonel - sadece initialize kontrolü)
        try:
            from src.miniflow.utils.handlers.mailtrap_handler import MailTrapClient
            MailTrapClient.initialize()
            print("✓ Mail OK")
        except Exception as e:
            # Mail opsiyonel olabilir, sadece warning ver
            print("⚠ Mail warning (optional)")

    def _initialize_seed_services(self):
        """Initialize seed services"""
        if not self._user_role_service:
            self._user_role_service = UserRolesService()
        if not self._workspace_plan_service:
            self._workspace_plan_service = WorkspacePlansService()
        if not self._agreement_service:
            self._agreement_service = AgreementService()

    # ============================================================================
    # RUN MODE
    # ============================================================================

    def run(self):
        """
        Uygulamayı başlatır (veritabanı hazır olmalı).
        """
        print("\n" + "=" * 70)
        print("MINIFLOW RUN MODE".center(70))
        print("=" * 70 + "\n")
        
        # Veritabanı hazır mı kontrol et
        if not self._is_database_ready():
            print("\n❌ Database is not ready!")
            print("Please run setup first: python -m src.miniflow setup")
            sys.exit(1)
        
        # FastAPI app oluştur
        app = self.create_fastapi_app()
        
        # Sunucuyu başlat
        self.start_server(app)

    def _is_database_ready(self) -> bool:
        """
        Veritabanı hazır mı kontrol et (tablolar var mı?).
        """
        try:
            manager = DatabaseManager()
            if manager.is_initialized and manager.is_started:
                inspector = inspect(manager.engine._engine)
                tables = inspector.get_table_names()
                return len(tables) > 0
            
            # İlk kez kontrol - geçici engine kullan
            from sqlalchemy import create_engine
            from sqlalchemy.pool import NullPool
            db_config = self._get_db_config()
            db_url = db_config.get_connection_string()
            
            # NullPool kullan (connection pool oluşturma)
            engine = create_engine(db_url, echo=False, poolclass=NullPool)
            
            try:
                with engine.connect() as connection:
                    # Bağlantı testi
                    connection.execute(text("SELECT 1"))
                    
                    # Tablo kontrolü
                    inspector = inspect(engine)
                    tables = inspector.get_table_names()
                    result = len(tables) > 0
                    if self.is_development and not result:
                        print(f"[DEBUG] Database check: {len(tables)} tables found")
                    return result
            finally:
                engine.dispose()
                
        except Exception as e:
            if self.is_development:
                print(f"[DEBUG] Database ready check failed: {type(e).__name__}: {str(e)}")
            return False

    def create_fastapi_app(self):
        """
        FastAPI uygulamasını oluştur ve yapılandır.
        """
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware
        
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            """Lifespan yönetimi (startup/shutdown)"""
            worker_pid = os.getpid()
            manager = None
            
            try:
                # Startup
                manager = self._worker_startup(worker_pid)
                print(f"[WORKER-{worker_pid}] Ready")
                yield
            except Exception as e:
                print(f"[WORKER-{worker_pid}] Error: {e}")
                raise
            finally:
                # Shutdown
                if manager:
                    try:
                        self._worker_shutdown(worker_pid, manager)
                        print(f"[WORKER-{worker_pid}] Shutdown complete")
                    except Exception as e:
                        print(f"[WORKER-{worker_pid}] Shutdown error: {e}")

        # FastAPI app oluştur
        app = FastAPI(
            title=self._config.get("Server", "title", "MiniFlow API"),
            description=self._config.get("Server", "description", "MiniFlow Application"),
            version=self._config.get("Server", "version", "1.0.0"),
            docs_url="/docs" if not self.is_production else None,
            redoc_url="/redoc" if not self.is_production else None,
            openapi_url="/openapi.json" if not self.is_production else None,
            lifespan=lifespan,
        )

        # CORS
        self._add_cors_middleware(app)
        
        # Middleware'ler
        self._add_middleware(app)
        
        # Exception handler'lar
        self._add_exception_handlers(app)
        
        # Route'lar
        self._add_routes(app)
        
        return app

    def _add_cors_middleware(self, app):
        """CORS middleware ekle"""
        from fastapi.middleware.cors import CORSMiddleware
        
        allowed_origins = self._config.get_list("Server", "allowed_origins", "*")
        if isinstance(allowed_origins, str):
            allowed_origins = [allowed_origins]

        app.add_middleware(
            CORSMiddleware,
            allow_origins=allowed_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def _add_middleware(self, app):
        """
        Middleware'leri ekle (sıra önemli).
        """
        from src.miniflow.server.middleware.request_id_handler import RequestIdMiddleware
        from src.miniflow.server.middleware.rate_limit_handler import RateLimitMiddleware
        
        # 1. Request ID Middleware (en üstte)
        app.add_middleware(RequestIdMiddleware)
        
        # 2. Rate Limit Middleware
        app.add_middleware(RateLimitMiddleware)

    def _add_exception_handlers(self, app):
        """
        Exception handler'ları ekle (spesifikten genele).
        """
        import warnings
        # HTTP_422_UNPROCESSABLE_ENTITY deprecation warning'ini suppress et
        # FastAPI/Starlette'de henüz HTTP_422_UNPROCESSABLE_CONTENT mevcut değil
        warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*HTTP_422_UNPROCESSABLE_ENTITY.*")
        
        from fastapi.exceptions import RequestValidationError
        from starlette.exceptions import HTTPException as StarletteHTTPException
        from src.miniflow.server.middleware.exception_handler import (
            app_exception_handler,
            validation_exception_handler,
            http_exception_handler,
            generic_exception_handler,
        )
        from src.miniflow.core.exceptions import AppException
        
        # 1. AppException (en spesifik)
        app.add_exception_handler(AppException, app_exception_handler)
        
        # 2. ValidationError (Pydantic)
        app.add_exception_handler(RequestValidationError, validation_exception_handler)
        
        # 3. HTTPException (Starlette)
        app.add_exception_handler(StarletteHTTPException, http_exception_handler)
        
        # 4. Generic Exception (en genel)
        app.add_exception_handler(Exception, generic_exception_handler)

    def _add_routes(self, app):
        """
        Tüm route'ları ekle.
        """
        from src.miniflow.server.routes import auth_routes
        from src.miniflow.server.routes import user_routes
        from src.miniflow.server.routes import agreement_routes
        from src.miniflow.server.routes import workspace_plans_routes
        from src.miniflow.server.routes import workspace_routes
        from src.miniflow.server.routes import workspace_member_routes
        from src.miniflow.server.routes import workspace_invitation_routes
        from src.miniflow.server.routes import api_key_routes
        from src.miniflow.server.routes import variable_routes
        from src.miniflow.server.routes import database_routes
        from src.miniflow.server.routes import file_routes
        from src.miniflow.server.routes import credential_routes
        from src.miniflow.server.routes import global_script_routes
        from src.miniflow.server.routes import custom_script_routes
        from src.miniflow.server.routes import workflow_routes
        from src.miniflow.server.routes import trigger_routes
        from src.miniflow.server.routes import node_routes
        from src.miniflow.server.routes import edge_routes
        
        # Health check routes
        @app.get("/", tags=["General"])
        async def root():
            """Ana sayfa"""
            return {
                "app": "MiniFlow",
                "status": "running",
                "environment": self._app_env,
                "docs": "/docs" if not self.is_production else None
            }
        
        @app.get("/health", tags=["Health"])
        async def health_check():
            """Sağlık kontrolü"""
            return {
                "status": "healthy",
                "environment": self._app_env,
                "database_type": self._db_type
            }
        
        # API routes
        app.include_router(auth_routes.router)
        app.include_router(user_routes.router)
        app.include_router(agreement_routes.router)
        app.include_router(workspace_plans_routes.router)
        app.include_router(workspace_routes.router)
        app.include_router(workspace_member_routes.router)
        app.include_router(workspace_invitation_routes.router)
        app.include_router(api_key_routes.router)
        app.include_router(variable_routes.router)
        app.include_router(database_routes.router)
        app.include_router(file_routes.router)
        app.include_router(credential_routes.router)
        app.include_router(global_script_routes.router)
        app.include_router(custom_script_routes.router)
        app.include_router(workflow_routes.router)
        app.include_router(trigger_routes.router)
        app.include_router(node_routes.router)
        app.include_router(edge_routes.router)

    def _worker_startup(self, worker_pid: int) -> DatabaseManager:
        """Worker başlatma"""
        manager = DatabaseManager()
        if not manager.is_initialized:
            db_config = self._get_db_config()
            manager.initialize(db_config, auto_start=True, create_tables=False)
            print(f"[WORKER-{worker_pid}] Database connection established")
        
        # Start scheduler service (only in main worker or all workers depending on configuration)
        try:
            from src.miniflow.services.execution_services import SchedulerService
            scheduler_service = SchedulerService()
            if scheduler_service.start():
                print(f"[WORKER-{worker_pid}] SchedulerService started")
                # Store scheduler service in manager for shutdown
                manager._scheduler_service = scheduler_service
            else:
                print(f"[WORKER-{worker_pid}] Warning: SchedulerService failed to start")
        except Exception as e:
            print(f"[WORKER-{worker_pid}] Warning: Failed to start SchedulerService: {str(e)}")
            # Don't fail startup if scheduler fails - it's optional for API-only mode
        
        return manager

    def _worker_shutdown(self, worker_pid: int, manager: DatabaseManager):
        """Worker kapatma"""
        # Stop scheduler service if it exists
        if hasattr(manager, '_scheduler_service') and manager._scheduler_service:
            try:
                print(f"[WORKER-{worker_pid}] Stopping SchedulerService...")
                manager._scheduler_service.stop()
                print(f"[WORKER-{worker_pid}] SchedulerService stopped")
            except Exception as e:
                print(f"[WORKER-{worker_pid}] Error stopping SchedulerService: {str(e)}")
        
        if manager.is_started:
            manager.engine.stop()

    def start_server(self, app):
        """
        Uvicorn sunucusunu başlat.
        """
        import uvicorn
        
        host = self._config.get("Server", "host", "0.0.0.0")
        port = self._config.get_int("Server", "port", 8000)
        reload_config = self._config.get_bool("Server", "reload", False)
        workers = self._config.get_int("Server", "workers", 1)
        
        # Uvicorn reload için app objesi yerine import string kullanılmalı
        # Reload=True olduğunda import string kullan, reload=False olduğunda app objesi kullan
        reload = reload_config and self.is_development
        
        print("\n" + "-" * 70)
        print("WEB SERVER STARTING".center(70))
        print("-" * 70)
        print(f"Environment      : {self._app_env.upper()}")
        print(f"Database Type     : {self._db_type.upper()}")
        print(f"Address           : http://{host}:{port}")
        if not self.is_production:
            print(f"Documentation     : http://{host}:{port}/docs")
        print(f"Reload            : {'✅ Active' if reload else '❌ Disabled'}")
        print(f"Workers           : {workers if not reload else 1}")
        print("-" * 70 + "\n")
        
        self.is_running = True
        
        if reload:
            # Reload için import string kullan
            uvicorn.run(
                "src.miniflow.app:app",
                host=host,
                port=port,
                reload=True,
                workers=1,  # Reload ile workers kullanılamaz
                access_log=self.is_development,
            )
        else:
            # Reload olmadan app objesi kullan
            uvicorn.run(
                app,
                host=host,
                port=port,
                reload=False,
                workers=workers,
                access_log=self.is_development,
            )


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def print_help():
    """Yardım mesajını göster"""
    print("\n" + "=" * 70)
    print("MINIFLOW ENTERPRISE - Available Commands".center(70))
    print("=" * 70)
    print("\n  setup      Initial setup (create database, seed data, test handlers)")
    print("  run        Start the application (default)")
    print("  help       Show this help message")
    print("\nExamples:")
    print("  python -m src.miniflow setup")
    print("  python -m src.miniflow run")
    print("  python -m src.miniflow        # 'run' command (default)\n")


if __name__ == "__main__":
    """Main entry point for MiniFlow application."""
    miniflow = None
    try:
        # Komut satırı argümanı
        command = sys.argv[1].lower() if len(sys.argv) > 1 else "run"
        
        # Diğer komutlar için MiniFlow'u initialize et
        miniflow = MiniFlow()
        
        if command == "setup":
            miniflow.setup()
        elif command == "run":
            miniflow.run()
        elif command in ("help", "--help", "-h"):
            print_help()
        else:
            print(f"Unknown command: {command}")
            print_help()
            sys.exit(1)
        
    except KeyboardInterrupt:
        print("\n\n[INFO] Application interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n[FATAL] Application failed: {type(e).__name__}: {str(e)}")
        import traceback
        if miniflow and miniflow.is_development:
            traceback.print_exc()
        sys.exit(1)
