"""
Trace, Correlation ve Session ile Loglama Middleware'i

Çalışma sırası:
1. Middleware trace context'i başlatır (correlation_id header'dan alır veya oluşturur)
2. authenticate_user dependency çalıştığında trace context'e session_id eklenir
3. Middleware response'a trace bilgilerini eklerken güncel context'i kullanır
"""

import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from qbitra.core.logger.context import trace, get_current_context
from qbitra.core.qbitra_logger import get_logger, get_access_logger

# API katmanı genel istek/cevap logger'ı
logger = get_logger("logging_middleware", parent_folder="api")
# Sade access log (method, path, status_code, trace/correlation) için logger
access_logger = get_access_logger()


def _generate_correlation_id() -> str:
    """Benzersiz correlation ID oluşturur."""
    return f"corr-{uuid.uuid4().hex[:16]}"


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Basit ve sade logging middleware.
    
    Özellikler:
    - Her request için trace context oluşturur
    - Correlation ID: Header'dan alır, yoksa unique ID oluşturur
    - Session ID: authenticate_user dependency çalıştığında trace context'e eklenir
    - Request/response loglarını yazar
    - Response header'larına trace bilgilerini ekler
    """
    
    def __init__(self, app: ASGIApp, log_requests: bool = True):
        super().__init__(app)
        self.log_requests = log_requests
    
    def _extract_correlation_id(self, headers: dict) -> str:
        """
        Correlation ID'yi çıkarır veya oluşturur.
        
        Header'da varsa onu kullanır, yoksa unique ID oluşturur.
        """
        correlation_id = headers.get("x-correlation-id")
        if correlation_id:
            return correlation_id
        
        # Header'da yoksa unique ID oluştur
        return _generate_correlation_id()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Request'i işler ve loglar.
        
        Args:
            request: FastAPI Request objesi
            call_next: Sonraki middleware/handler fonksiyonu
        
        Returns:
            Response objesi
        """
        # Header'ları dict olarak al (case-insensitive için normalize et)
        headers = {k.lower(): v for k, v in request.headers.items()}
        
        # Correlation ID: Header'dan al veya oluştur
        correlation_id = self._extract_correlation_id(headers)
        
        # Session ID: Header'dan al (varsa)
        # Not: authenticate_user dependency çalıştığında trace context güncellenecek
        session_id = headers.get("x-session-id")
        
        # Trace context oluştur
        with trace(
            correlation_id=correlation_id,
            session_id=session_id,
            headers=dict(request.headers),  # Original headers for TraceContext.from_headers
        ) as ctx:
            # Request başlangıç zamanı
            start_time = time.time()
            
            # Request logu
            if self.log_requests:
                logger.info(
                    "Request başladı",
                    extra={
                        "method": request.method,
                        "path": request.url.path,
                        "query": str(request.url.query) if request.url.query else None,
                        "client": request.client.host if request.client else None,
                        "correlation_id": correlation_id,
                        "session_id": session_id,
                    },
                )
            
            # Request'i işle
            # authenticate_user dependency burada çalışacak ve trace context'i güncelleyecek
            try:
                response = await call_next(request)
                
                # İşlem süresi
                process_time = time.time() - start_time
                
                # Güncel trace context'i al (authenticate_user sonrası güncellenmiş olabilir)
                current_ctx = get_current_context()
                if current_ctx:
                    # Response header'larına trace bilgilerini ekle
                    for key, value in current_ctx.to_headers().items():
                        response.headers[key] = value
                    
                    # Response logu
                    if self.log_requests:
                        logger.info(
                            "Request tamamlandı",
                            extra={
                                "method": request.method,
                                "path": request.url.path,
                                "status_code": response.status_code,
                                "process_time": f"{process_time:.3f}s",
                                "correlation_id": current_ctx.correlation_id,
                                "session_id": current_ctx.session_id,
                                "trace_id": current_ctx.trace_id,
                            },
                        )
                    
                    # Sade access log (her istek için tek satır)
                    access_logger.info(
                        "access",
                        extra={
                            "method": request.method,
                            "path": request.url.path,
                            "status_code": response.status_code,
                            "trace_id": current_ctx.trace_id,
                            "correlation_id": current_ctx.correlation_id,
                        },
                    )
                else:
                    # Context yoksa (çok nadir durum) başlangıç context'ini kullan
                    for key, value in ctx.to_headers().items():
                        response.headers[key] = value
                    
                    if self.log_requests:
                        logger.info(
                            "Request tamamlandı",
                            extra={
                                "method": request.method,
                                "path": request.url.path,
                                "status_code": response.status_code,
                                "process_time": f"{process_time:.3f}s",
                                "correlation_id": ctx.correlation_id,
                                "session_id": ctx.session_id,
                                "trace_id": ctx.trace_id,
                            },
                        )
                    
                    # Sade access log (context fallback ile)
                    access_logger.info(
                        "access",
                        extra={
                            "method": request.method,
                            "path": request.url.path,
                            "status_code": response.status_code,
                            "trace_id": ctx.trace_id,
                            "correlation_id": ctx.correlation_id,
                        },
                    )
                
                return response
            
            except Exception as e:
                # Hata durumu
                process_time = time.time() - start_time
                
                # Güncel trace context'i al
                current_ctx = get_current_context() or ctx
                
                logger.error(
                    "Request hatası",
                    extra={
                        "method": request.method,
                        "path": request.url.path,
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "process_time": f"{process_time:.3f}s",
                        "correlation_id": current_ctx.correlation_id,
                        "session_id": current_ctx.session_id,
                    },
                    exc_info=True,
                )
                
                raise
