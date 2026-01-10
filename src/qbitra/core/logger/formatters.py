from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Set


# ═══════════════════════════════════════════════════════════════════════════════
# ORTAK SABITLER
# ═══════════════════════════════════════════════════════════════════════════════

# Python logging'in standart alanları
# Bu alanlar JSON'a eklenmez (gereksiz/tekrar)
# Tek bir yerde tanımlanır, tüm formatter'lar kullanır (DRY)
RESERVED_LOG_ATTRS: frozenset[str] = frozenset({
    "name",           # Logger adı (service olarak ekliyoruz)
    "msg",            # Ham mesaj
    "args",           # Format argümanları
    "levelname",      # Level adı (level olarak ekliyoruz)
    "levelno",        # Level numarası
    "pathname",       # Dosya yolu
    "filename",       # Dosya adı
    "module",         # Modül adı
    "exc_info",       # Exception bilgisi
    "exc_text",       # Exception text
    "stack_info",     # Stack bilgisi
    "lineno",         # Satır numarası
    "funcName",       # Fonksiyon adı
    "created",        # Oluşturulma zamanı (float)
    "msecs",          # Milisaniye
    "relativeCreated",# Göreli zaman
    "thread",         # Thread ID
    "threadName",     # Thread adı
    "processName",    # Process adı
    "process",        # Process ID
    "message",        # Formatlanmış mesaj
    "taskName",       # Async task adı (Python 3.12+)
})

# Serialize edilecek maksimum derinlik (recursive yapılar için)
MAX_SERIALIZE_DEPTH = 10


# ═══════════════════════════════════════════════════════════════════════════════
# YARDIMCI FONKSİYONLAR
# ═══════════════════════════════════════════════════════════════════════════════

def get_record_timestamp(record: logging.LogRecord, use_utc: bool = True) -> datetime:
    """
    LogRecord'un oluşturulma zamanını datetime olarak döndürür.
    
    Args:
        record: Log kaydı
        use_utc: UTC mi local time mı
    
    Returns:
        datetime objesi
    """
    tz = timezone.utc if use_utc else None
    return datetime.fromtimestamp(record.created, tz=tz)


def serialize_value(value: Any, depth: int = 0) -> Any:
    """
    Değeri JSON-serializable formata dönüştürür.
    
    Args:
        value: Serialize edilecek değer
        depth: Mevcut derinlik (recursive protection)
    
    Returns:
        JSON-safe değer
    """
    # Derinlik kontrolü
    if depth > MAX_SERIALIZE_DEPTH:
        return f"<max depth {MAX_SERIALIZE_DEPTH} exceeded>"
    
    # Primitif tipler
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    
    # Liste/tuple
    if isinstance(value, (list, tuple)):
        return [serialize_value(v, depth + 1) for v in value]
    
    # Dict
    if isinstance(value, dict):
        return {str(k): serialize_value(v, depth + 1) for k, v in value.items()}
    
    # Set
    if isinstance(value, (set, frozenset)):
        return [serialize_value(v, depth + 1) for v in value]
    
    # Datetime
    if isinstance(value, datetime):
        return value.isoformat()
    
    # Bytes
    if isinstance(value, bytes):
        try:
            return value.decode("utf-8")
        except UnicodeDecodeError:
            return f"<bytes len={len(value)}>"
    
    # Diğer tipler string'e çevrilir
    try:
        return str(value)
    except Exception:
        return f"<unserializable: {type(value).__name__}>"


def get_extra_fields(record: logging.LogRecord) -> Dict[str, Any]:
    """
    Log record'dan extra alanları çıkarır.
    
    Args:
        record: Log kaydı
    
    Returns:
        Extra alanların dict'i
    """
    extras = {}
    for key, value in record.__dict__.items():
        if key not in RESERVED_LOG_ATTRS and not key.startswith("_"):
            extras[key] = serialize_value(value)
    return extras


