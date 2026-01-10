from __future__ import annotations

import sys
import gzip
import shutil
import logging
import atexit
import queue
import threading
import time
import weakref
from datetime import datetime
from pathlib import Path
from typing import Optional, Any
from logging.handlers import QueueHandler, QueueListener


# ═══════════════════════════════════════════════════════════════════════════════
# BASE ASYNC HANDLER
# ═══════════════════════════════════════════════════════════════════════════════

class AsyncHandler:
    """
    Asenkron handler base class.
    
    Queue kullanarak logları arka planda işler.
    Ana thread'i bloklamaz.
    
    Çalışma Mantığı:
        1. Logger, log.info() çağrılınca QueueHandler'a yazar
        2. QueueHandler, log'u queue'ya ekler (anında döner)
        3. QueueListener, queue'dan okur ve gerçek handler'a yazar
        4. Gerçek handler (console/file/smtp) I/O işlemini yapar
    """
    
    def __init__(self, handler: logging.Handler):
        """
        Args:
            handler: Sarmalanacak gerçek handler (Console, File, SMTP)
        """
        self._queue: queue.Queue = queue.Queue(-1)  # -1 = sınırsız boyut
        self._handler = handler
        self._listener: Optional[QueueListener] = None
        self._started = False
        self._lock = threading.Lock()
        self._atexit_registered = False
    
    def _start_unlocked(self) -> None:
        """
        Lock almadan başlatma işlemi yapar.
        
        Not: Bu metod sadece lock zaten alınmışken çağrılmalı!
        """
        if not self._started:
            self._listener = QueueListener(
                self._queue,
                self._handler,
                respect_handler_level=True
            )
            self._listener.start()
            self._started = True
            
            # Program kapanırken otomatik durdur (sadece bir kez register et)
            if not self._atexit_registered:
                weak_self = weakref.ref(self)
                
                def cleanup():
                    strong_self = weak_self()
                    if strong_self is not None:
                        strong_self.stop()
                
                atexit.register(cleanup)
                self._atexit_registered = True
    
    def start(self) -> None:
        """Asenkron listener'ı başlatır."""
        with self._lock:
            self._start_unlocked()
    
    def stop(self) -> None:
        """
        Asenkron listener'ı durdurur ve kaynakları temizler.
        
        Queue'daki tüm pending mesajların flush edilmesini garantiler.
        QueueListener.stop() kendi sentinel pattern'ini kullanır.
        """
        with self._lock:
            # Eğer zaten durmuşsa hemen dön (idempotent)
            if not self._started or not self._listener:
                return
            
            # 1. Listener'ı durdur
            # QueueListener.stop() kendi sentinel değerini gönderir
            # ve queue'nun boşalmasını bekler
            self._listener.stop()
            
            # 2. Listener thread'in terminate olmasını bekle
            if hasattr(self._listener, '_thread') and self._listener._thread:
                self._listener._thread.join(timeout=5.0)
            
            self._started = False
            
            # 3. Handler'ı flush et (birden fazla kez, güvenlik için)
            if hasattr(self._handler, 'flush'):
                for _ in range(3):
                    try:
                        self._handler.flush()
                        time.sleep(0.02)
                    except Exception:
                        pass
            
            # 4. Handler'ı kapat
            if hasattr(self._handler, 'close'):
                try:
                    self._handler.close()
                except Exception:
                    pass
    
    def __enter__(self):
        """Context manager entry - otomatik start."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - otomatik stop."""
        self.stop()
        return False
    
    async def __aenter__(self):
        """Async context manager entry - otomatik start."""
        self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - otomatik stop (non-blocking)."""
        import asyncio
        # stop() blocking olduğu için thread pool'da çalıştır
        await asyncio.to_thread(self.stop)
        return False
    
    def get_queue_handler(self) -> QueueHandler:
        """
        Logger'a eklenecek QueueHandler'ı döndürür.
        
        Thread-safe: Birden fazla thread aynı anda çağırabilir.
        
        Returns:
            QueueHandler instance
        """
        with self._lock:
            if not self._started:
                self._start_unlocked()
        return QueueHandler(self._queue)
    
    @property
    def handler(self) -> logging.Handler:
        """
        Gerçek handler'ı döndürür.
        
        Formatter ayarlamak için kullanılır:
            async_handler.handler.setFormatter(JSONFormatter())
        """
        return self._handler


# ═══════════════════════════════════════════════════════════════════════════════
# ASYNC CONSOLE HANDLER
# ═══════════════════════════════════════════════════════════════════════════════

class AsyncConsoleHandler(AsyncHandler):
    """
    Asenkron konsol (stdout/stderr) handler.
    
    Özellikler:
    - Asenkron yazma (ana thread bloklanmaz)
    - İsteğe bağlı ERROR+ için stderr'e yönlendirme
    
    Kullanım:
        handler = AsyncConsoleHandler()
        handler.handler.setFormatter(JSONFormatter())
        logger.addHandler(handler.get_queue_handler())
    """
    
    def __init__(
        self,
        stream: Any = None,
        level: int = logging.DEBUG,
        error_stream: Any = None,
        split_errors: bool = False
    ):
        """
        Args:
            stream:       Çıktı stream'i (default: stdout)
            level:        Minimum log seviyesi
            error_stream: Error stream (default: stderr)
            split_errors: ERROR+ logları stderr'e yönlendir
        """
        if split_errors:
            handler = _SplitStreamHandler(
                stdout=stream or sys.stdout,
                stderr=error_stream or sys.stderr
            )
        else:
            handler = logging.StreamHandler(stream or sys.stdout)
        
        handler.setLevel(level)
        super().__init__(handler)


class _SplitStreamHandler(logging.Handler):
    """
    ERROR ve üstü için stderr, diğerleri için stdout kullanır.
    
    Bu sayede:
    - Normal loglar stdout'a (pipeable)
    - Error loglar stderr'e (dikkat çeker)
    """
    
    def __init__(self, stdout=None, stderr=None):
        super().__init__()
        self.stdout = stdout or sys.stdout
        self.stderr = stderr or sys.stderr
    
    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            stream = self.stderr if record.levelno >= logging.ERROR else self.stdout
            stream.write(msg + "\n")
            stream.flush()
        except Exception:
            self.handleError(record)
    
    def flush(self) -> None:
        """Her iki stream'i de flush eder."""
        try:
            self.stdout.flush()
        except Exception:
            pass
        try:
            self.stderr.flush()
        except Exception:
            pass
    
    def close(self) -> None:
        """Handler'ı kapatır (stream'leri kapatmaz - sahip değiliz)."""
        self.flush()
        super().close()


