import pytest
import time
import asyncio
from unittest.mock import patch, MagicMock, call
from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram, Summary
from qbitra.utils.handlers.prometheus_handler import PrometheusClient
from qbitra.utils.handlers import ConfigurationHandler
from qbitra.core.exceptions import PrometheusClientError, PrometheusMetricError

@pytest.fixture(autouse=True)
def reset_prometheus_client():
    """Reset PrometheusClient class variables before each test."""
    PrometheusClient._initialized = False
    PrometheusClient._registry = None
    PrometheusClient._counters = {}
    PrometheusClient._gauges = {}
    PrometheusClient._histograms = {}
    PrometheusClient._summaries = {}
    PrometheusClient._namespace = None
    PrometheusClient._push_gateway_url = None
    PrometheusClient._job_name = None
    PrometheusClient._metrics_port = None
    yield

def test_load_success():
    """Test successful client loading and registry creation."""
    with patch.object(ConfigurationHandler, "ensure_loaded"), \
         patch.object(ConfigurationHandler, "get_value_as_str", side_effect=["test_ns", None, "test_job"]), \
         patch.object(ConfigurationHandler, "get_value_as_int", return_value=9090), \
         patch("qbitra.utils.handlers.prometheus_handler.CollectorRegistry") as mock_registry:
        
        PrometheusClient.load()
        
        assert PrometheusClient._initialized is True
        assert PrometheusClient._namespace == "test_ns"
        assert PrometheusClient._job_name == "test_job"
        assert PrometheusClient._metrics_port == 9090
        mock_registry.assert_called_once()

def test_load_failure():
    """Test client loading failure."""
    with patch.object(ConfigurationHandler, "ensure_loaded", side_effect=Exception("Config Error")):
        with pytest.raises(PrometheusClientError) as exc:
            PrometheusClient.load()
        assert "başlatılamadı" in str(exc.value)

def test_init_success():
    """Test successful initialization with validation."""
    def mock_load():
        PrometheusClient._initialized = True

    with patch.object(PrometheusClient, "load", side_effect=mock_load), \
         patch.object(PrometheusClient, "test", return_value=(True, "test_ns")):
        
        success = PrometheusClient.init()
        assert success is True
        assert PrometheusClient.is_initialized() is True

def test_init_failure():
    """Test initialization failure when test fails."""
    with patch.object(PrometheusClient, "load"), \
         patch.object(PrometheusClient, "test", return_value=(False, None)):
        
        with pytest.raises(PrometheusClientError) as exc:
            PrometheusClient.init()
        assert "test başarısız" in str(exc.value)

def test_ensure_initialized_error():
    """Test error when calling operation before initialization."""
    PrometheusClient._initialized = False
    with pytest.raises(PrometheusClientError) as exc:
        PrometheusClient.create_counter("svc", "cnt", "desc")
    assert "başlatılmadan metrik işlemi yapılamaz" in str(exc.value)

def test_metric_name_validation():
    """Test metric and label name validation logic."""
    assert PrometheusClient._validate_metric_name("valid_metric_123") is True
    assert PrometheusClient._validate_metric_name("invalid-metric") is False
    assert PrometheusClient._validate_metric_name("123metric") is False
    
    assert PrometheusClient._validate_label_name("valid_label") is True
    assert PrometheusClient._validate_label_name("invalid:label") is False

def test_create_counter():
    """Test counter creation and duplicate handling."""
    PrometheusClient._initialized = True
    PrometheusClient._registry = MagicMock()
    PrometheusClient._namespace = "qbitra"
    
    with patch("qbitra.utils.handlers.prometheus_handler.Counter") as mock_counter_cls:
        # Create first time
        mock_counter_cls.return_value = "counter_inst"
        res1 = PrometheusClient.create_counter("svc", "hits", "Desc")
        assert res1 == "counter_inst"
        assert PrometheusClient._counters["qbitra_svc_hits"] == "counter_inst"
        
        # Create second time - should return existing
        res2 = PrometheusClient.create_counter("svc", "hits", "Desc")
        assert res2 == "counter_inst"
        assert mock_counter_cls.call_count == 1

def test_create_counter_invalid_name():
    """Test counter creation with invalid name."""
    PrometheusClient._initialized = True
    with pytest.raises(PrometheusMetricError) as exc:
        PrometheusClient.create_counter("svc", "invalid-hits", "Desc")
    assert "Invalid metric name" in str(exc.value)

def test_counter_operations():
    """Test incrementing counters with and without labels."""
    PrometheusClient._initialized = True
    mock_counter = MagicMock()
    PrometheusClient._counters["qbitra_svc_hits"] = mock_counter
    PrometheusClient._namespace = "qbitra"
    
    # Simple increment
    PrometheusClient.increment_counter("svc", "hits")
    mock_counter.inc.assert_called_with(1)
    
    # Increment with labels
    labels = {"method": "GET", "path": "/api"}
    PrometheusClient.increment_counter("svc", "hits", value=5, labels=labels)
    mock_counter.labels.assert_called_with(**labels)
    mock_counter.labels.return_value.inc.assert_called_with(5)

def test_gauge_operations():
    """Test Gauge operations (set, inc, dec)."""
    PrometheusClient._initialized = True
    mock_gauge = MagicMock()
    PrometheusClient._gauges["qbitra_svc_metric"] = mock_gauge
    PrometheusClient._namespace = "qbitra"
    
    PrometheusClient.set_gauge("svc", "metric", 42)
    mock_gauge.set.assert_called_with(42)
    
    PrometheusClient.increment_gauge("svc", "metric", 10)
    mock_gauge.inc.assert_called_with(10)
    
    PrometheusClient.decrement_gauge("svc", "metric", 5)
    mock_gauge.dec.assert_called_with(5)