def format_exception_info(record: logging.LogRecord, formatter: logging.Formatter) -> Optional[Dict[str, Any]]:
    """
    Exception bilgisini dict olarak döndürür.
    
    Not: Asenkron handler'larda exc_info tuple olarak geçirilmeli,
    True olarak geçirilirse farklı thread'de sys.exc_info() boş döner.
    
    Args:
        record: Log kaydı
        formatter: Traceback formatlamak için formatter instance
    
    Returns:
        Exception dict veya None
    """
    if not record.exc_info:
        return None
    
    exc_info = record.exc_info
    
    # exc_info True ise (nadir, genelde tuple gelir)
    # Asenkron handler'da bu çalışmaz ama yine de handle edelim
    if exc_info is True:
        import sys
        exc_info = sys.exc_info()
        if exc_info[0] is None:
            return None
    
    # Geçerli exception tuple kontrolü
    if not exc_info or exc_info[0] is None:
        return None
    
    return {
        "type": exc_info[0].__name__,
        "message": str(exc_info[1]) if exc_info[1] else None,
        "traceback": formatter.formatException(exc_info)
    }


# ═══════════════════════════════════════════════════════════════════════════════
# JSON FORMATTER
# ═══════════════════════════════════════════════════════════════════════════════

class JSONFormatter(logging.Formatter):
    """
    Yapılandırılmış JSON log formatı.
    
    Log aggregation sistemleri için ideal (ELK, Datadog, Splunk).
    
    Örnek çıktı:
        {"timestamp":"2025-01-07T12:00:00.123456+00:00","level":"INFO",
         "service":"order-service","message":"Order created","order_id":"ORD-123"}
    
    Özellikler:
        - ISO 8601 veya Unix timestamp
        - Extra alanlar otomatik eklenir
        - Exception detayları (type, message, traceback)
        - Thread-safe (record.created kullanır)
    """
    
    def __init__(
        self,
        service_name: Optional[str] = None,
        include_extra: bool = True,
        timestamp_format: str = "iso",
        include_location: bool = False,
        include_exception: bool = True
    ):
        """
        Args:
            service_name:     Servis adı (default: logger name)
            include_extra:    Extra alanları dahil et
            timestamp_format: "iso" veya "unix"
            include_location: Dosya/satır bilgisi ekle
            include_exception: Exception bilgisi (type, message, traceback) ekle
        """
        super().__init__()
        self.service_name = service_name
        self.include_extra = include_extra
        self.timestamp_format = timestamp_format
        self.include_location = include_location
        self.include_exception = include_exception
    
    def format(self, record: logging.LogRecord) -> str:
        """Log kaydını JSON string'e dönüştürür."""
        
        # Mesajı al
        message = record.getMessage()
        
        # Exception bilgisi varsa mesajdan ayır
        exception_data = None
        if self.include_exception:
            # Mesajda traceback varsa parse et
            if '\nTraceback (most recent call last):' in message:
                parts = message.split('\nTraceback (most recent call last):', 1)
                clean_message = parts[0].strip()
                traceback_text = 'Traceback (most recent call last):' + parts[1]
                
                # Exception type ve message'ı traceback'ten çıkar
                lines = traceback_text.strip().split('\n')
                last_line = lines[-1] if lines else ""
                
                exc_type = "Exception"
                exc_message = ""
                if ': ' in last_line:
                    exc_type, exc_message = last_line.split(': ', 1)
                elif last_line:
                    exc_type = last_line
                
                exception_data = {
                    "type": exc_type,
                    "message": exc_message,
                    "traceback": traceback_text
                }
                message = clean_message
        
        # Temel alanlar
        log_data: Dict[str, Any] = {
            "timestamp": self._format_timestamp(record),
            "level": record.levelname,
            "service": self.service_name or record.name,
            "message": message,
        }
        
        # Lokasyon bilgisi (opsiyonel)
        if self.include_location:
            log_data["location"] = {
                "file": record.filename,
                "line": record.lineno,
                "function": record.funcName
            }
        
        # Extra alanlar
        if self.include_extra:
            extras = get_extra_fields(record)
            log_data.update(extras)
        
        # Exception bilgisi ekle (opsiyonel)
        if exception_data:
            log_data["exception"] = exception_data
        
        # JSON serialize (hata korumalı)
        try:
            return json.dumps(log_data, ensure_ascii=False, default=str)
        except (TypeError, ValueError) as e:
            # Fallback: basit format
            return json.dumps({
                "timestamp": self._format_timestamp(record),
                "level": record.levelname,
                "service": self.service_name or record.name,
                "message": record.getMessage(),
                "_serialization_error": str(e)
            })
    
    def _format_timestamp(self, record: logging.LogRecord) -> str:
        """Record'un timestamp'ini formatlar."""
        dt = get_record_timestamp(record, use_utc=True)
        
        if self.timestamp_format == "unix":
            return str(record.created)
        
        return dt.isoformat(timespec="microseconds")


