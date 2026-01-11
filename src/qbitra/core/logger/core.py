from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, List, Union, Dict, Any
from logging.handlers import QueueHandler

from .handlers import (
    AsyncHandler,
    AsyncConsoleHandler,
    AsyncRotatingFileHandler,
)
from .formatters import (
    JSONFormatter,
    PrettyFormatter,
    CompactFormatter
)
from .context import get_current_context, TraceContext



class TraceContextFilter(logging.Filter):
    """
    Log kayıtlarına trace context bilgilerini ekler.
    
    Bu filter, her log kaydına aktif trace context'ten
    trace_id, span_id gibi bilgileri otomatik ekler.
    """
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Log kaydını filtreler ve trace bilgilerini ekler."""
        try:
            ctx = get_current_context()
            
            if ctx:
                trace_data = ctx.to_dict()
                for key, value in trace_data.items():
                    setattr(record, key, value)
        except Exception:
            # Context alınamazsa log yazma işlemini engelleme
            # Sadece trace bilgisi eklenmez
            pass
        
        return True
    

@dataclass
class HandlerConfig:
    """Handler + Formatter eşleştirmesi."""
    handler: Union[AsyncHandler, logging.Handler]
    formatter: Optional[logging.Formatter] = None
    level: Optional[int] = None


def setup_logger(
    name: str = "root",
    level: int = logging.INFO,
    service_name: Optional[str] = None,
    handlers: Optional[List[HandlerConfig]] = None,
    add_trace_filter: bool = True,
    return_handlers: bool = False
) -> Union[logging.Logger, tuple[logging.Logger, List[AsyncHandler]]]:
    """
    Logger oluşturur.
    
    Args:
        name:         Logger adı
        level:        Log seviyesi
        service_name: Servis adı (default: name)
        handlers:     HandlerConfig listesi
        add_trace_filter: Trace filter ekle
        return_handlers: Handler'ları da döndür mü? (default: False)
                        True ise (logger, handlers) tuple döner
    
    Returns:
        Logger veya (Logger, List[AsyncHandler]) tuple
    
    Kullanım:
        # Basit - default console handler (geriye uyumlu)
        logger = setup_logger("myapp")
        
        # Servis adıyla
        logger = setup_logger("myapp", service_name="order-service")
        
        # Handler'ları da al (yeni özellik)
        logger, handlers = setup_logger("myapp", return_handlers=True)
        
        # Program sonunda (opsiyonel - atexit zaten var)
        for handler in handlers:
            handler.stop()
        
        # Farklı formatter'larla
        logger = setup_logger("myapp", handlers=[
            HandlerConfig(AsyncConsoleHandler(), PrettyFormatter()),
            HandlerConfig(AsyncRotatingFileHandler("app.log"), JSONFormatter()),
        ])
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.handlers.clear()
    logger.propagate = False
    
    # Effective service name
    svc = service_name or name
    
    # Default handler
    if not handlers:
        handlers = [
            HandlerConfig(
                handler=AsyncConsoleHandler(level=level),
                formatter=PrettyFormatter(service_name=svc)
            )
        ]
    
    # Handler'ları ekle ve topla
    created_handlers: List[AsyncHandler] = []
    
    for config in handlers:
        handler = config.handler
        formatter = config.formatter or PrettyFormatter(service_name=svc)
        handler_level = config.level or level
        
        if isinstance(handler, AsyncHandler):
            handler.handler.setFormatter(formatter)
            handler.handler.setLevel(handler_level)
            logger.addHandler(handler.get_queue_handler())
            created_handlers.append(handler)  # Handler'ı kaydet
        else:
            handler.setFormatter(formatter)
            handler.setLevel(handler_level)
            logger.addHandler(handler)
    
    if add_trace_filter:
        # Duplicate filter kontrolü
        has_trace_filter = any(isinstance(f, TraceContextFilter) for f in logger.filters)
        if not has_trace_filter:
            logger.addFilter(TraceContextFilter())
    
    # Return type'a göre döndür
    if return_handlers:
        return logger, created_handlers
    else:
        return logger


