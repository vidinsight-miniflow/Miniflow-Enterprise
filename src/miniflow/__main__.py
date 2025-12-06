"""
MiniFlow Enterprise - Main Entry Point

Terminal üzerinden sunucuyu yönetmek için iki mod:
- setup: İlk kurulum (dosya yapısı, veritabanı, seed, handler testleri)
- run: Uygulamayı başlat (FastAPI app, middleware, routes, server)
"""
# ============================================================================
# STANDARD LIBRARY IMPORTS
# ============================================================================
import os
import sys
import time
import traceback
import warnings
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

# ============================================================================
# PROJECT ROOT PATH SETUP
# ============================================================================
# Add project root to Python path for seeds import
_project_root = Path(__file__).resolve().parents[2]  # src/miniflow/__main__.py -> project root
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

# ============================================================================
# THIRD-PARTY IMPORTS
# ============================================================================
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.pool import NullPool

# ============================================================================
# SEEDS
# ============================================================================
from seeds.agreement_seeds import AGREEMENT_SEEDS
from seeds.user_role_seeds import USER_ROLES_SEED
from seeds.workflow_plan_seeds import WORKSPACE_PLANS_SEED
from seeds.global_script_seeds import GLOBAL_SCRIPT_SEEDS

# ============================================================================
# CORE
# ============================================================================
from miniflow.core.exceptions import (
    InternalError,
    InvalidInputError,
    ResourceNotFoundError,
)

# ============================================================================
# DATABASE
# ============================================================================
from miniflow.database import (
    DatabaseManager,
    get_mysql_config,
    get_postgresql_config,
    get_sqlite_config,
)

# ============================================================================
# SERVICES
# ============================================================================
from miniflow.services import (
    AgreementService,
    UserRoleService,
    WorkspacePlanService,
    GlobalScriptService,
)

# ============================================================================
# UTILS
# ============================================================================
from miniflow.utils import ConfigurationHandler, EnvironmentHandler, RedisClient
from miniflow.utils.helpers.file_helper import create_resources_folder

# ============================================================================
# EARLY EXIT FOR HELP
# ============================================================================
if len(sys.argv) > 1 and sys.argv[1].lower() in ("help", "--help", "-h"):
    print("\n" + "=" * 70)
    print("MINIFLOW ENTERPRISE - Available Commands".center(70))
    print("=" * 70)
    print("\n  quickstart  Interactive .env setup wizard")
    print("  setup      Initial setup (database, seed data, tests)")
    print("  run        Start application (default)")
    print("  help       Show this help message")
    print("\nExamples:")
    print("  miniflow quickstart  # Create .env file interactively")
    print("  miniflow setup       # Initialize database")
    print("  miniflow run         # Start application")
    print("  miniflow             # defaults to 'run'")
    print("\nNote: If 'miniflow' command not found, use:")
    print("  python -m src.miniflow <command>\n")
    sys.exit(0)