# ═══════════════════════════════════════════════════════════════════════════════
# PRETTY FORMATTER (Renkli Terminal)
# ═══════════════════════════════════════════════════════════════════════════════

class PrettyFormatter(logging.Formatter):
    """
    Terminal için renkli ve okunabilir log formatı.
    
    Geliştirme ortamında kullanım için ideal.
    
    Örnek çıktı:
        14:32:01 │ INFO     │ order-service   │ Order created │ order_id=ORD-123
        14:32:02 │ ERROR    │ order-service   │ DB error      │ error_code=E001
    
    Renkler:
        DEBUG    → Cyan
        INFO     → Green
        WARNING  → Yellow
        ERROR    → Red
        CRITICAL → Magenta (Bold)
    """
    
    # ANSI renk kodları
    COLORS = {
        "DEBUG":    "\033[36m",      # Cyan
        "INFO":     "\033[32m",      # Green
        "WARNING":  "\033[33m",      # Yellow
        "ERROR":    "\033[31m",      # Red
        "CRITICAL": "\033[35;1m",    # Magenta + Bold
    }
    RESET = "\033[0m"
    DIM = "\033[2m"
    BOLD = "\033[1m"
    
    def __init__(
        self,
        service_name: Optional[str] = None,
        use_colors: bool = True,
        use_utc: bool = False,
        show_date: bool = False
    ):
        """
        Args:
            service_name: Servis adı (override)
            use_colors:   ANSI renkleri kullan
            use_utc:      UTC zaman kullan (default: local)
            show_date:    Tarih göster (default: sadece saat)
        """
        super().__init__()
        self.service_name = service_name
        self.use_colors = use_colors
        self.use_utc = use_utc
        self.show_date = show_date
    
    def format(self, record: logging.LogRecord) -> str:
        """Log kaydını okunabilir formata dönüştürür."""
        
        # Zaman (record'dan al, tutarlılık için)
        dt = get_record_timestamp(record, use_utc=self.use_utc)
        if self.show_date:
            time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
        else:
            time_str = dt.strftime("%H:%M:%S")
        
        # Level (renkli veya düz)
        level = record.levelname
        if self.use_colors:
            color = self.COLORS.get(level, "")
            level_str = f"{color}{level:8}{self.RESET}"
        else:
            level_str = f"{level:8}"
        
        # Servis adı
        service = self.service_name or record.name
        
        # Mesaj
        message = record.getMessage()
        
        # Extra alanlar (key=value formatında)
        extras = get_extra_fields(record)
        if self.use_colors:
            extra_parts = [f"{self.DIM}{k}={v}{self.RESET}" for k, v in extras.items()]
        else:
            extra_parts = [f"{k}={v}" for k, v in extras.items()]
        extra_str = " ".join(extra_parts)
        
        # Final format
        if self.use_colors:
            line = (
                f"{self.DIM}{time_str}{self.RESET} │ "
                f"{level_str} │ "
                f"{self.BOLD}{service:15}{self.RESET} │ "
                f"{message}"
            )
        else:
            line = f"{time_str} │ {level_str} │ {service:15} │ {message}"
        
        # Extra alanları ekle
        if extra_str:
            line += f" │ {extra_str}"
        
        # Exception varsa ekle
        if record.exc_info:
            exc_text = self.formatException(record.exc_info)
            if self.use_colors:
                line += f"\n{self.COLORS['ERROR']}{exc_text}{self.RESET}"
            else:
                line += f"\n{exc_text}"
        
        return line


# ═══════════════════════════════════════════════════════════════════════════════
# COMPACT FORMATTER (Minimal)
# ═══════════════════════════════════════════════════════════════════════════════

