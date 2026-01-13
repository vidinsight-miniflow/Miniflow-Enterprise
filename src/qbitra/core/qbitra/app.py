import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Callable, Optional, List, Dict

from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware

from qbitra.utils.handlers.configuration_handler import ConfigurationHandler
from qbitra.core.qbitra_logger import get_logger


@dataclass
class AppConfig:
    title: str = "QBitra API"
    description: str = "QBitra Application"
    version: str = "1.0.0"
    allowed_origins: List[str] = field(default_factory=lambda: ["*"])
    debug: bool = False
    app_env: str = "dev"

    def __post_init__(self):
        if self.is_production:
            self.debug = False

    @classmethod
    def from_config(cls):
        return cls(
            title=ConfigurationHandler.get_value_as_str("Server", "title", fallback="QBitra API"),
            description=ConfigurationHandler.get_value_as_str("Server", "description", fallback="QBitra Application"),
            version=ConfigurationHandler.get_value_as_str("Server", "version", fallback="1.0.0"),
            allowed_origins=ConfigurationHandler.get_value_as_list("Server", "allowed_origins", fallback=["*"]),
            debug=ConfigurationHandler.get_value_as_bool("Server", "debug", fallback=False),
            app_env=ConfigurationHandler.get_current_env()
        )

    @property
    def is_production(self) -> bool:
        return self.app_env == "prod"
    
    @property
    def is_development(self) -> bool:
        return self.app_env == "dev"


class AppFactory:
    def __init__(self, config: AppConfig):
        self.config = config
        self._app: Optional[FastAPI] = None
        self._health_checks: Dict[str, Callable] = {}
        self.logger = get_logger("main")

    @property
    def app(self) -> Optional[FastAPI]:
        return self._app

    def create(self, lifespan: Optional[Callable] = None) -> FastAPI:
        if self._app is not None:
            self.logger.warning("App already created, returning existing instance")
            return self._app
        
        self.logger.info(
            f"Creating FastAPI application: {self.config.title} v{self.config.version}",
            extra={"env": self.config.app_env, "debug": self.config.debug}
        )
        
        # Eğer custom lifespan verilmemişse, logger initialization lifespan kullan
        if lifespan is None:
            lifespan = self._create_lifespan()
        
        self._app = FastAPI(
            title=self.config.title,
            description=self.config.description,
            version=self.config.version,
            docs_url="/docs" if not self.config.is_production else None,
            redoc_url="/redoc" if not self.config.is_production else None,
            openapi_url="/openapi.json" if not self.config.is_production else None,
            lifespan=lifespan
        )

        self._setup_cors()
        self._setup_exception_handlers()
        self._setup_default_routes()
        
        self.logger.info("FastAPI application created successfully")
        
        return self._app
    
    def _create_lifespan(self):
        """
        FastAPI lifespan context manager.
        Worker başladığında logger'ları initialize eder.
        """
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            # Startup: Logger'ları worker sürecinde initialize et
            startup_logger = get_logger("startup")
            startup_logger.info("FastAPI worker started - initializing loggers")
            
            # Tüm kritik logger'ları touch et (lazy initialization garantisi)
            api_logger = get_logger("api")
            auth_service_logger = get_logger("Auth Service")
            auth_routes_logger = get_logger("Auth Routes")
            
            api_logger.info("API logger initialized in worker process")
            auth_service_logger.debug("Auth Service logger initialized in worker process")
            auth_routes_logger.debug("Auth Routes logger initialized in worker process")
            
            startup_logger.info("All loggers initialized successfully in worker")
            
            yield  # App çalışır
            
            # Shutdown: Temizlik işlemleri
            startup_logger.info("FastAPI worker shutting down")
        
        return lifespan

    def _setup_cors(self):
        origins = self.config.allowed_origins
        allow_all = not origins or origins == ["*"] or "*" in origins
        
        if allow_all:
            self.logger.info("CORS configured to allow all origins")
            self._app.add_middleware(
                CORSMiddleware,
                allow_origin_regex=".*",
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )
        else:
            self.logger.info(f"CORS configured with specific origins: {origins}")
            self._app.add_middleware(
                CORSMiddleware,
                allow_origins=origins,
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )

    def _setup_exception_handlers(self) -> None:
        pass

    def _setup_default_routes(self) -> None:
        # Health endpoints
        @self._app.get("/", tags=["General"])
        async def root() -> dict:
            """Kök endpoint"""
            response = {
                "app": self.config.title,
                "version": self.config.version,
                "status": "running",
            }
            
            if self.config.is_development:
                response["docs"] = "/docs"
            
            return response

        @self._app.get("/health", tags=["Health"])
        async def health() -> dict:
            checks = {"status": "healthy"}
            all_healthy = True
            
            for name, check_func in self._health_checks.items():
                try:
                    result = await check_func() if asyncio.iscoroutinefunction(check_func) else check_func()
                    checks[name] = "ok" if result else "unhealthy"
                    if not result:
                        all_healthy = False
                except Exception as e:
                    self.logger.error(f"Health check '{name}' failed: {e}", exc_info=True)
                    checks[name] = f"error: {str(e)}"
                    all_healthy = False
            
            if not all_healthy:
                checks["status"] = "unhealthy"
            
            return checks

    # ========================================================================
    # HELPERS
    # ========================================================================

    def register_health_check(self, name: str, check_func: Callable[[], bool]) -> None:
        """
        Health check fonksiyonu kaydet
        
        Args:
            name: Check adı
            check_func: Boolean dönen kontrol fonksiyonu
        
        Örnek:
            >>> factory.register_health_check("database", lambda: db.is_connected())
        """
        self._health_checks[name] = check_func
        self.logger.info(f"Health check registered: {name}")
    
    def include_router(self, router: "APIRouter", **kwargs) -> None:
        """
        Router ekle
        
        Args:
            router: Eklenecek APIRouter
            **kwargs: include_router'a geçilecek parametreler (prefix, tags, vb.)
        """
        if not self._app:
            self.logger.warning("Cannot include router: app not created yet. Call create() first.")
            return

        prefix = kwargs.get("prefix", "")
        tags = kwargs.get("tags", [])
        self.logger.info(
            f"Registering router: prefix={prefix}, tags={tags}",
            extra={"prefix": prefix, "tags": tags}
        )
        self._app.include_router(router, **kwargs)

    def add_middleware(self, middleware_class: type, **kwargs) -> None:
        """
        Middleware ekle
        
        Args:
            middleware_class: Middleware sınıfı
            **kwargs: Middleware parametreleri
        """
        if not self._app:
            raise RuntimeError("Önce create() çağrılmalı")
        self.logger.info(f"Adding middleware: {middleware_class.__name__}")
        self._app.add_middleware(middleware_class, **kwargs)
    
    def add_exception_handler(self, exc_class: type, handler: Callable) -> None:
        """
        Exception handler ekle
        
        Args:
            exc_class: Exception sınıfı
            handler: Handler fonksiyonu
        """
        if not self._app:
            raise RuntimeError("Önce create() çağrılmalı")
        self.logger.info(f"Adding exception handler: {exc_class.__name__}")
        self._app.add_exception_handler(exc_class, handler)