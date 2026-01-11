import re
import time
import threading
from typing import Optional, Dict, List, Any, Callable
from functools import wraps

from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    Summary,
    CollectorRegistry,
    push_to_gateway,
    generate_latest,
    CONTENT_TYPE_LATEST,
    start_http_server
)

from qbitra.core.qbitra_logger import get_logger
from qbitra.core.exceptions import (
    PrometheusError,
    PrometheusClientError,
    PrometheusMetricError,
)
from .configuration_handler import ConfigurationHandler


class PrometheusClient:
    """Prometheus client for managing metrics across different services."""

    _registry: CollectorRegistry = None
    _initialized: bool = False
    _logger = get_logger("prometheus")
    _lock = threading.RLock()

    # Configuration
    _namespace: str = None
    _push_gateway_url: str = None
    _job_name: str = None
    _metrics_port: int = None

    # Metric storage
    _counters: Dict[str, Counter] = {}
    _gauges: Dict[str, Gauge] = {}
    _histograms: Dict[str, Histogram] = {}
    _summaries: Dict[str, Summary] = {}

    # Default histogram buckets
    DEFAULT_BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0)

    @classmethod
    def _load_configuration(cls):
        """Load Prometheus configuration from configuration handler."""
        ConfigurationHandler.ensure_loaded()

        cls._namespace = ConfigurationHandler.get_value_as_str(
            "Prometheus", "namespace", fallback="qbitra"
        )
        cls._push_gateway_url = ConfigurationHandler.get_value_as_str(
            "Prometheus", "push_gateway_url", fallback=None
        )
        cls._job_name = ConfigurationHandler.get_value_as_str(
            "Prometheus", "job_name", fallback="qbitra_service"
        )
        cls._metrics_port = ConfigurationHandler.get_value_as_int(
            "Prometheus", "metrics_port", fallback=9090
        )

        cls._logger.debug(
            "Prometheus configuration yüklendi",
            extra={
                "namespace": cls._namespace,
                "job_name": cls._job_name,
                "metrics_port": cls._metrics_port,
                "push_gateway_url": cls._push_gateway_url
            }
        )

    @classmethod
    def _validate_metric_name(cls, name: str) -> bool:
        """Validate metric name according to Prometheus conventions."""
        # Prometheus metric names: [a-zA-Z_:][a-zA-Z0-9_:]*
        pattern = r'^[a-zA-Z_:][a-zA-Z0-9_:]*$'
        return bool(re.match(pattern, name))

    @classmethod
    def _validate_label_name(cls, name: str) -> bool:
        """Validate label name according to Prometheus conventions."""
        # Label names: [a-zA-Z_][a-zA-Z0-9_]*
        pattern = r'^[a-zA-Z_][a-zA-Z0-9_]*$'
        return bool(re.match(pattern, name))

    @classmethod
    def load(cls):
        """Load Prometheus client and create registry."""
        if cls._initialized:
            cls._logger.info("Prometheus client daha önce başlatılmış, tekrar başlatılamaz")
            return

        try:
            cls._load_configuration()
            
            with cls._lock:
                cls._registry = CollectorRegistry()

                # Reset metric storage
                cls._counters = {}
                cls._gauges = {}
                cls._histograms = {}
                cls._summaries = {}

            cls._logger.debug(
                "Prometheus client başarıyla yüklendi",
                extra={
                    "namespace": cls._namespace,
                    "job_name": cls._job_name,
                    "initialized": True
                }
            )
            cls._initialized = True
        except Exception as e:
            cls._logger.error(
                f"Prometheus client başlatılırken hata oluştu: {e}",
                extra={"error": str(e), "error_type": type(e).__name__},
                exc_info=True
            )
            raise PrometheusClientError(
                operation="initialization",
                message=f"Prometheus client başlatılamadı: {e}",
                cause=e
            ) from e

    @classmethod
    def test(cls) -> tuple[bool, Optional[str]]:
        """Test Prometheus client by checking registry status."""
        if not cls._initialized:
            cls._logger.error("Test işlemi yapılmadan önce Prometheus client başlatılmalıdır")
            cls._logger.debug("Prometheus client başlatılıyor...")
            cls.load()

        is_valid = all([
            cls._registry is not None,
            cls._namespace is not None
        ])

        cls._logger.debug(
            f"Prometheus test - Registry: {'initialized' if cls._registry else 'missing'}, "
            f"Namespace: {cls._namespace}",
            extra={
                "registry_initialized": cls._registry is not None,
                "namespace": cls._namespace,
                "is_valid": is_valid
            }
        )

        return is_valid, cls._namespace if is_valid else None

    @classmethod
    def init(cls) -> bool:
        """Initialize Prometheus client with validation test."""
        if cls._initialized:
            cls._logger.info("Prometheus client daha önce başlatılmış, tekrar başlatılamaz")
            return True

        cls.load()

        success, namespace = cls.test()
        if not success:
            cls._logger.error(
                "Prometheus client test başarısız",
                extra={"namespace": cls._namespace}
            )
            raise PrometheusClientError(
                operation="test",
                message="Prometheus client test başarısız. Konfigürasyonu kontrol ediniz."
            )

        cls._logger.info(
            f"Prometheus client başarıyla başlatıldı (namespace: {namespace})",
            extra={
                "namespace": namespace,
                "job_name": cls._job_name,
                "initialized": True
            }
        )
        return cls._initialized

    @classmethod
    def is_initialized(cls) -> bool:
        """Check if Prometheus client is initialized."""
        return cls._initialized

    @classmethod
    def _ensure_initialized(cls):
        """Ensure client is initialized before operations."""
        if not cls._initialized:
            cls._logger.error("Prometheus client başlatılmadan işlem yapılamaz")
            raise PrometheusClientError(
                operation="operation",
                message="Prometheus client başlatılmadan metrik işlemi yapılamaz"
            )

    @classmethod
    def _build_metric_name(cls, service: str, name: str) -> str:
        """Build full metric name with namespace and service prefix."""
        return f"{cls._namespace}_{service}_{name}"

    @classmethod
    def _get_full_name(cls, service: str, name: str) -> str:
        """Get the full metric name for lookup."""
        return cls._build_metric_name(service, name)

    # =========================================================================
    # COUNTER OPERATIONS
    # =========================================================================

    @classmethod
    def create_counter(
        cls,
        service: str,
        name: str,
        description: str,
        labels: Optional[List[str]] = None
    ) -> Counter:
        """Create a new counter metric."""
        cls._ensure_initialized()

        full_name = cls._get_full_name(service, name)

        # Validate metric name
        if not cls._validate_metric_name(full_name):
            raise PrometheusMetricError(
                metric_name=full_name,
                metric_type="counter",
                operation="create",
                message=f"Invalid metric name: {full_name}"
            )

        # Validate label names
        if labels:
            for label in labels:
                if not cls._validate_label_name(label):
                    raise PrometheusMetricError(
                        metric_name=full_name,
                        metric_type="counter",
                        operation="create",
                        message=f"Invalid label name: {label}"
                    )

        with cls._lock:
            if full_name in cls._counters:
                cls._logger.debug(
                    f"Counter zaten mevcut, mevcut döndürülüyor: {full_name}",
                    extra={"metric_name": full_name, "service": service}
                )
                return cls._counters[full_name]

            try:
                counter = Counter(
                    full_name,
                    description,
                    labelnames=labels or [],
                    registry=cls._registry
                )
                cls._counters[full_name] = counter
                cls._logger.debug(
                    f"Counter oluşturuldu: {full_name}",
                    extra={
                        "metric_name": full_name,
                        "service": service,
                        "description": description,
                        "labels": labels
                    }
                )
                return counter
            except Exception as e:
                cls._logger.error(
                    f"Counter oluşturulamadı: {full_name}",
                    extra={
                        "metric_name": full_name,
                        "service": service,
                        "error": str(e),
                        "error_type": type(e).__name__
                    },
                    exc_info=True
                )
                raise PrometheusMetricError(
                    metric_name=full_name,
                    metric_type="counter",
                    operation="create",
                    message=f"Counter oluşturulamadı: {e}",
                    cause=e
                ) from e

    @classmethod
    def increment_counter(
        cls,
        service: str,
        name: str,
        value: float = 1,
        labels: Optional[Dict[str, str]] = None
    ):
        """Increment a counter by the given value."""
        cls._ensure_initialized()

        full_name = cls._get_full_name(service, name)

        if full_name not in cls._counters:
            cls._logger.error(
                f"Counter bulunamadı: {full_name}",
                extra={
                    "metric_name": full_name,
                    "service": service,
                    "available_counters": list(cls._counters.keys())
                }
            )
            raise PrometheusMetricError(
                metric_name=full_name,
                metric_type="counter",
                operation="increment",
                message=f"Counter bulunamadı: {full_name}"
            )

        try:
            counter = cls._counters[full_name]
            if labels:
                counter.labels(**labels).inc(value)
            else:
                counter.inc(value)
            cls._logger.debug(
                f"Counter artırıldı: {full_name}",
                extra={
                    "metric_name": full_name,
                    "service": service,
                    "value": value,
                    "labels": labels
                }
            )
        except Exception as e:
            cls._logger.error(
                f"Counter artırılamadı: {full_name}",
                extra={
                    "metric_name": full_name,
                    "service": service,
                    "value": value,
                    "labels": labels,
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            raise PrometheusMetricError(
                metric_name=full_name,
                metric_type="counter",
                operation="increment",
                message=f"Counter artırılamadı: {e}",
                cause=e
            ) from e

    # =========================================================================
    # GAUGE OPERATIONS
    # =========================================================================

    @classmethod
    def create_gauge(
        cls,
        service: str,
        name: str,
        description: str,
        labels: Optional[List[str]] = None
    ) -> Gauge:
        """Create a new gauge metric."""
        cls._ensure_initialized()

        full_name = cls._get_full_name(service, name)

        # Validate metric name
        if not cls._validate_metric_name(full_name):
            raise PrometheusMetricError(
                metric_name=full_name,
                metric_type="gauge",
                operation="create",
                message=f"Invalid metric name: {full_name}"
            )

        with cls._lock:
            if full_name in cls._gauges:
                cls._logger.debug(
                    f"Gauge zaten mevcut, mevcut döndürülüyor: {full_name}",
                    extra={"metric_name": full_name, "service": service}
                )
                return cls._gauges[full_name]

            try:
                gauge = Gauge(
                    full_name,
                    description,
                    labelnames=labels or [],
                    registry=cls._registry
                )
                cls._gauges[full_name] = gauge
                cls._logger.debug(
                    f"Gauge oluşturuldu: {full_name}",
                    extra={
                        "metric_name": full_name,
                        "service": service,
                        "description": description,
                        "labels": labels
                    }
                )
                return gauge
            except Exception as e:
                cls._logger.error(
                    f"Gauge oluşturulamadı: {full_name}",
                    extra={
                        "metric_name": full_name,
                        "service": service,
                        "error": str(e),
                        "error_type": type(e).__name__
                    },
                    exc_info=True
                )
                raise PrometheusMetricError(
                    metric_name=full_name,
                    metric_type="gauge",
                    operation="create",
                    message=f"Gauge oluşturulamadı: {e}",
                    cause=e
                ) from e

    @classmethod
    def set_gauge(
        cls,
        service: str,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None
    ):
        """Set a gauge to the given value."""
        cls._ensure_initialized()

        full_name = cls._get_full_name(service, name)

        if full_name not in cls._gauges:
            raise PrometheusMetricError(
                metric_name=full_name,
                metric_type="gauge",
                operation="set",
                message=f"Gauge bulunamadı: {full_name}"
            )

        try:
            gauge = cls._gauges[full_name]
            if labels:
                gauge.labels(**labels).set(value)
            else:
                gauge.set(value)
            cls._logger.debug(
                f"Gauge ayarlandı: {full_name} = {value}",
                extra={
                    "metric_name": full_name,
                    "service": service,
                    "value": value,
                    "labels": labels
                }
            )
        except Exception as e:
            cls._logger.error(
                f"Gauge ayarlanamadı: {full_name}",
                extra={
                    "metric_name": full_name,
                    "service": service,
                    "value": value,
                    "error": str(e)
                },
                exc_info=True
            )
            raise PrometheusMetricError(
                metric_name=full_name,
                metric_type="gauge",
                operation="set",
                message=f"Gauge ayarlanamadı: {e}",
                cause=e
            ) from e

    @classmethod
    def increment_gauge(
        cls,
        service: str,
        name: str,
        value: float = 1,
        labels: Optional[Dict[str, str]] = None
    ):
        """Increment a gauge by the given value."""
        cls._ensure_initialized()

        full_name = cls._get_full_name(service, name)

        if full_name not in cls._gauges:
            raise PrometheusMetricError(
                metric_name=full_name,
                metric_type="gauge",
                operation="increment",
                message=f"Gauge bulunamadı: {full_name}"
            )

        try:
            gauge = cls._gauges[full_name]
            if labels:
                gauge.labels(**labels).inc(value)
            else:
                gauge.inc(value)
            cls._logger.debug(
                f"Gauge artırıldı: {full_name} (+{value})",
                extra={"metric_name": full_name, "service": service, "value": value}
            )
        except Exception as e:
            cls._logger.error(
                f"Gauge artırılamadı: {full_name}",
                extra={"metric_name": full_name, "error": str(e)},
                exc_info=True
            )
            raise PrometheusMetricError(
                metric_name=full_name,
                metric_type="gauge",
                operation="increment",
                message=f"Gauge artırılamadı: {e}",
                cause=e
            ) from e

    @classmethod
    def decrement_gauge(
        cls,
        service: str,
        name: str,
        value: float = 1,
        labels: Optional[Dict[str, str]] = None
    ):
        """Decrement a gauge by the given value."""
        cls._ensure_initialized()

        full_name = cls._get_full_name(service, name)

        if full_name not in cls._gauges:
            raise PrometheusMetricError(
                metric_name=full_name,
                metric_type="gauge",
                operation="decrement",
                message=f"Gauge bulunamadı: {full_name}"
            )

        try:
            gauge = cls._gauges[full_name]
            if labels:
                gauge.labels(**labels).dec(value)
            else:
                gauge.dec(value)
            cls._logger.debug(
                f"Gauge azaltıldı: {full_name} (-{value})",
                extra={"metric_name": full_name, "service": service, "value": value}
            )
        except Exception as e:
            cls._logger.error(
                f"Gauge azaltılamadı: {full_name}",
                extra={"metric_name": full_name, "error": str(e)},
                exc_info=True
            )
            raise PrometheusMetricError(
                metric_name=full_name,
                metric_type="gauge",
                operation="decrement",
                message=f"Gauge azaltılamadı: {e}",
                cause=e
            ) from e

    # =========================================================================
    # HISTOGRAM OPERATIONS
    # =========================================================================

    @classmethod
    def create_histogram(
        cls,
        service: str,
        name: str,
        description: str,
        labels: Optional[List[str]] = None,
        buckets: Optional[tuple] = None
    ) -> Histogram:
        """Create a new histogram metric."""
        cls._ensure_initialized()

        full_name = cls._get_full_name(service, name)

        # Validate metric name
        if not cls._validate_metric_name(full_name):
            raise PrometheusMetricError(
                metric_name=full_name,
                metric_type="histogram",
                operation="create",
                message=f"Invalid metric name: {full_name}"
            )

        with cls._lock:
            if full_name in cls._histograms:
                cls._logger.debug(
                    f"Histogram zaten mevcut, mevcut döndürülüyor: {full_name}",
                    extra={"metric_name": full_name, "service": service}
                )
                return cls._histograms[full_name]

            try:
                histogram = Histogram(
                    full_name,
                    description,
                    labelnames=labels or [],
                    buckets=buckets or cls.DEFAULT_BUCKETS,
                    registry=cls._registry
                )
                cls._histograms[full_name] = histogram
                cls._logger.debug(
                    f"Histogram oluşturuldu: {full_name}",
                    extra={
                        "metric_name": full_name,
                        "service": service,
                        "description": description,
                        "labels": labels,
                        "buckets": buckets or cls.DEFAULT_BUCKETS
                    }
                )
                return histogram
            except Exception as e:
                cls._logger.error(
                    f"Histogram oluşturulamadı: {full_name}",
                    extra={
                        "metric_name": full_name,
                        "service": service,
                        "error": str(e)
                    },
                    exc_info=True
                )
                raise PrometheusMetricError(
                    metric_name=full_name,
                    metric_type="histogram",
                    operation="create",
                    message=f"Histogram oluşturulamadı: {e}",
                    cause=e
                ) from e

    @classmethod
    def observe_histogram(
        cls,
        service: str,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None
    ):
        """Observe a value in a histogram."""
        cls._ensure_initialized()

        full_name = cls._get_full_name(service, name)

        if full_name not in cls._histograms:
            raise PrometheusMetricError(
                metric_name=full_name,
                metric_type="histogram",
                operation="observe",
                message=f"Histogram bulunamadı: {full_name}"
            )

        try:
            histogram = cls._histograms[full_name]
            if labels:
                histogram.labels(**labels).observe(value)
            else:
                histogram.observe(value)
            cls._logger.debug(
                f"Histogram gözlemlendi: {full_name} = {value}",
                extra={"metric_name": full_name, "service": service, "value": value}
            )
        except Exception as e:
            cls._logger.error(
                f"Histogram gözlemlenemedi: {full_name}",
                extra={"metric_name": full_name, "error": str(e)},
                exc_info=True
            )
            raise PrometheusMetricError(
                metric_name=full_name,
                metric_type="histogram",
                operation="observe",
                message=f"Histogram gözlemlenemedi: {e}",
                cause=e
            ) from e

    # =========================================================================
    # SUMMARY OPERATIONS
    # =========================================================================

    @classmethod
    def create_summary(
        cls,
        service: str,
        name: str,
        description: str,
        labels: Optional[List[str]] = None
    ) -> Summary:
        """Create a new summary metric."""
        cls._ensure_initialized()

        full_name = cls._get_full_name(service, name)

        # Validate metric name
        if not cls._validate_metric_name(full_name):
            raise PrometheusMetricError(
                metric_name=full_name,
                metric_type="summary",
                operation="create",
                message=f"Invalid metric name: {full_name}"
            )

        with cls._lock:
            if full_name in cls._summaries:
                cls._logger.debug(
                    f"Summary zaten mevcut, mevcut döndürülüyor: {full_name}",
                    extra={"metric_name": full_name, "service": service}
                )
                return cls._summaries[full_name]

            try:
                summary = Summary(
                    full_name,
                    description,
                    labelnames=labels or [],
                    registry=cls._registry
                )
                cls._summaries[full_name] = summary
                cls._logger.debug(
                    f"Summary oluşturuldu: {full_name}",
                    extra={
                        "metric_name": full_name,
                        "service": service,
                        "description": description,
                        "labels": labels
                    }
                )
                return summary
            except Exception as e:
                cls._logger.error(
                    f"Summary oluşturulamadı: {full_name}",
                    extra={"metric_name": full_name, "error": str(e)},
                    exc_info=True
                )
                raise PrometheusMetricError(
                    metric_name=full_name,
                    metric_type="summary",
                    operation="create",
                    message=f"Summary oluşturulamadı: {e}",
                    cause=e
                ) from e

    @classmethod
    def observe_summary(
        cls,
        service: str,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None
    ):
        """Observe a value in a summary."""
        cls._ensure_initialized()

        full_name = cls._get_full_name(service, name)

        if full_name not in cls._summaries:
            raise PrometheusMetricError(
                metric_name=full_name,
                metric_type="summary",
                operation="observe",
                message=f"Summary bulunamadı: {full_name}"
            )

        try:
            summary = cls._summaries[full_name]
            if labels:
                summary.labels(**labels).observe(value)
            else:
                summary.observe(value)
            cls._logger.debug(
                f"Summary gözlemlendi: {full_name} = {value}",
                extra={"metric_name": full_name, "service": service, "value": value}
            )
        except Exception as e:
            cls._logger.error(
                f"Summary gözlemlenemedi: {full_name}",
                extra={"metric_name": full_name, "error": str(e)},
                exc_info=True
            )
            raise PrometheusMetricError(
                metric_name=full_name,
                metric_type="summary",
                operation="observe",
                message=f"Summary gözlemlenemedi: {e}",
                cause=e
            ) from e

    # =========================================================================
    # DECORATORS
    # =========================================================================

    @classmethod
    def track_time(
        cls,
        service: str,
        name: str,
        labels: Optional[Dict[str, str]] = None
    ) -> Callable:
        """Decorator to track function execution time in a histogram."""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = time.perf_counter()
                try:
                    return func(*args, **kwargs)
                finally:
                    elapsed = time.perf_counter() - start_time
                    try:
                        cls.observe_histogram(service, name, elapsed, labels)
                    except PrometheusMetricError:
                        cls._logger.warning(
                            f"Histogram bulunamadı, süre kaydedilemedi: {service}_{name}",
                            extra={"service": service, "metric_name": name}
                        )

            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.perf_counter()
                try:
                    return await func(*args, **kwargs)
                finally:
                    elapsed = time.perf_counter() - start_time
                    try:
                        cls.observe_histogram(service, name, elapsed, labels)
                    except PrometheusMetricError:
                        cls._logger.warning(
                            f"Histogram bulunamadı, süre kaydedilemedi: {service}_{name}",
                            extra={"service": service, "metric_name": name}
                        )

            import asyncio
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            return sync_wrapper
        return decorator

    @classmethod
    def track_in_progress(
        cls,
        service: str,
        name: str,
        labels: Optional[Dict[str, str]] = None
    ) -> Callable:
        """Decorator to track in-progress function calls with a gauge."""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                try:
                    cls.increment_gauge(service, name, 1, labels)
                except PrometheusMetricError:
                    cls._logger.warning(
                        f"Gauge bulunamadı: {service}_{name}",
                        extra={"service": service, "metric_name": name}
                    )
                try:
                    return func(*args, **kwargs)
                finally:
                    try:
                        cls.decrement_gauge(service, name, 1, labels)
                    except PrometheusMetricError:
                        pass

            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                try:
                    cls.increment_gauge(service, name, 1, labels)
                except PrometheusMetricError:
                    cls._logger.warning(
                        f"Gauge bulunamadı: {service}_{name}",
                        extra={"service": service, "metric_name": name}
                    )
                try:
                    return await func(*args, **kwargs)
                finally:
                    try:
                        cls.decrement_gauge(service, name, 1, labels)
                    except PrometheusMetricError:
                        pass

            import asyncio
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            return sync_wrapper
        return decorator

    @classmethod
    def count_calls(
        cls,
        service: str,
        name: str,
        labels: Optional[Dict[str, str]] = None
    ) -> Callable:
        """Decorator to count function calls."""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                try:
                    cls.increment_counter(service, name, 1, labels)
                except PrometheusMetricError:
                    cls._logger.warning(
                        f"Counter bulunamadı: {service}_{name}",
                        extra={"service": service, "metric_name": name}
                    )
                return func(*args, **kwargs)

            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                try:
                    cls.increment_counter(service, name, 1, labels)
                except PrometheusMetricError:
                    cls._logger.warning(
                        f"Counter bulunamadı: {service}_{name}",
                        extra={"service": service, "metric_name": name}
                    )
                return await func(*args, **kwargs)

            import asyncio
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            return sync_wrapper
        return decorator

    # =========================================================================
    # CONTEXT MANAGER
    # =========================================================================

    @classmethod
    def timer(
        cls,
        service: str,
        name: str,
        labels: Optional[Dict[str, str]] = None
    ):
        """Context manager for tracking execution time."""
        return _MetricTimer(cls, service, name, labels)

    # =========================================================================
    # SERVICE HELPER - BULK METRIC CREATION
    # =========================================================================

    @classmethod
    def register_service_metrics(
        cls,
        service: str,
        metrics_config: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Register multiple metrics for a service at once.
        
        Example config:
        {
            "request_count": {
                "type": "counter",
                "description": "Total request count",
                "labels": ["endpoint", "method", "status"]
            },
            "active_connections": {
                "type": "gauge",
                "description": "Current active connections"
            },
            "request_duration": {
                "type": "histogram",
                "description": "Request duration in seconds",
                "labels": ["endpoint"],
                "buckets": (0.1, 0.5, 1.0, 2.0, 5.0)
            }
        }
        """
        cls._ensure_initialized()

        created_metrics = {}

        for metric_name, config in metrics_config.items():
            metric_type = config.get("type", "counter")
            description = config.get("description", f"{service} {metric_name}")
            labels = config.get("labels")

            try:
                if metric_type == "counter":
                    created_metrics[metric_name] = cls.create_counter(
                        service, metric_name, description, labels
                    )
                elif metric_type == "gauge":
                    created_metrics[metric_name] = cls.create_gauge(
                        service, metric_name, description, labels
                    )
                elif metric_type == "histogram":
                    buckets = config.get("buckets")
                    created_metrics[metric_name] = cls.create_histogram(
                        service, metric_name, description, labels, buckets
                    )
                elif metric_type == "summary":
                    created_metrics[metric_name] = cls.create_summary(
                        service, metric_name, description, labels
                    )
                else:
                    cls._logger.warning(
                        f"Bilinmeyen metrik tipi: {metric_type}",
                        extra={"metric_type": metric_type, "metric_name": metric_name}
                    )
            except Exception as e:
                cls._logger.error(
                    f"Metrik oluşturulamadı: {service}_{metric_name}",
                    extra={"service": service, "metric_name": metric_name, "error": str(e)},
                    exc_info=True
                )

        cls._logger.info(
            f"Servis metrikleri oluşturuldu: {service}",
            extra={
                "service": service,
                "created_count": len(created_metrics),
                "requested_count": len(metrics_config)
            }
        )
        return created_metrics

    # =========================================================================
    # EXPORT & PUSH
    # =========================================================================

    @classmethod
    def get_metrics(cls) -> bytes:
        """Get all metrics in Prometheus format."""
        cls._ensure_initialized()
        return generate_latest(cls._registry)

    @classmethod
    def get_content_type(cls) -> str:
        """Get the content type for Prometheus metrics."""
        return CONTENT_TYPE_LATEST

    @classmethod
    def push_to_gateway(cls, grouping_key: Optional[Dict[str, str]] = None):
        """Push all metrics to the configured push gateway."""
        cls._ensure_initialized()

        if not cls._push_gateway_url:
            cls._logger.warning("Push gateway URL yapılandırılmamış")
            raise PrometheusClientError(
                operation="push",
                message="Push gateway URL yapılandırılmamış"
            )

        try:
            push_to_gateway(
                cls._push_gateway_url,
                job=cls._job_name,
                registry=cls._registry,
                grouping_key=grouping_key or {}
            )
            cls._logger.debug(
                f"Metrikler push gateway'e gönderildi: {cls._push_gateway_url}",
                extra={
                    "push_gateway_url": cls._push_gateway_url,
                    "job_name": cls._job_name,
                    "grouping_key": grouping_key
                }
            )
        except Exception as e:
            cls._logger.error(
                f"Push gateway'e gönderilemedi: {e}",
                extra={
                    "push_gateway_url": cls._push_gateway_url,
                    "error": str(e)
                },
                exc_info=True
            )
            raise PrometheusClientError(
                operation="push",
                message=f"Push gateway'e gönderilemedi: {e}",
                cause=e
            ) from e

    @classmethod
    def start_http_server(cls, port: Optional[int] = None):
        """Start a HTTP server to expose metrics."""
        cls._ensure_initialized()

        metrics_port = port or cls._metrics_port

        try:
            start_http_server(metrics_port, registry=cls._registry)
            cls._logger.info(
                f"Prometheus HTTP server başlatıldı: port {metrics_port}",
                extra={"port": metrics_port}
            )
        except Exception as e:
            cls._logger.error(
                f"HTTP server başlatılamadı: {e}",
                extra={"port": metrics_port, "error": str(e)},
                exc_info=True
            )
            raise PrometheusClientError(
                operation="start_http_server",
                message=f"HTTP server başlatılamadı (port {metrics_port}): {e}",
                cause=e
            ) from e

    # =========================================================================
    # UTILITY
    # =========================================================================

    @classmethod
    def get_metric(cls, service: str, name: str) -> Optional[Any]:
        """Get a metric by service and name."""
        cls._ensure_initialized()

        full_name = cls._get_full_name(service, name)

        if full_name in cls._counters:
            return cls._counters[full_name]
        if full_name in cls._gauges:
            return cls._gauges[full_name]
        if full_name in cls._histograms:
            return cls._histograms[full_name]
        if full_name in cls._summaries:
            return cls._summaries[full_name]

        return None

    @classmethod
    def list_metrics(cls) -> Dict[str, List[str]]:
        """List all registered metrics by type."""
        cls._ensure_initialized()

        return {
            "counters": list(cls._counters.keys()),
            "gauges": list(cls._gauges.keys()),
            "histograms": list(cls._histograms.keys()),
            "summaries": list(cls._summaries.keys())
        }

    @classmethod
    def get_info(cls) -> Dict[str, Any]:
        """Get Prometheus client configuration info."""
        cls._ensure_initialized()

        return {
            "namespace": cls._namespace,
            "job_name": cls._job_name,
            "push_gateway_url": cls._push_gateway_url,
            "metrics_port": cls._metrics_port,
            "initialized": cls._initialized,
            "metric_counts": {
                "counters": len(cls._counters),
                "gauges": len(cls._gauges),
                "histograms": len(cls._histograms),
                "summaries": len(cls._summaries)
            }
        }

    @classmethod
    def reload(cls):
        """Reload Prometheus client configuration."""
        old_namespace = cls._namespace
        old_job_name = cls._job_name
        
        cls._logger.info(
            "Prometheus client yeniden yükleniyor...",
            extra={
                "old_namespace": old_namespace,
                "old_job_name": old_job_name
            }
        )
        
        with cls._lock:
            cls._initialized = False
            cls._registry = None
            cls._counters = {}
            cls._gauges = {}
            cls._histograms = {}
            cls._summaries = {}
        
        cls.load()
        
        cls._logger.info(
            "Prometheus client başarıyla yeniden yüklendi",
            extra={
                "new_namespace": cls._namespace,
                "new_job_name": cls._job_name,
                "old_namespace": old_namespace,
                "old_job_name": old_job_name
            }
        )

    @classmethod
    def close(cls):
        """Close and cleanup Prometheus client."""
        cls._logger.info(
            "Prometheus client kapatılıyor...",
            extra={
                "namespace": cls._namespace,
                "metric_counts": {
                    "counters": len(cls._counters),
                    "gauges": len(cls._gauges),
                    "histograms": len(cls._histograms),
                    "summaries": len(cls._summaries)
                }
            }
        )
        
        with cls._lock:
            cls._initialized = False
            cls._registry = None
            cls._counters = {}
            cls._gauges = {}
            cls._histograms = {}
            cls._summaries = {}
        
        cls._logger.info("Prometheus client kapatıldı")


class _MetricTimer:
    """Context manager for tracking execution time."""
    
    def __init__(
        self,
        client: PrometheusClient,
        service: str,
        name: str,
        labels: Optional[Dict[str, str]] = None
    ):
        self.client = client
        self.service = service
        self.name = name
        self.labels = labels
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = time.perf_counter() - self.start_time
        try:
            self.client.observe_histogram(self.service, self.name, elapsed, self.labels)
        except PrometheusMetricError:
            self.client._logger.warning(
                f"Histogram bulunamadı: {self.service}_{self.name}",
                extra={"service": self.service, "metric_name": self.name}
            )
    
    async def __aenter__(self):
        self.start_time = time.perf_counter()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        elapsed = time.perf_counter() - self.start_time
        try:
            self.client.observe_histogram(self.service, self.name, elapsed, self.labels)
        except PrometheusMetricError:
            self.client._logger.warning(
                f"Histogram bulunamadı: {self.service}_{self.name}",
                extra={"service": self.service, "metric_name": self.name}
            )