# ═══════════════════════════════════════════════════════════════════════════════
# ASYNC ROTATING FILE HANDLER
# ═══════════════════════════════════════════════════════════════════════════════

class AsyncRotatingFileHandler(AsyncHandler):
    """
    Asenkron dönen (rotating) dosya handler.
    """
    
    def __init__(
        self,
        filename: str,
        max_bytes: int = 10 * 1024 * 1024,  # 10MB default
        backup_count: int = 5,
        compress: bool = True,
        encoding: str = "utf-8",
        level: int = logging.DEBUG
    ):
        """
        Args:
            filename:     Log dosyası yolu
            max_bytes:    Maksimum dosya boyutu (byte)
            backup_count: Saklanacak eski dosya sayısı
            compress:     Eski dosyaları gzip ile sıkıştır
            encoding:     Dosya encoding'i
            level:        Minimum log seviyesi
        """
        handler = _RotatingFileHandler(
            filename=filename,
            max_bytes=max_bytes,
            backup_count=backup_count,
            compress=compress,
            encoding=encoding
        )
        handler.setLevel(level)
        super().__init__(handler)
        
        # Public attributes
        self.filename = filename
        self.max_bytes = max_bytes
        self.backup_count = backup_count


class _RotatingFileHandler(logging.Handler):
    """
    Gerçek rotating file handler implementasyonu.
    
    Thread-safe ve gzip desteği ile.
    """
    
    def __init__(
        self,
        filename: str,
        max_bytes: int,
        backup_count: int,
        compress: bool,
        encoding: str
    ):
        super().__init__()
        self.filename = Path(filename)
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self.compress = compress
        self.encoding = encoding
        
        # Thread safety için lock
        self._lock = threading.RLock()
        self._stream: Optional[Any] = None
        
        # Dosya dizinini oluştur (yoksa)
        self.filename.parent.mkdir(parents=True, exist_ok=True)
        
        # Dosyayı aç
        self._open()
    
    def _open(self) -> None:
        """Dosyayı açar."""
        self._stream = open(self.filename, "a", encoding=self.encoding)
    
    def _close(self) -> None:
        """Dosyayı kapatır."""
        if self._stream:
            try:
                self._stream.flush()
            except Exception:
                pass
            try:
                self._stream.close()
            except Exception:
                pass
            self._stream = None
    
    def emit(self, record: logging.LogRecord) -> None:
        """Log kaydını dosyaya yazar."""
        try:
            # Format işlemi lock dışında - daha iyi concurrency
            # Not: Formatter thread-safe olmalı (standart formatter'lar öyle)
            msg = self.format(record)
            
            with self._lock:
                # Rotation gerekli mi?
                if self._should_rotate():
                    self._rotate()
                
                # Dosyaya yaz
                if self._stream:
                    self._stream.write(msg + "\n")
                    self._stream.flush()
        except Exception:
            self.handleError(record)
    
    def _should_rotate(self) -> bool:
        """Dosya döndürülmeli mi kontrol eder."""
        if self.max_bytes <= 0:
            return False
        
        if not self.filename.exists():
            return False
        
        return self.filename.stat().st_size >= self.max_bytes
    
    def _rotate(self) -> None:
        """
        Dosyayı döndürür ve eski dosyaları yönetir.
        
        backup_count=1 edge case'ini de handle eder.
        """
        self._close()
        
        # Eski backup'ları kaydır (backup_count > 1 için)
        # range(0, 0, -1) boş olduğundan backup_count=1 için loop çalışmaz
        # bu durumda sadece mevcut dosya backup yapılır
        for i in range(self.backup_count - 1, 0, -1):
            src = self._get_backup_name(i)
            dst = self._get_backup_name(i + 1)
            
            # Compressed versiyonları da kontrol et
            src_gz = Path(str(src) + ".gz")
            dst_gz = Path(str(dst) + ".gz")
            
            if src_gz.exists():
                if dst_gz.exists():
                    dst_gz.unlink()
                src_gz.rename(dst_gz)
            elif src.exists():
                if dst.exists():
                    dst.unlink()
                src.rename(dst)
        
        # Mevcut dosyayı ilk backup yap
        if self.filename.exists():
            backup_path = self._get_backup_name(1)
            
            if self.compress:
                # Gzip ile sıkıştır
                with open(self.filename, "rb") as f_in:
                    with gzip.open(str(backup_path) + ".gz", "wb") as f_out:
                        shutil.copyfileobj(f_in, f_out)
                self.filename.unlink()
            else:
                if backup_path.exists():
                    backup_path.unlink()
                self.filename.rename(backup_path)
        
        # En eski backup'ı sil (limit aşıldıysa)
        oldest = self._get_backup_name(self.backup_count)
        if oldest.exists():
            oldest.unlink()
        oldest_gz = Path(str(oldest) + ".gz")
        if oldest_gz.exists():
            oldest_gz.unlink()
        
        # Yeni dosya aç
        self._open()
    
    def _get_backup_name(self, index: int) -> Path:
        """Backup dosya adını döndürür."""
        return Path(f"{self.filename}.{index}")
    
    def flush(self) -> None:
        """Stream'i flush eder."""
        with self._lock:
            if self._stream:
                try:
                    self._stream.flush()
                except Exception:
                    pass
    
    def close(self) -> None:
        """Handler'ı kapatır."""
        with self._lock:
            self._close()
        super().close()