class CompactFormatter(logging.Formatter):
    """
    Minimal tek satır format.
    
    Production log aggregation için ideal.
    Dosya boyutunu küçük tutar.
    
    Örnek çıktı:
        INFO order-service Order created order_id=ORD-123 user_id=usr-456
        ERROR payment-service Payment failed error=timeout exc_type=TimeoutError
    """
    
    def __init__(
        self,
        service_name: Optional[str] = None,
        include_timestamp: bool = False
    ):
        """
        Args:
            service_name:      Servis adı (override)
            include_timestamp: Zaman damgası ekle (default: hayır)
        """
        super().__init__()
        self.service_name = service_name
        self.include_timestamp = include_timestamp
    
    def format(self, record: logging.LogRecord) -> str:
        """Log kaydını minimal formata dönüştürür."""
        
        service = self.service_name or record.name
        message = record.getMessage()
        
        # Parçaları birleştir
        parts = []
        
        # Opsiyonel timestamp
        if self.include_timestamp:
            dt = get_record_timestamp(record, use_utc=True)
            parts.append(dt.strftime("%Y%m%dT%H%M%S"))
        
        parts.extend([record.levelname, service, message])
        
        # Extra alanları ekle
        extras = get_extra_fields(record)
        for key, value in extras.items():
            # Value'da boşluk varsa quote içine al
            str_value = str(value)
            if " " in str_value:
                parts.append(f'{key}="{str_value}"')
            else:
                parts.append(f"{key}={str_value}")
        
        # Exception bilgisi (compact formatta)
        if record.exc_info and record.exc_info[0] is not None:
            exc_type = record.exc_info[0].__name__
            exc_msg = str(record.exc_info[1]) if record.exc_info[1] else ""
            # Mesajı kısalt ve tek satıra sığdır
            exc_msg_short = exc_msg.replace("\n", " ")[:100]
            parts.append(f"exc_type={exc_type}")
            if exc_msg_short:
                parts.append(f'exc_msg="{exc_msg_short}"')
        
        return " ".join(parts)


# ═══════════════════════════════════════════════════════════════════════════════
# FACTORY FONKSİYONU
# ═══════════════════════════════════════════════════════════════════════════════

def create_formatter(
    format_type: str = "json",
    service_name: Optional[str] = None,
    **kwargs
) -> logging.Formatter:
    """
    Formatter factory fonksiyonu.
    
    Args:
        format_type:  "json", "pretty", veya "compact"
        service_name: Servis adı
        **kwargs:     Formatter'a özel parametreler
    
    Returns:
        logging.Formatter instance
    
    Raises:
        ValueError: Bilinmeyen format tipi
    
    Örnek:
        formatter = create_formatter("json", service_name="api")
        formatter = create_formatter("pretty", use_colors=False)
    """
    formatters = {
        "json": JSONFormatter,
        "pretty": PrettyFormatter,
        "compact": CompactFormatter,
    }
    
    if format_type not in formatters:
        valid = ", ".join(formatters.keys())
        raise ValueError(f"Bilinmeyen format tipi: {format_type}. Geçerli değerler: {valid}")
    
    return formatters[format_type](service_name=service_name, **kwargs)


"""
Bu modül ne yapar?
- JSONFormatter:    Yapılandırılmış JSON (ELK, Datadog, Splunk için)
- PrettyFormatter:  Renkli terminal çıktısı (development için)
- CompactFormatter: Minimal tek satır (log dosyaları için)

Düzeltilen Sorunlar:
1. Timestamp tutarlılığı: Artık record.created kullanılıyor (format anı değil)
2. RESERVED_ATTRS: Tek yerde tanımlandı (DRY)
3. Serialize depth: MAX_SERIALIZE_DEPTH ile recursive protection
4. PrettyFormatter UTC: use_utc parametresi eklendi
5. CompactFormatter exception: exc_type ve exc_msg eklendi
6. JSON hata handling: try-catch ile fallback
7. Ortak fonksiyonlar: get_extra_fields, serialize_value, format_exception_info

Kullanım:
    from formatters import JSONFormatter, PrettyFormatter, create_formatter
    
    # Manuel
    formatter = JSONFormatter(service_name="api", include_location=True)
    
    # Factory ile
    formatter = create_formatter("pretty", use_colors=True)
"""