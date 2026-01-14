from typing import Optional, Callable
from fastapi import FastAPI, APIRouter
from qbitra.core.qbitra.app import AppFactory, AppConfig
from qbitra.core.qbitra.server import ServerManager, ServerConfig
from qbitra.core.qbitra_logger import get_logger


class QBitra:
    def __init__(
        self,
        app_config: Optional[AppConfig] = None,
        server_config: Optional[ServerConfig] = None
    ):
        # Çekirdek qbitra logger'ı (logs/core/qbitra/service.log)
        self.logger = get_logger("qbitra", parent_folder="core")
        self.app_config = app_config or AppConfig.from_config()
        self.server_config = server_config or ServerConfig.from_config()
        self.app_factory = AppFactory(self.app_config)
        self.server_manager = ServerManager(self.server_config)
    
    def create_app(self, lifespan: Optional[Callable] = None) -> FastAPI:
        return self.app_factory.create(lifespan=lifespan)
    
    def run(self, app: Optional[FastAPI] = None, app_import_string: Optional[str] = None) -> None:
        if app is None:
            app = self.create_app()
        self.server_manager.start(app, app_import_string=app_import_string)
    
    def include_router(self, router: APIRouter, **kwargs) -> None:
        self.app_factory.include_router(router, **kwargs)
    
    def add_middleware(self, middleware_class: type, **kwargs) -> None:
        self.app_factory.add_middleware(middleware_class, **kwargs)
    
    def add_exception_handler(self, exc_class: type, handler: Callable) -> None:
        self.app_factory.add_exception_handler(exc_class, handler)
    
    def register_health_check(self, name: str, check_func: Callable[[], bool]) -> None:
        self.app_factory.register_health_check(name, check_func)
    
    @property
    def app(self) -> Optional[FastAPI]:
        return self.app_factory.app
    
    @property
    def is_running(self) -> bool:
        return self.server_manager.is_running
    
    def get_info(self) -> dict:
        info = self.server_manager.get_info()
        info.update({
            "app_title": self.app_config.title,
            "app_version": self.app_config.version,
            "app_env": self.app_config.app_env,
        })
        return info
