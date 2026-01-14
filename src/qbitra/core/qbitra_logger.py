"""
QBitra Logger Manager
=====================

Sade ve merkezi logger yönetim sistemi.

Yapı:
    src/logs/
        ├── app.log          (Tüm loglar, Pretty format)
        ├── error.log        (ERROR+ loglar, JSON format)
        └── {service_name}/
            └── service.log  (Servis logları, JSON format)

Kullanım:
    from qbitra.core.qbitra_logger import get_logger
    
    # Root logger (app.log + error.log)
    logger = get_logger()
    logger.info("Application started")
    
    # Service logger (logs/user_service/service.log)
    logger = get_logger("user_service")
    logger.info("User created", extra={"user_id": "123"})
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, Dict

from .logger.core import setup_logger, HandlerConfig
from .logger.handlers import AsyncRotatingFileHandler
from .logger.formatters import PrettyFormatter, JSONFormatter


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

# Log dizini (src/logs/)
LOGS_DIR = Path(__file__).parent.parent.parent / "logs"

# Rotation ayarları
MAX_BYTES = 10 * 1024 * 1024  # 10MB
BACKUP_COUNT = 5
COMPRESS = True

# Log seviyeleri
ROOT_LEVEL = logging.INFO
ERROR_LEVEL = logging.ERROR
# Servis logger seviyeleri (daha detaylı log için DEBUG)
SERVICE_LEVEL = logging.DEBUG
# API access log seviyesi
API_ACCESS_LEVEL = logging.INFO


# ═══════════════════════════════════════════════════════════════════════════════
# LOGGER MANAGER
# ═══════════════════════════════════════════════════════════════════════════════

class QbitraLoggerManager:
    """
    Logger yönetim sınıfı.
    
    Singleton pattern ile tüm logger'ları merkezi yönetir.
    """
    
    _instance: Optional["QbitraLoggerManager"] = None
    _initialized: bool = False
    
    def __new__(cls) -> "QbitraLoggerManager":
        """Singleton instance döndürür."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Manager'ı başlatır (sadece bir kez çalışır)."""
        if self._initialized:
            return
        
        # Logger cache
        self._loggers: Dict[str, logging.Logger] = {}
        self._handlers: Dict[str, list] = {}
        
        # Log dizinini oluştur
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        
        # Root logger'ı başlat
        self._setup_root_logger()
        # API access logger'ı başlat
        self._setup_api_access_logger()
        
        self._initialized = True
    
    # ────────────────────────────────────────────────────────────────────────
    # ROOT LOGGER
    # ────────────────────────────────────────────────────────────────────────
    def _setup_root_logger(self) -> None:
        """
        Root logger'ı kurar.
        
        Handlers:
            1. app.log     - Tüm loglar (INFO+), Pretty format
            2. error.log   - Sadece ERROR+, JSON format
        """
        handlers = [
            # app.log - Tüm loglar
            HandlerConfig(
                handler=AsyncRotatingFileHandler(
                    filename=str(LOGS_DIR / "app.log"),
                    max_bytes=MAX_BYTES,
                    backup_count=BACKUP_COUNT,
                    compress=COMPRESS,
                    level=ROOT_LEVEL,
                ),
                formatter=PrettyFormatter(
                    service_name="qbitra",
                    use_colors=False,  # Dosyaya renk kodu yazılmaz
                ),
                level=ROOT_LEVEL,
            ),
            # error.log - Sadece hatalar
            HandlerConfig(
                handler=AsyncRotatingFileHandler(
                    filename=str(LOGS_DIR / "error.log"),
                    max_bytes=MAX_BYTES,
                    backup_count=BACKUP_COUNT,
                    compress=COMPRESS,
                    level=ERROR_LEVEL,
                ),
                formatter=JSONFormatter(
                    service_name="qbitra",
                    include_location=True,   # Hata yerini göster
                    include_exception=True,  # Traceback bilgisi
                ),
                level=ERROR_LEVEL,
            ),
        ]
        
        logger, handler_instances = setup_logger(
            name="qbitra",
            level=ROOT_LEVEL,
            handlers=handlers,
            return_handlers=True,
        )
        
        self._loggers["root"] = logger
        self._handlers["root"] = handler_instances
    
    # ────────────────────────────────────────────────────────────────────────
    # API ACCESS LOGGER
    # ────────────────────────────────────────────────────────────────────────
    def _setup_api_access_logger(self) -> None:
        """
        API access logger'ını kurar.
        
        Dosya: logs/api.log
        Format: JSON (method, path, status_code, trace/correlation vb.)
        """
        handlers = [
            HandlerConfig(
                handler=AsyncRotatingFileHandler(
                    filename=str(LOGS_DIR / "api.log"),
                    max_bytes=MAX_BYTES,
                    backup_count=BACKUP_COUNT,
                    compress=COMPRESS,
                    level=API_ACCESS_LEVEL,
                ),
                formatter=JSONFormatter(
                    service_name="api",
                    include_location=False,
                    include_exception=False,
                ),
                level=API_ACCESS_LEVEL,
            )
        ]
        
        # ÖNEMLİ:
        #  - Access logger için benzersiz bir logger name kullanıyoruz ("qbitra.api_access")
        #  - Böylece "api" servisi için oluşturulan logger'larla (qbitra.api) çakışmıyor.
        #  - Daha önce aynı name ("qbitra.api") kullanıldığı için,
        #    service logger yaratılırken handler'lar temizleniyor ve api.log boşa düşüyordu.
        logger, handler_instances = setup_logger(
            name="qbitra.api_access",
            level=API_ACCESS_LEVEL,
            handlers=handlers,
            return_handlers=True,
        )
        
        self._loggers["api_access"] = logger
        self._handlers["api_access"] = handler_instances
    
    # ────────────────────────────────────────────────────────────────────────
    # GENEL LOGGER ALMA
    # ────────────────────────────────────────────────────────────────────────
    def get_logger(
        self,
        service_name: Optional[str] = None,
        parent_folder: Optional[str] = None,
    ) -> logging.Logger:
        """
        Logger döndürür.
        
        Args:
            service_name:  Servis adı (None ise root logger)
            parent_folder: Opsiyonel üst klasör (örn: "services").
                           Belirtilirse log yolu:
                               logs/{parent_folder}/{service_name}/service.log
                           Aksi halde:
                               logs/{service_name}/service.log
        """
        # Root logger
        if service_name is None:
            return self._loggers["root"]
        
        # Cache key: parent_folder + service_name kombinasyonu
        cache_key = f"{parent_folder}:{service_name}" if parent_folder else service_name
        
        # Cache'den dön
        if cache_key in self._loggers:
            return self._loggers[cache_key]
        
        # Yeni service logger oluştur
        logger = self._create_service_logger(service_name, parent_folder=parent_folder)
        self._loggers[cache_key] = logger
        
        return logger
    
    def _create_service_logger(
        self,
        service_name: str,
        parent_folder: Optional[str] = None,
    ) -> logging.Logger:
        """
        Servis için özel logger oluşturur.
        
        Yapı:
            Varsayılan:
                logs/{service_name}/service.log (JSON format)
            
            parent_folder verildiğinde:
                logs/{parent_folder}/{service_name}/service.log (JSON format)
        """
        # Servis dizini
        if parent_folder:
            # Örn: LOGS_DIR / "services" / "auth_service"
            service_dir = LOGS_DIR / parent_folder / service_name
        else:
            # Geriye uyumlu: LOGS_DIR / "auth_service"
            service_dir = LOGS_DIR / service_name
        service_dir.mkdir(parents=True, exist_ok=True)
        
        # Handler: logs/{...}/{service_name}/service.log
        handlers = [
            HandlerConfig(
                handler=AsyncRotatingFileHandler(
                    filename=str(service_dir / "service.log"),
                    max_bytes=MAX_BYTES,
                    backup_count=BACKUP_COUNT,
                    compress=COMPRESS,
                    level=SERVICE_LEVEL,
                ),
                formatter=JSONFormatter(
                    service_name=service_name,
                    include_location=False,   # Servis loglarında location yok
                    include_exception=False,  # Servis loglarında traceback yok
                ),
                level=SERVICE_LEVEL,
            ),
        ]
        
        # Logger adı: qbitra.{service_name}
        logger_name = f"qbitra.{service_name}"
        
        logger, handler_instances = setup_logger(
            name=logger_name,
            level=SERVICE_LEVEL,
            service_name=service_name,
            handlers=handlers,
            return_handlers=True,
        )
        # Logger propagate ayarı setup_logger içinde otomatik yapılıyor
        # (qbitra.* logger'lar otomatik olarak root'a propagate eder)
        
        # Handler'ları cache'le (aynı cache_key mantığı get_logger içinde)
        cache_key = f"{parent_folder}:{service_name}" if parent_folder else service_name
        self._handlers[cache_key] = handler_instances
        
        return logger
    
    def shutdown(self) -> None:
        """
        Tüm handler'ları durdurur.
        
        Not: Normalde atexit ile otomatik çalışır, 
        manuel shutdown gerekirse kullanılır.
        """
        for service_name, handlers in self._handlers.items():
            for handler in handlers:
                try:
                    handler.stop()
                except Exception:
                    pass


# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════════════════════

# Global manager instance
_manager = QbitraLoggerManager()


def get_logger(
    service_name: Optional[str] = None,
    parent_folder: Optional[str] = None,
) -> logging.Logger:
    """
    Logger döndürür.
    
    Args:
        service_name:  Servis adı (None ise root logger)
        parent_folder: Opsiyonel üst klasör (örn: "services").
    """
    return _manager.get_logger(service_name=service_name, parent_folder=parent_folder)


def get_access_logger() -> logging.Logger:
    """
    Sadece API access logları için özel logger döndürür.
    
    Dosya:
        logs/api.log  (JSON format)
    """
    return _manager._loggers["api_access"]


def shutdown_logger() -> None:
    """
    Tüm logger'ları kapatır.
    
    Not: Normalde gerekli değil (atexit ile otomatik).
    """
    _manager.shutdown()


# Re-export trace utilities (kullanım kolaylığı için)
from .logger.context import trace, get_current_context
from .logger.decorators import with_trace

__all__ = [
    "get_logger",
    "get_access_logger",
    "shutdown_logger",
    "trace",
    "get_current_context",
    "with_trace",
]