class MiniFlow:
    """MiniFlow Enterprise uygulama yöneticisi."""

    def __init__(self):
        """Temel initialization"""
        self._app_env: Optional[str] = None
        self._db_type: Optional[str] = None
        self._db_manager: Optional[DatabaseManager] = None
        self.is_running = False

        # Lazy initialization için seed services
        self._user_role_service: Optional[UserRoleService] = None
        self._workspace_plan_service: Optional[WorkspacePlanService] = None
        self._agreement_service: Optional[AgreementService] = None
        self._global_script_service: Optional[GlobalScriptService] = None

        self._initialize()

    # ========================================================================
    # INITIALIZATION
    # ========================================================================

    def _initialize(self):
        """Uygulama başlangıç ayarları"""
        self._print_header("MINIFLOW STARTUP INITIALIZATION")

        try:
            self._load_configurations()
            self._set_environment_vars()
            self._print_success("STARTUP INITIALIZATION COMPLETED")

        except (ResourceNotFoundError, InternalError) as e:
            self._handle_initialization_error(e)
        except Exception as e:
            self._handle_unexpected_error(e, "startup initialization")

    def _load_configurations(self):
        """Tüm konfigürasyonları yükle"""
        steps = [
            ("Loading environment variables", EnvironmentHandler.load_env),
            ("Loading configuration files", ConfigurationHandler.load_config),
            ("Initializing Redis connection", RedisClient.initialize),
            ("Creating resources folder", create_resources_folder),
        ]

        for i, (description, action) in enumerate(steps, 1):
            print(f"[{i}/{len(steps)}] {description}...", end=" ", flush=True)
            action()
            print("[OK]")

    def _set_environment_vars(self):
        """Ortam değişkenlerini ayarla ve doğrula"""
        self._app_env = EnvironmentHandler.get("APP_ENV", "").lower()
        self._db_type = EnvironmentHandler.get("DB_TYPE", "").lower()

        if not self._app_env:
            raise InternalError("miniflow", "APP_ENV environment variable is not set")
        if not self._db_type:
            raise InternalError("miniflow", "DB_TYPE environment variable is not set")

    # ========================================================================
    # SETUP MODE
    # ========================================================================

    def setup(self):
        """İlk kurulum ve sistem hazırlama"""
        self._print_header("MINIFLOW SETUP MODE")

        try:
            self._check_file_structure()
            self._setup_database()
            self._seed_initial_data()
            self._test_handlers()

            self._print_success("SETUP COMPLETED")
            print("Uygulamayı başlatmak için: python -m src.miniflow run\n")

        except Exception as e:
            self._print_error("SETUP ERROR", f"{type(e).__name__}: {str(e)}")
            print("\nSetup işlemi başarısız oldu. Lütfen yukarıdaki hataları kontrol edin.\n")
            raise
        finally:
            self._cleanup_database()

    def _check_file_structure(self):
        """Dosya yapısı kontrolü"""
        print("[1/4] Checking file structure...", end=" ", flush=True)

        create_resources_folder()

        required_paths = [Path("configurations"), Path("seeds")]
        missing = [p for p in required_paths if not p.exists()]

        if missing:
            raise ResourceNotFoundError(
                "required_directories",
                message=f"Missing: {', '.join(str(p) for p in missing)}"
            )

        if not Path(".env").exists():
            print("\n      [WARNING] .env file not found", end="")

        print(" [OK]")

    def _setup_database(self):
        """Veritabanı kurulumu"""
        print("[2/4] Setting up database...", end=" ", flush=True)

        db_config = self._get_db_config()
        self._db_manager = DatabaseManager()
        self._db_manager.initialize(db_config, auto_start=True, create_tables=True)

        if not self._test_db_connection():
            raise InternalError("database_manager", "Database connection test failed")

        print("[OK]")

    def _seed_initial_data(self):
        """Başlangıç verilerini ekle"""
        print("[3/4] Seeding initial data...", end=" ", flush=True)

        if not self._db_manager or not self._db_manager.is_initialized:
            raise RuntimeError("Database Manager not initialized")

        self._initialize_seed_services()

        role_stats = UserRoleService.seed_default_user_roles(roles_data=USER_ROLES_SEED)
        plan_stats = WorkspacePlanService.seed_default_workspace_plans(plans_data=WORKSPACE_PLANS_SEED)
        agreement_stats = AgreementService.seed_default_agreements(agreements_data=AGREEMENT_SEEDS)
        script_stats = GlobalScriptService.seed_scripts(scripts_data=GLOBAL_SCRIPT_SEEDS)

        print("[OK]")
        print(f"      • Roles: {role_stats['created']} created, {role_stats['skipped']} skipped")
        print(f"      • Plans: {plan_stats['created']} created, {plan_stats['skipped']} skipped")
        print(f"      • Agreements: {agreement_stats['created']} created, {agreement_stats['skipped']} skipped")
        print(f"      • Global Scripts: {script_stats['created']} created, {script_stats['skipped']} skipped")

    def _test_handlers(self):
        """Handler testleri"""
        print("[4/4] Testing handlers...", end=" ", flush=True)

        # Redis test
        try:
            RedisClient._client.ping()
            print("[OK] Redis", end=" ")
        except Exception as e:
            raise InternalError("redis_client", f"Redis test failed: {str(e)}")

        # Mail test (opsiyonel)
        try:
            from miniflow.utils.handlers.mailtrap_handler import MailTrapClient
            MailTrapClient.initialize()
            print("• Mail [OK]")
        except:
            print("• Mail [OPTIONAL]")

    # ========================================================================
    # RUN MODE
    # ========================================================================

    def run(self):
        """Uygulamayı başlat"""
        self._print_header("MINIFLOW RUN MODE")

        if not self._is_database_ready():
            self._print_error("DATABASE NOT READY",
                            "Please run setup first: python -m src.miniflow setup")
            sys.exit(1)

        app = self._create_fastapi_app()
        self._start_server(app)

    def _create_fastapi_app(self):
        """FastAPI uygulaması oluştur"""
        from fastapi import FastAPI

        app = FastAPI(
            title=self._config.get("Server", "title", "MiniFlow API"),
            description=self._config.get("Server", "description", "MiniFlow Application"),
            version=self._config.get("Server", "version", "1.0.0"),
            docs_url="/docs" if not self.is_production else None,
            redoc_url="/redoc" if not self.is_production else None,
            openapi_url="/openapi.json" if not self.is_production else None,
            lifespan=self._app_lifespan,
        )

        self._configure_middleware(app)
        self._configure_exception_handlers(app)
        self._configure_routes(app)

        return app

    @asynccontextmanager
    async def _app_lifespan(self, app):
        """App lifecycle yönetimi"""
        worker_pid = os.getpid()
        state = None

        try:
            state = self._worker_startup(worker_pid)
            yield
        except Exception as e:
            print(f"[WORKER-{worker_pid}] [ERROR] Startup failed: {e}")
            if state:
                self._worker_shutdown(worker_pid, state, force=True)
            raise
        finally:
            if state:
                self._worker_shutdown(worker_pid, state)

    def _worker_startup(self, pid: int) -> dict:
        """Worker servisleri başlat"""
        state = {}
        services = [
            ("Database", self._start_database),
            ("Engine", self._start_engine),
            ("Output Handler", self._start_output_handler),
            ("Input Handler", self._start_input_handler),
        ]

        try:
            for i, (name, starter) in enumerate(services, 1):
                print(f"[WORKER-{pid}] [{i}/{len(services)}] Starting {name}...")
                component = starter(state)
                if component:
                    state[name.lower().replace(" ", "_")] = component
                print(f"[WORKER-{pid}] [{i}/{len(services)}] [OK] {name} started")

            # Scheduler (opsiyonel)
            self._start_scheduler(pid, state)

            print(f"[WORKER-{pid}] [SUCCESS] All services started\n")
            return state

        except Exception as e:
            print(f"[WORKER-{pid}] [ERROR] Startup failed: {e}")
            self._worker_shutdown(pid, state, force=True)
            raise

    def _worker_shutdown(self, pid: int, state: dict, force: bool = False):
        """Worker servisleri kapat"""
        if not state:
            return

        prefix = "[FORCE] " if force else ""
        print(f"\n[WORKER-{pid}] {prefix}Stopping services...")

        # Ters sırada kapat
        shutdown_order = ['input_handler', 'output_handler', 'engine', 'database', 'scheduler']

        for i, service_key in enumerate(shutdown_order, 1):
            if service := state.get(service_key):
                service_name = service_key.replace("_", " ").title()
                print(f"[WORKER-{pid}] {prefix}[{i}/{len(shutdown_order)}] Stopping {service_name}...")

                try:
                    self._stop_service(service, service_key)
                    print(f"[WORKER-{pid}] {prefix}[{i}/{len(shutdown_order)}] [OK] {service_name} stopped")
                except Exception as e:
                    print(f"[WORKER-{pid}] {prefix}[{i}/{len(shutdown_order)}] [WARNING] {service_name}: {e}")

        print(f"[WORKER-{pid}] {prefix}[SUCCESS] Shutdown complete\n")

    def _start_server(self, app):
        """Uvicorn sunucu başlat"""
        import uvicorn

        host = self._config.get("Server", "host", "0.0.0.0")
        port = self._config.get_int("Server", "port", 8000)
        reload = self._config.get_bool("Server", "reload", False) and self.is_development
        workers = 1 if reload else self._config.get_int("Server", "workers", 1)

        self._print_server_info(host, port, reload, workers)
        self.is_running = True

        if reload:
            uvicorn.run("src.miniflow.app:app", host=host, port=port, reload=True)
        else:
            uvicorn.run(app, host=host, port=port, workers=workers)

    # ========================================================================
    # SERVICE STARTERS/STOPPERS
    # ========================================================================

    def _start_database(self, state: dict):
        """Database başlat"""
        db_manager = DatabaseManager()
        if not db_manager.is_initialized:
            db_manager.initialize(self._get_db_config(), auto_start=True, create_tables=False)
        state['db_manager'] = db_manager
        return db_manager

    def _start_engine(self, state: dict):
        """Engine başlat"""
        from miniflow.engine.manager.engine_manager import EngineManager
        engine = EngineManager()
        if not engine.started:
            engine.start()
        state['engine_manager'] = engine
        return engine

    def _start_output_handler(self, state: dict):
        """Output Handler başlat"""
        from miniflow.handlers.execution_output_handler import ExecutionOutputHandler
        ExecutionOutputHandler.start(state['engine_manager'])
        return ExecutionOutputHandler

    def _start_input_handler(self, state: dict):
        """Input Handler başlat"""
        from miniflow.handlers.execution_input_handler import ExecutionInputHandler
        ExecutionInputHandler.start(state['engine_manager'])
        return ExecutionInputHandler

    def _start_scheduler(self, pid: int, state: dict):
        """
        Scheduler başlat (opsiyonel)
        
        Note: Scheduler functionality is handled by SchedulerForInputHandler and
        SchedulerForOutputHandler which are used internally by the handlers.
        This method is kept for compatibility but does nothing.
        """
        # Scheduler is handled internally by ExecutionInputHandler and ExecutionOutputHandler
        # No separate scheduler service to start
        pass

    def _stop_service(self, service, service_key: str):
        """Servisi durdur"""
        if service_key == 'database':
            time.sleep(0.5)  # Transaction'ların bitmesini bekle
            if service.is_started:
                if active := service.engine.get_active_session_count():
                    service.engine.close_all_sessions()
                service.engine.stop()
        elif hasattr(service, 'shutdown'):
            service.shutdown()
        elif hasattr(service, 'stop'):
            service.stop()

    # ========================================================================
    # MIDDLEWARE & ROUTES
    # ========================================================================

    def _configure_middleware(self, app):
        """Middleware yapılandırması"""
        from fastapi.middleware.cors import CORSMiddleware
        from miniflow.server.middleware import RequestContextMiddleware, IPRateLimitMiddleware

        # CORS
        origins = self._config.get_list("Server", "allowed_origins", "*")
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins if isinstance(origins, list) else [origins],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Request Context & Rate Limit
        # Note: Order matters - RequestContextMiddleware should be added first
        # so it runs last (middleware are executed in reverse order)
        app.add_middleware(IPRateLimitMiddleware)
        app.add_middleware(RequestContextMiddleware)

    def _configure_exception_handlers(self, app):
        """Exception handler yapılandırması"""
        warnings.filterwarnings("ignore", category=DeprecationWarning,
                              message=".*HTTP_422_UNPROCESSABLE_ENTITY.*")

        from miniflow.server.middleware.exception_handler import register_exception_handlers
        
        # Register all exception handlers at once
        register_exception_handlers(app)

    def _configure_routes(self, app):
        """Route yapılandırması"""
        # Health endpoints
        @app.get("/", tags=["General"])
        async def root():
            return {
                "app": "MiniFlow",
                "status": "running",
                "environment": self._app_env,
                "docs": "/docs" if not self.is_production else None
            }

        @app.get("/health", tags=["Health"])
        async def health():
            return {
                "status": "healthy",
                "environment": self._app_env,
                "database_type": self._db_type
            }

        # API routers
        from miniflow.server.routes.frontend import router as frontend_router

        app.include_router(frontend_router)

    # ========================================================================
    # HELPERS
    # ========================================================================

    def _get_db_config(self):
        """Veritabanı konfigürasyonu"""
        configs = {
            "sqlite": lambda: get_sqlite_config(
                self._config.get("Database", "db_path", "./miniflow.db")
            ),
            "postgresql": lambda: get_postgresql_config(
                database_name=self._config.get("Database", "db_name", "miniflow"),
                host=self._config.get("Database", "db_host", "localhost"),
                port=self._config.get_int("Database", "db_port", 5432),
                username=self._config.get("Database", "db_user", "postgres"),
                password=self._config.get("Database", "db_password", ""),
            ),
            "mysql": lambda: get_mysql_config(
                database_name=self._config.get("Database", "db_name", "miniflow"),
                host=self._config.get("Database", "db_host", "localhost"),
                port=self._config.get_int("Database", "db_port", 3306),
                username=self._config.get("Database", "db_user", "root"),
                password=self._config.get("Database", "db_password", ""),
            ),
        }

        if self._db_type not in configs:
            raise InvalidInputError(field_name="DB_TYPE")

        return configs[self._db_type]()

    def _test_db_connection(self) -> bool:
        """Veritabanı bağlantı testi"""
        if not self._db_manager or not self._db_manager.is_initialized:
            return False

        try:
            engine = self._db_manager.engine._engine
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                return len(inspect(engine).get_table_names()) > 0
        except:
            return False

    def _is_database_ready(self) -> bool:
        """Veritabanı hazır mı kontrolü"""
        try:
            db_url = self._get_db_config().get_connection_string()
            engine = create_engine(db_url, echo=False, poolclass=NullPool)

            try:
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                    return len(inspect(engine).get_table_names()) > 0
            finally:
                engine.dispose()
        except:
            return False

    def _initialize_seed_services(self):
        """Seed service'leri başlat"""
        self._user_role_service = self._user_role_service or UserRoleService()
        self._workspace_plan_service = self._workspace_plan_service or WorkspacePlanService()
        self._agreement_service = self._agreement_service or AgreementService()
        self._global_script_service = self._global_script_service or GlobalScriptService()

    def _cleanup_database(self):
        """Veritabanı temizleme"""
        if self._db_manager and self._db_manager.is_started:
            self._db_manager.engine.stop()

    # ========================================================================
    # PROPERTIES
    # ========================================================================

    @property
    def _config(self):
        return ConfigurationHandler

    @property
    def is_development(self) -> bool:
        return 'dev' in self._app_env

    @property
    def is_production(self) -> bool:
        return 'prod' in self._app_env

    # ========================================================================
    # OUTPUT HELPERS
    # ========================================================================

    def _print_header(self, title: str):
        """Başlık yazdır"""
        print("\n" + "=" * 70)
        print(title.center(70))
        print("=" * 70 + "\n")

    def _print_success(self, title: str):
        """Başarı mesajı"""
        print("\n" + "=" * 70)
        print(f"[SUCCESS] {title}".center(70))
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
        print(f"Environment       : {self._app_env.upper()}")
        print(f"Database Type     : {self._db_type.upper()}")
        print(f"Address           : http://{host}:{port}")
        if not self.is_production:
            print(f"Documentation     : http://{host}:{port}/docs")
        print(f"Reload            : {'[ACTIVE]' if reload else '[DISABLED]'}")
        print(f"Workers           : {workers}")
        print("-" * 70 + "\n")

    def _handle_initialization_error(self, e):
        """Initialization hata yönetimi"""
        self._print_error(
            "INITIALIZATION ERROR" if isinstance(e, InternalError) else "RESOURCE NOT FOUND",
            str(e.error_message if hasattr(e, 'error_message') else e)
        )

        troubleshooting = {
            "environment_handler": [
                "Verify .env file exists in project root",
                "Check TEST_KEY='ThisKeyIsForConfigTest'",
            ],
            "configuration_handler": [
                "Verify config files in 'configurations/' directory",
                "Check INI format with [Test] section",
            ],
            "redis_client": [
                "Verify Redis server is running",
                "Test connection: redis-cli ping",
            ],
        }

        component = getattr(e, 'component_name', None)
        if component and component in troubleshooting:
            print("Troubleshooting:")
            for tip in troubleshooting[component]:
                print(f"  • {tip}")
            print("-" * 70 + "\n")

        sys.exit(1)

    def _handle_unexpected_error(self, e, context: str = ""):
        """Beklenmeyen hata yönetimi"""
        self._print_error(
            "UNEXPECTED ERROR",
            f"{type(e).__name__}: {str(e)}\n\nContext: {context}" if context else str(e)
        )
        sys.exit(1)


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main entry point for MiniFlow CLI - used by pyproject.toml scripts."""
    miniflow = None

    try:
        command = sys.argv[1].lower() if len(sys.argv) > 1 else "run"
        
        # Quickstart komutu - .env oluşturma wizard
        if command == "quickstart":
            _quickstart()
            return
        
        miniflow = MiniFlow()

        if command == "setup":
            miniflow.setup()
        elif command == "run":
            miniflow.run()
        else:
            print(f"\nUnknown command: {command}")
            print("Use 'miniflow help' for available commands\n")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n[INFO] Application interrupted by user\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n[FATAL] {type(e).__name__}: {str(e)}")
        if miniflow and miniflow.is_development:
            traceback.print_exc()
        sys.exit(1)


def _quickstart():
    """İnteraktif .env oluşturma wizard'ı."""
    import secrets
    import os
    
    print("\n" + "=" * 60)
    print("MINIFLOW QUICKSTART".center(60))
    print("=" * 60 + "\n")
    
    env_path = Path(".env")
    
    # .env var mı kontrol et
    if env_path.exists():
        # Mevcut .env dosyasını kontrol et
        from dotenv import load_dotenv
        load_dotenv(env_path)
        
        # Gerekli değişkenler var mı kontrol et
        required_vars = ["APP_ENV", "DB_TYPE", "TEST_KEY", "JWT_SECRET_KEY", "ENCRYPTION_KEY"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            print(f"⚠️  .env dosyası mevcut ancak bazı değişkenler eksik: {', '.join(missing_vars)}")
            response = input("Üzerine yazılsın mı? [y/N]: ")
            if response.lower() != 'y':
                print("\n❌ Eksik değişkenler nedeniyle devam edilemiyor.")
                print("   Lütfen .env dosyasını düzenleyin veya 'y' ile yeni oluşturun.\n")
                return
        else:
            # Tüm gerekli değişkenler var, mevcut .env kullanılacak
            app_env = os.getenv("APP_ENV", "local")
            print(f"✅ Mevcut .env dosyası bulundu (APP_ENV={app_env})")
            print("   Mevcut yapılandırma kullanılacak.\n")
            print("📋 Sonraki adımlar:")
            print("   miniflow setup   # Veritabanını başlat (henüz yapılmadıysa)")
            print("   miniflow run     # Uygulamayı başlat")
            print()
            return
    
    # Secret key'leri oluştur
    jwt_key = secrets.token_hex(32)
    enc_key = secrets.token_hex(32)
    
    # Ortam seçimi
    print("Ortam seçin:")
    print("  1) local  - Yerel geliştirme (varsayılan)")
    print("  2) dev    - Development sunucusu")
    print("  3) test   - Test ortamı")
    print("  4) prod   - Production")
    
    choice = input("\nSeçim [1]: ").strip() or "1"
    env_map = {"1": "local", "2": "dev", "3": "test", "4": "prod"}
    app_env = env_map.get(choice, "local")
    
    # .env oluştur
    env_content = f"""# MiniFlow Enterprise Configuration
# Oluşturulma: quickstart wizard

APP_ENV={app_env}
DB_TYPE=sqlite
TEST_KEY=ThisKeyIsForConfigTest

JWT_SECRET_KEY={jwt_key}
JWT_ALGORITHM=HS256
ENCRYPTION_KEY={enc_key}
"""
    
    env_path.write_text(env_content)
    
    print(f"\n✅ .env dosyası oluşturuldu (APP_ENV={app_env})")
    print("\n📋 Sonraki adımlar:")
    print("   miniflow setup   # Veritabanını başlat")
    print("   miniflow run     # Uygulamayı başlat")
    print()


if __name__ == "__main__":
    main()