def test_histogram_summary_operations():
    """Test Histogram and Summary observe operations."""
    PrometheusClient._initialized = True
    mock_hist = MagicMock()
    mock_sum = MagicMock()
    PrometheusClient._histograms["qbitra_svc_hist"] = mock_hist
    PrometheusClient._summaries["qbitra_svc_sum"] = mock_sum
    PrometheusClient._namespace = "qbitra"
    
    PrometheusClient.observe_histogram("svc", "hist", 0.5)
    mock_hist.observe.assert_called_with(0.5)
    
    PrometheusClient.observe_summary("svc", "sum", 1.2)
    mock_sum.observe.assert_called_with(1.2)

def test_register_service_metrics():
    """Test bulk registration of metrics."""
    PrometheusClient._initialized = True
    PrometheusClient._namespace = "qbitra"
    PrometheusClient._registry = MagicMock()
    
    config = {
        "cnt": {"type": "counter", "description": "d1"},
        "gg": {"type": "gauge", "description": "d2"},
        "hist": {"type": "histogram", "description": "d3", "buckets": (1, 2)},
        "sum": {"type": "summary", "description": "d4"}
    }
    
    with patch.object(PrometheusClient, "create_counter") as m1, \
         patch.object(PrometheusClient, "create_gauge") as m2, \
         patch.object(PrometheusClient, "create_histogram") as m3, \
         patch.object(PrometheusClient, "create_summary") as m4:
        
        PrometheusClient.register_service_metrics("svc", config)
        m1.assert_called_once()
        m2.assert_called_once()
        m3.assert_called_once()
        m4.assert_called_once()

def test_track_time_sync():
    """Test @track_time decorator for sync functions."""
    PrometheusClient._initialized = True
    with patch.object(PrometheusClient, "observe_histogram") as mock_observe:
        @PrometheusClient.track_time("svc", "duration")
        def work():
            time.sleep(0.01)
            return "done"
        
        res = work()
        assert res == "done"
        mock_observe.assert_called_once()
        args, _ = mock_observe.call_args
        assert args[0] == "svc"
        assert args[1] == "duration"
        assert args[2] > 0

@pytest.mark.anyio
async def test_track_time_async():
    """Test @track_time decorator for async functions."""
    PrometheusClient._initialized = True
    with patch.object(PrometheusClient, "observe_histogram") as mock_observe:
        @PrometheusClient.track_time("svc", "duration_async")
        async def work():
            await asyncio.sleep(0.01)
            return "done"
        
        res = await work()
        assert res == "done"
        mock_observe.assert_called_once()

def test_track_in_progress():
    """Test @track_in_progress decorator (gauge inc/dec)."""
    PrometheusClient._initialized = True
    with patch.object(PrometheusClient, "increment_gauge") as mock_inc, \
         patch.object(PrometheusClient, "decrement_gauge") as mock_dec:
        
        @PrometheusClient.track_in_progress("svc", "active")
        def work():
            return "ok"
        
        work()
        mock_inc.assert_called_once_with("svc", "active", 1, None)
        mock_dec.assert_called_once_with("svc", "active", 1, None)

def test_timer_context_manager():
    """Test timer context manager (sync)."""
    PrometheusClient._initialized = True
    with patch.object(PrometheusClient, "observe_histogram") as mock_observe:
        with PrometheusClient.timer("svc", "timer_metric"):
            time.sleep(0.01)
        mock_observe.assert_called_once()

@pytest.mark.anyio
async def test_timer_context_manager_async():
    """Test timer context manager (async)."""
    PrometheusClient._initialized = True
    with patch.object(PrometheusClient, "observe_histogram") as mock_observe:
        async with PrometheusClient.timer("svc", "timer_async"):
            await asyncio.sleep(0.01)
        mock_observe.assert_called_once()

def test_export_and_push():
    """Test metric export and pushing to gateway."""
    PrometheusClient._initialized = True
    PrometheusClient._registry = MagicMock()
    PrometheusClient._push_gateway_url = "http://gateway"
    PrometheusClient._job_name = "job"
    
    with patch("qbitra.utils.handlers.prometheus_handler.generate_latest", return_value=b"metrics") as mock_gen:
        assert PrometheusClient.get_metrics() == b"metrics"
        mock_gen.assert_called_with(PrometheusClient._registry)
    
    with patch("qbitra.utils.handlers.prometheus_handler.push_to_gateway") as mock_push:
        grouping = {"node": "1"}
        PrometheusClient.push_to_gateway(grouping_key=grouping)
        mock_push.assert_called_with(
            "http://gateway",
            job="job",
            registry=PrometheusClient._registry,
            grouping_key=grouping
        )

def test_start_http_server():
    """Test starting the metrics HTTP server."""
    PrometheusClient._initialized = True
    PrometheusClient._registry = MagicMock()
    with patch("qbitra.utils.handlers.prometheus_handler.start_http_server") as mock_start:
        PrometheusClient.start_http_server(8080)
        mock_start.assert_called_once_with(8080, registry=PrometheusClient._registry)

def test_reload_and_close():
    """Test reload and close lifecycle."""
    PrometheusClient._initialized = True
    PrometheusClient._counters = {"c": 1}
    
    with patch.object(PrometheusClient, "load") as mock_load:
        PrometheusClient.reload()
        assert PrometheusClient._initialized is False
        assert PrometheusClient._counters == {}
        mock_load.assert_called_once()
    
    PrometheusClient._initialized = True
    PrometheusClient.close()
    assert PrometheusClient._initialized is False
    assert PrometheusClient._counters == {}