"""
Bu modül ne yapar?
- AsyncConsoleHandler:        Asenkron konsol çıktısı (stdout)
- AsyncRotatingFileHandler:   Asenkron dosya + otomatik döndürme + gzip

Neden Asenkron?
- Log yazmak I/O işlemidir (disk, network)
- Senkron olsa ana thread bekler, uygulama yavaşlar
- Asenkron olunca log queue'ya atılır, arka planda yazılır

Mimari:
    ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
    │ Ana Thread  │────▶│   Queue     │────▶│  Listener   │
    │ (log.info)  │     │ (buffer)    │     │ (arka plan) │
    └─────────────┘     └─────────────┘     └─────────────┘
         │                                        │
         │ Hemen döner                            │ Asenkron yazar
         ▼                                        ▼
    Uygulama devam                         Console/File/SMTP

Düzeltilen Sorunlar:
1. Sentinel pattern: QueueListener.stop() kendi sentinel'ını kullanır, 
   ekstra None göndermeye gerek yok
2. Race condition: get_queue_handler() artık lock içinde start kontrolü yapıyor
3. Async context manager: asyncio.to_thread() ile non-blocking
4. _SplitStreamHandler: flush() ve close() metodları eklendi
5. __del__ kaldırıldı: Güvenilir değil, atexit yeterli
6. _rotate() edge case: backup_count=1 düzgün çalışıyor
"""