import signal
from fastapi import FastAPI
from dataclasses import dataclass, field
from typing import Optional, List

from qbitra.utils.handlers.configuration_handler import ConfigurationHandler
from qbitra.core.qbitra_logger import get_logger

@dataclass
class ServerConfig:
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    reload: bool = False
    reload_dirs: List[str] = field(default_factory=list)
    timeout_keep_alive: int = 5
    timeout_graceful_shutdown: int = 30
    log_level: str = "info"
    access_log: bool = True
    environment: str = "development"

    def __post_init__(self):
        """Validation"""
        if self.port < 1 or self.port > 65535:
            raise ValueError(f"Geçersiz port: {self.port}")
        
        if self.workers < 0:
            raise ValueError(f"Workers negatif olamaz: {self.workers}")
        
        # Reload açıkken workers 1 olmalı
        if self.reload and self.workers > 1:
            self.workers = 1

    @classmethod
    def from_config(cls):
        return cls(
            host=ConfigurationHandler.get_value_as_str("Server", "host", fallback="0.0.0.0"),
            port=ConfigurationHandler.get_value_as_int("Server", "port", fallback=8000),
            workers=ConfigurationHandler.get_value_as_int("Server", "workers", fallback=1),
            reload=ConfigurationHandler.get_value_as_bool("Server", "reload", fallback=False),
            reload_dirs=ConfigurationHandler.get_value_as_list("Server", "reload_dirs", fallback=[]),
            timeout_keep_alive=ConfigurationHandler.get_value_as_int("Server", "timeout_keep_alive", fallback=5),
            timeout_graceful_shutdown=ConfigurationHandler.get_value_as_int("Server", "timeout_graceful_shutdown", fallback=30),
            log_level=ConfigurationHandler.get_value_as_str("Server", "log_level", fallback="info"),
            access_log=ConfigurationHandler.get_value_as_bool("Server", "access_log", fallback=True),
            environment=ConfigurationHandler.get_value_as_str("Server", "environment", fallback="development")
        )
    
    @property
    def is_production(self) -> bool:
        """Production ortamı mı?"""
        return self.environment.lower() in ("prod", "production")
    
    @property
    def is_development(self) -> bool:
        """Development ortamı mı?"""
        return self.environment.lower() in ("dev", "development")


class ServerManager:
    """Uvicorn sunucu yöneticisi"""
    
    def __init__(self, config: ServerConfig):
        self.config = config
        self.server = None
        self._is_running = False
        # Sunucu / process seviyesi logger
        self.logger = get_logger("server", parent_folder="core")

    def start(self, app: "FastAPI", app_import_string: Optional[str] = None) -> None:
        """
        Uvicorn sunucusunu başlatır
        
        Args:
            app: FastAPI uygulama instance'ı
            app_import_string: Reload modu için app import string'i (örn: "qbitra.app:app")
        """
        import uvicorn

        self._setup_signal_handlers()
        self._is_running = True
        
        uvicorn_kwargs = self._build_uvicorn_config()
        
        # Konsolda da kritik başlangıç bilgisini göster
        print(
            f"[QBITRA] Starting server on {self.config.host}:{self.config.port} "
            f"(env={self.config.environment}, workers={self.config.workers if not self.config.reload else 1}, "
            f"reload={self.config.reload})"
        )
        self.logger.info(
            f"Starting server on {self.config.host}:{self.config.port}",
            extra={
                "host": self.config.host,
                "port": self.config.port,
                "workers": self.config.workers if not self.config.reload else 1,
                "reload": self.config.reload,
                "environment": self.config.environment
            }
        )

        if self.config.reload:
            if not app_import_string:
                raise ValueError("Reload modu için 'app_import_string' parametresi zorunludur")
            self.logger.info(f"Starting in reload mode with app: {app_import_string}")
            uvicorn.run(app_import_string, **uvicorn_kwargs)
        else:
            self.logger.info(f"Starting with {self.config.workers} worker(s)")
            uvicorn.run(app, **uvicorn_kwargs)
    
    def _build_uvicorn_config(self) -> dict:
        """Uvicorn yapılandırmasını oluşturur"""
        config = {
            "host": self.config.host,
            "port": self.config.port,
            "log_level": self.config.log_level,
            "access_log": self.config.access_log,
            "timeout_keep_alive": self.config.timeout_keep_alive,
            "timeout_graceful_shutdown": self.config.timeout_graceful_shutdown,
            "log_config": None,  # Uvicorn'un kendi log config'ini disable et
        }
        
        if self.config.reload:
            config["reload"] = True
            config["reload_dirs"] = self.config.reload_dirs
        else:
            config["workers"] = self.config.workers
        
        return config
    
    def _setup_signal_handlers(self) -> None:
        """Signal handler'ları kurar (SIGTERM, SIGINT)"""
        def handle_shutdown(signum: int, frame) -> None:
            signal_name = signal.Signals(signum).name
            self.logger.info(f"Received {signal_name}, shutting down...")
            self.stop()  # stop() metodu flag'i güncelleyecek
        
        signal.signal(signal.SIGTERM, handle_shutdown)
        signal.signal(signal.SIGINT, handle_shutdown)
    
    def get_info(self) -> dict:
        """Sunucu bilgilerini döndürür"""
        base_url = f"http://{self.config.host}:{self.config.port}"
        
        return {
            "host": self.config.host,
            "port": self.config.port,
            "workers": self.config.workers if not self.config.reload else 1,
            "reload": self.config.reload,
            "environment": self.config.environment,
            "log_level": self.config.log_level,
            "url": base_url,
            "docs_url": f"{base_url}/docs" if self.config.is_development else None,
        }
    
    def stop(self) -> None:
        """
        Sunucuyu durdurur
        
        Not: Mevcut implementasyonda uvicorn.run() blocking olduğu için,
        bu metod sadece flag'i günceller. Gerçek durdurma signal handler'lar
        (SIGTERM, SIGINT) veya uvicorn'un kendi shutdown mekanizması ile yapılır.
        """
        if not self._is_running:
            self.logger.warning("Server is not running")
            return
        
        print("[QBITRA] Stopping server (shutdown requested)...")
        self.logger.info("Stopping server...")
        self._is_running = False
        
        # Eğer server instance varsa (async yapı için gelecekte kullanılabilir)
        if self.server is not None:
            try:
                # Uvicorn Server instance'ı varsa durdur
                if hasattr(self.server, 'should_exit'):
                    self.server.should_exit = True
                elif hasattr(self.server, 'stop'):
                    self.server.stop()
            except Exception as e:
                self.logger.error(f"Error stopping server instance: {e}", exc_info=True)
        
        self.logger.info("Server stop signal sent")
        print("[QBITRA] Server stop signal sent. Waiting for graceful shutdown...")
    
    @property
    def is_running(self) -> bool:
        """Sunucu çalışıyor mu?"""
        return self._is_running