"""
ROTATING FILE LOGGER - Merkezi Log Yönetimi
==========================================

Amaç:
    - Uygulama genelinde merkezi log yönetimi
    - Otomatik dosya rotasyonu (5 dosya maksimum)
    - Boyut bazlı log dosyası döngüsü
    - Güncel loglar her zaman aynı yerde

Özellikler:
    - Maksimum 5 log dosyası tutulur
    - Her dosya maksimum 10MB
    - Eski dosyalar otomatik silinir
    - Thread-safe logging
    - Farklı log seviyeleri (DEBUG, INFO, WARNING, ERROR, CRITICAL)

Kullanım:
    from miniflow.core.logger import get_logger
    
    logger = get_logger(__name__)
    logger.info("İşlem başarılı")
    logger.error("Hata oluştu", exc_info=True)
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional


# Log dizini
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# Log dosyası ayarları
LOG_FILE = LOG_DIR / "miniflow.log"
MAX_BYTES = 10 * 1024 * 1024  # 10 MB
BACKUP_COUNT = 4  # Ana dosya + 4 backup = toplam 5 dosya

# Log formatı
LOG_FORMAT = (
    "[%(asctime)s] "
    "[%(levelname)-8s] "
    "[%(name)s:%(funcName)s:%(lineno)d] "
    "%(message)s"
)
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


# Global logger instance'ları
_loggers = {}
_configured = False


def configure_root_logger(
    level: int = logging.INFO,
    log_file: Optional[Path] = None,
    max_bytes: int = MAX_BYTES,
    backup_count: int = BACKUP_COUNT,
    console_output: bool = True
) -> None:
    """
    Root logger'ı yapılandır.
    
    Bu fonksiyon sadece bir kez çağrılmalı (uygulama başlangıcında).
    
    Args:
        level: Log seviyesi (logging.DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Log dosyası yolu (None ise default kullanılır)
        max_bytes: Her log dosyasının maksimum boyutu (byte)
        backup_count: Tutulacak backup dosya sayısı (toplam = backup_count + 1)
        console_output: Console'a da log yazılsın mı?
    
    Examples:
        >>> # Uygulama başlangıcında
        >>> configure_root_logger(level=logging.INFO)
        
        >>> # Development ortamında DEBUG seviyesi
        >>> configure_root_logger(level=logging.DEBUG, console_output=True)
        
        >>> # Production ortamında sadece dosyaya log
        >>> configure_root_logger(level=logging.WARNING, console_output=False)
    """
    global _configured
    
    if _configured:
        return
    
    # Root logger'ı al
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Mevcut handler'ları temizle
    root_logger.handlers.clear()
    
    # Formatter oluştur
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    
    # Rotating File Handler ekle
    log_path = log_file or LOG_FILE
    file_handler = RotatingFileHandler(
        filename=str(log_path),
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # Console Handler ekle (isteğe bağlı)
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    _configured = True
    
    # İlk log mesajı
    root_logger.info(
        f"Logger configured: level={logging.getLevelName(level)}, "
        f"log_file={log_path}, max_files={backup_count + 1}"
    )


def get_logger(name: str = None) -> logging.Logger:
    """
    İsimlendirilmiş logger instance'ı döndür.
    
    Her modül kendi logger'ını almalı. Bu sayede log mesajlarında
    hangi modülden geldiği görünür.
    
    Args:
        name: Logger adı (genelde __name__ kullanılır)
    
    Returns:
        logging.Logger: Logger instance
    
    Examples:
        >>> # Modül başında
        >>> logger = get_logger(__name__)
        >>> 
        >>> # Kullanım
        >>> logger.info("İşlem başladı")
        >>> logger.warning("Dikkat edilmesi gereken durum")
        >>> logger.error("Hata oluştu", exc_info=True)
        >>> 
        >>> # Exception ile birlikte
        >>> try:
        ...     risky_operation()
        ... except Exception as e:
        ...     logger.error(f"İşlem başarısız: {e}", exc_info=True)
    """
    # Root logger henüz yapılandırılmadıysa, default ayarlarla yapılandır
    if not _configured:
        configure_root_logger()
    
    # Cache'den döndür veya yeni oluştur
    if name and name not in _loggers:
        _loggers[name] = logging.getLogger(name)
    
    return _loggers.get(name) or logging.getLogger(name)


def log_function_call(func):
    """
    Decorator: Fonksiyon çağrılarını otomatik logla.
    
    Fonksiyon başlangıç ve bitiş zamanlarını, parametreleri ve
    dönüş değerlerini loglar. Hata durumunda exception'ları yakalar ve loglar.
    
    Examples:
        >>> @log_function_call
        ... def calculate_total(items):
        ...     return sum(items)
        >>> 
        >>> result = calculate_total([1, 2, 3])
        # Log: [INFO] calculate_total called with args=(([1, 2, 3],), {})
        # Log: [INFO] calculate_total returned: 6
    """
    from functools import wraps
    
    logger = get_logger(func.__module__)
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger.debug(f"{func.__name__} called with args={args}, kwargs={kwargs}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"{func.__name__} returned: {result}")
            return result
        except Exception as e:
            logger.error(
                f"{func.__name__} raised {type(e).__name__}: {e}",
                exc_info=True
            )
            raise
    
    return wrapper


def log_exception(logger: logging.Logger = None):
    """
    Context manager: Exception'ları otomatik logla.
    
    Args:
        logger: Kullanılacak logger (None ise root logger kullanılır)
    
    Examples:
        >>> with log_exception():
        ...     risky_operation()
        # Exception oluşursa otomatik loglanır
        
        >>> logger = get_logger(__name__)
        >>> with log_exception(logger):
        ...     database_operation()
    """
    from contextlib import contextmanager
    
    @contextmanager
    def _log_exception():
        try:
            yield
        except Exception as e:
            log = logger or get_logger()
            log.error(
                f"Exception caught: {type(e).__name__}: {e}",
                exc_info=True
            )
            raise
    
    return _log_exception()


def get_log_files() -> list:
    """
    Mevcut log dosyalarının listesini döndür.
    
    Returns:
        list: Log dosyalarının Path objelerinin listesi (yeniden eskiye)
    
    Examples:
        >>> files = get_log_files()
        >>> for f in files:
        ...     print(f"{f.name}: {f.stat().st_size} bytes")
    """
    if not LOG_DIR.exists():
        return []
    
    # miniflow.log ve miniflow.log.1, .2, .3, .4 dosyalarını bul
    log_files = []
    
    # Ana log dosyası
    if LOG_FILE.exists():
        log_files.append(LOG_FILE)
    
    # Backup dosyaları
    for i in range(1, BACKUP_COUNT + 1):
        backup_file = Path(f"{LOG_FILE}.{i}")
        if backup_file.exists():
            log_files.append(backup_file)
    
    # Değiştirilme tarihine göre sırala (yeni -> eski)
    log_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    return log_files


def get_log_stats() -> dict:
    """
    Log dosyaları hakkında istatistikler döndür.
    
    Returns:
        dict: Log istatistikleri
            - total_files: Toplam dosya sayısı
            - total_size_mb: Toplam boyut (MB)
            - files: Dosya detayları
    
    Examples:
        >>> stats = get_log_stats()
        >>> print(f"Toplam {stats['total_files']} log dosyası")
        >>> print(f"Toplam {stats['total_size_mb']:.2f} MB")
    """
    files = get_log_files()
    
    total_size = sum(f.stat().st_size for f in files)
    
    file_details = []
    for f in files:
        stat = f.stat()
        file_details.append({
            'name': f.name,
            'size_mb': stat.st_size / (1024 * 1024),
            'modified': stat.st_mtime
        })
    
    return {
        'total_files': len(files),
        'total_size_mb': total_size / (1024 * 1024),
        'files': file_details
    }


def clear_logs() -> int:
    """
    Tüm log dosyalarını temizle.
    
    ⚠️ DİKKAT: Bu işlem geri alınamaz!
    
    Returns:
        int: Silinen dosya sayısı
    
    Examples:
        >>> # Test ortamında logları temizle
        >>> if os.getenv('APP_ENV') == 'test':
        ...     clear_logs()
    """
    files = get_log_files()
    count = 0
    
    for f in files:
        try:
            f.unlink()
            count += 1
        except Exception as e:
            logger = get_logger(__name__)
            logger.error(f"Log dosyası silinemedi {f}: {e}")
    
    return count


# Uygulama başlangıcında otomatik yapılandırma
# (sadece logger import edildiğinde, kullanılmadığında çalışmaz)
def _auto_configure():
    """Otomatik yapılandırma (sadece ilk import'ta çalışır)"""
    import os
    
    # Ortam değişkeninden log seviyesini al
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    level = level_map.get(log_level, logging.INFO)
    
    # Test ortamında console output kapat
    console = os.getenv('APP_ENV', 'development') != 'test'
    
    # Yapılandır
    configure_root_logger(level=level, console_output=console)


# İlk import'ta otomatik yapılandır
_auto_configure()


# Public API
__all__ = [
    'get_logger',
    'configure_root_logger',
    'log_function_call',
    'log_exception',
    'get_log_files',
    'get_log_stats',
    'clear_logs',
]