def configure_logger(
    logger: logging.Logger,
    level: Optional[int] = None,
    service_name: Optional[str] = None,
    handlers: Optional[List[HandlerConfig]] = None,
    add_trace_filter: bool = True
) -> logging.Logger:
    """
    Mevcut logger'ı yapılandırır.
    
    Args:
        logger:       Yapılandırılacak logger
        level:        Log seviyesi (None = değiştirme)
        service_name: Servis adı (default: logger.name)
        handlers:     HandlerConfig listesi (None = mevcut handler'ları koru)
        add_trace_filter: Trace filter ekle
    
    Kullanım:
        logger = logging.getLogger("myapp")
        configure_logger(logger, level=logging.DEBUG, service_name="order-api", handlers=[
            HandlerConfig(AsyncConsoleHandler(), JSONFormatter())
        ])
    """
    # Effective service name
    svc = service_name or logger.name
    
    if level is not None:
        logger.setLevel(level)
    
    if handlers:
        logger.handlers.clear()
        
        for config in handlers:
            handler = config.handler
            formatter = config.formatter or PrettyFormatter(service_name=svc)
            # logger.level NOTSET olabilir, effective level kullan
            handler_level = config.level or logger.getEffectiveLevel()
            
            if isinstance(handler, AsyncHandler):
                handler.handler.setFormatter(formatter)
                handler.handler.setLevel(handler_level)
                logger.addHandler(handler.get_queue_handler())
            else:
                handler.setFormatter(formatter)
                handler.setLevel(handler_level)
                logger.addHandler(handler)
    
    if add_trace_filter:
        has_trace_filter = any(isinstance(f, TraceContextFilter) for f in logger.filters)
        if not has_trace_filter:
            logger.addFilter(TraceContextFilter())
    
    return logger


def setup_console_logger(
    name: str = "root",
    level: int = logging.INFO,
    service_name: Optional[str] = None,
    use_colors: bool = True,
    return_handlers: bool = False
) -> Union[logging.Logger, tuple[logging.Logger, List[AsyncHandler]]]:
    """
    Sadece console handler ile logger kurar.
    
    Args:
        name:         Logger adı
        level:        Log seviyesi
        service_name: Servis adı
        use_colors:   Renkli çıktı kullan
        return_handlers: Handler'ları da döndür mü? (default: False)
    
    Kullanım:
        logger = setup_console_logger("myapp", use_colors=True)
        logger, handlers = setup_console_logger("myapp", return_handlers=True)
    """
    
    return setup_logger(
        name=name,
        level=level,
        handlers=[
            HandlerConfig(
                handler=AsyncConsoleHandler(level=level),
                formatter=PrettyFormatter(
                    service_name=service_name or name,
                    use_colors=use_colors
                )
            )
        ],
        return_handlers=return_handlers
    )


def setup_file_logger(
    name: str = "root",
    level: int = logging.INFO,
    service_name: Optional[str] = None,
    filename: str = "app.log",
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
    compress: bool = True,
    format_type: str = "json",
    return_handlers: bool = False
) -> Union[logging.Logger, tuple[logging.Logger, List[AsyncHandler]]]:
    """
    Sadece file handler ile logger kurar.
    
    Args:
        name:         Logger adı
        level:        Log seviyesi
        service_name: Servis adı
        filename:     Log dosyası yolu
        max_bytes:    Maksimum dosya boyutu (default: 10MB)
        backup_count: Backup dosya sayısı
        compress:     Sıkıştırma kullan
        format_type:  "json", "compact", veya "pretty"
        return_handlers: Handler'ları da döndür mü? (default: False)
    
    Kullanım:
        logger = setup_file_logger("myapp", filename="app.log", format_type="json")
        logger, handlers = setup_file_logger("myapp", return_handlers=True)
    """
    
    # Formatter seç
    svc = service_name or name
    if format_type == "json":
        formatter = JSONFormatter(service_name=svc)
    elif format_type == "compact":
        formatter = CompactFormatter(service_name=svc)
    elif format_type == "pretty":
        formatter = PrettyFormatter(service_name=svc, use_colors=False)
    else:
        valid_formats = ["json", "compact", "pretty"]
        raise ValueError(
            f"Geçersiz format_type: '{format_type}'. "
            f"Geçerli değerler: {', '.join(valid_formats)}"
        )
    
    return setup_logger(
        name=name,
        level=level,
        handlers=[
            HandlerConfig(
                handler=AsyncRotatingFileHandler(
                    filename=filename,
                    max_bytes=max_bytes,
                    backup_count=backup_count,
                    compress=compress,
                    level=level
                ),
                formatter=formatter
            )
        ],
        return_handlers=return_handlers
    )