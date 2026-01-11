from __future__ import annotations

import uuid
import threading
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Dict, Any


# Yardımcı fonksiyonlar
def _generate_id() -> str:
    """Benzersiz 16 haneli hex kodu üretir"""
    return uuid.uuid4().hex[:16]


def _now_iso() -> str:
    """ISO 8601 formatında UTC timestamp döndürür"""
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


# Trace Context Sınıfı
@dataclass
class TraceContext:
    # Trace ID
    trace_id: str = field(default_factory=_generate_id)

    # Span ID
    span_id: str = field(default_factory=_generate_id)

    # Parent Span ID
    parent_span_id: Optional[str] = None

    # Correlation ID
    correlation_id: Optional[str] = None

    # Session ID
    session_id: Optional[str] = None

    # Başlangıç Zamanı
    started_at: str = field(default_factory=_now_iso)

    # Ek Alanlar
    extra: Dict[str, Any] = field(default_factory=dict)

    def child_span(self) -> TraceContext:
        """
        Bu context üzerine yeni bir child span oluşturur
        """
        return TraceContext(
            trace_id=self.trace_id,
            span_id=_generate_id(),
            parent_span_id=self.span_id,
            correlation_id=self.correlation_id,
            session_id=self.session_id,
            extra=self.extra.copy(),
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Context'i dict olarak döndürür
        """
        response: Dict[str, Any] = {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "started_at": self.started_at,
        }

        if self.parent_span_id:
            response["parent_span_id"] = self.parent_span_id
        if self.correlation_id:
            response["correlation_id"] = self.correlation_id
        if self.session_id:
            response["session_id"] = self.session_id

        response.update(self.extra)
        return response

    def to_headers(self) -> Dict[str, str]:
        """
        Context'i HTTP Header'ları olarak döndürür
        """
        headers = {
            "X-Trace-Id": self.trace_id,
            "X-Span-Id": self.span_id,
        }

        if self.parent_span_id:
            headers["X-Parent-Span-Id"] = self.parent_span_id
        if self.correlation_id:
            headers["X-Correlation-Id"] = self.correlation_id
        if self.session_id:
            headers["X-Session-Id"] = self.session_id

        return headers

    @classmethod
    def from_headers(cls, headers: Dict[str, str]) -> TraceContext:
        """
        Header'lardan otomatik trace context oluşturur
        """
        # Case-insensitive header lookup
        normalized = {k.lower(): v for k, v in headers.items()}

        return cls(
            trace_id=normalized.get("x-trace-id", _generate_id()),
            span_id=_generate_id(),
            parent_span_id=normalized.get("x-span-id"),
            correlation_id=normalized.get("x-correlation-id"),
            session_id=normalized.get("x-session-id"),
        )


# Context Storage
_context_var: ContextVar[Optional[TraceContext]] = ContextVar(
    "trace_context", default=None
)
"""
Thread üzerinde memory yönetimi için. Thread hafızasına ilgili Trace Context'i depolar.
Thread üzerinde çalışan tüm servisler ilgili Trace Context bilgisine erişebilir.
"""

_thread_local = threading.local()
"""
Yukarıdaki sistemin fallback mekanizması.
Çalışmadığı veya desteklenmediği durumlarda devreye girer.
"""


def get_current_context() -> Optional[TraceContext]:
    """
    Aktif Trace Context değerini döndürür
    """
    try:
        context = _context_var.get()
        if context is not None:
            return context

        # Fallback
        return getattr(_thread_local, "context", None)

    except LookupError as e:
        raise RuntimeError(f"Trace Context variable is not reachable: {e}")


def set_current_context(ctx: Optional[TraceContext]) -> None:
    """
    Aktif Trace Context değerini ayarlar
    """
    try:
        _context_var.set(ctx)
        _thread_local.context = ctx
    except Exception as e:
        raise RuntimeError(f"Trace Context could not be configured: {e}")


def clear_current_context() -> None:
    """
    Aktif Trace Context değerini temizler
    """
    set_current_context(None)


# With bloğu için / context manager
class trace:
    """
    Trace context manager - sync ve async kullanım destekler.

    Kullanım:
        with trace(correlation_id="req-123") as ctx:
            # ctx.trace_id, ctx.span_id vb. erişilebilir
            do_work()

        async with trace(headers=request.headers) as ctx:
            await do_async_work()
    """

    def __init__(
        self,
        trace_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        session_id: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        parent: Optional[TraceContext] = None,
        **extra: Any,
    ):
        self.previous_context: Optional[TraceContext] = None
        self.context: TraceContext

        if headers:
            self.context = TraceContext.from_headers(headers)

        elif parent:
            self.context = parent.child_span()

        else:
            self.context = TraceContext(
                trace_id=trace_id or _generate_id(),
                correlation_id=correlation_id,
                session_id=session_id,
                extra=extra,
            )

    def __enter__(self) -> TraceContext:
        """
        Context Manager giriş noktası
        """
        self.previous_context = get_current_context()
        set_current_context(self.context)
        return self.context

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """
        Context Manager çıkış noktası
        """
        set_current_context(self.previous_context)

    async def __aenter__(self) -> TraceContext:
        """
        Asenkron Context Manager giriş noktası
        """
        return self.__enter__()

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """
        Asenkron Context Manager çıkış noktası
        """
        self.__exit__(exc_type, exc_val, exc_tb)


def create_trace(**kwargs: Any) -> TraceContext:
    """
    Yeni bir TraceContext oluşturur
    """
    return TraceContext(**kwargs)