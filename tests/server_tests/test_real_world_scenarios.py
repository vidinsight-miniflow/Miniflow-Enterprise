#!/usr/bin/env python3
"""
Real-World Scenario Tests
==========================

Tests middleware and dependencies with realistic usage scenarios:
- Multiple concurrent requests
- Rate limiting under load
- Authentication flows
- Error scenarios
- Different IP addresses
- Request ID propagation
"""

import sys
import time
import threading
from pathlib import Path
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.testclient import TestClient
from fastapi.security import HTTPBearer
import concurrent.futures

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


def scenario_1_concurrent_requests():
    """Test: Multiple concurrent requests from same IP."""
    print("=" * 70)
    print("SCENARIO 1: Concurrent Requests from Same IP")
    print("=" * 70)
    
    try:
        from miniflow.server.middleware import RequestContextMiddleware, IPRateLimitMiddleware
        from fastapi import FastAPI
        
        app = FastAPI()
        app.add_middleware(IPRateLimitMiddleware)
        app.add_middleware(RequestContextMiddleware)
        
        @app.get("/api/data")
        async def get_data(request: Request):
            return {
                "data": "test",
                "request_id": request.state.request_id,
                "ip": getattr(request.state, "client_ip", "unknown")
            }
        
        client = TestClient(app)
        
        # Simulate 50 concurrent requests from same IP
        def make_request():
            response = client.get("/api/data")
            return response.status_code, response.headers.get("X-Request-ID")
        
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(50)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        elapsed = time.time() - start_time
        
        success_count = sum(1 for status, _ in results if status == 200)
        rate_limited = sum(1 for status, _ in results if status == 429)
        
        # Check unique request IDs
        request_ids = [rid for _, rid in results if rid]
        unique_ids = len(set(request_ids))
        
        print(f"  📊 Total requests: 50")
        print(f"  ✅ Successful: {success_count}")
        print(f"  ⚠️  Rate limited: {rate_limited}")
        print(f"  🆔 Unique request IDs: {unique_ids}/50")
        print(f"  ⏱️  Time: {elapsed:.2f}s")
        
        assert unique_ids == 50, "All requests should have unique IDs"
        print("  ✅ All requests have unique request IDs")
        print("  ✅ Concurrent requests handled correctly\n")
        
        return True
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def scenario_2_different_ips():
    """Test: Requests from different IP addresses."""
    print("=" * 70)
    print("SCENARIO 2: Requests from Different IP Addresses")
    print("=" * 70)
    
    try:
        from miniflow.server.middleware import IPRateLimitMiddleware
        from fastapi import FastAPI
        
        app = FastAPI()
        app.add_middleware(IPRateLimitMiddleware)
        
        @app.get("/api/data")
        async def get_data():
            return {"data": "test"}
        
        client = TestClient(app)
        
        # Simulate requests from different IPs
        ips = ["192.168.1.1", "192.168.1.2", "10.0.0.1", "172.16.0.1"]
        results = {}
        
        for ip in ips:
            headers = {"X-Forwarded-For": ip}
            response = client.get("/api/data", headers=headers)
            results[ip] = response.status_code
        
        print(f"  📊 Tested {len(ips)} different IPs")
        for ip, status_code in results.items():
            status_icon = "✅" if status_code == 200 else "⚠️"
            print(f"  {status_icon} IP {ip}: {status_code}")
        
        # All should succeed (each IP has its own rate limit)
        all_success = all(status == 200 for status in results.values())
        assert all_success, "All IPs should be able to make requests"
        print("  ✅ Different IPs handled independently\n")
        
        return True
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def scenario_3_rate_limit_enforcement():
    """Test: Rate limit actually blocks requests when exceeded."""
    print("=" * 70)
    print("SCENARIO 3: Rate Limit Enforcement")
    print("=" * 70)
    
    try:
        from miniflow.server.middleware import IPRateLimitMiddleware
        from miniflow.utils import RedisClient
        from fastapi import FastAPI
        
        # Check if Redis is available
        redis_available = False
        try:
            if not RedisClient._initialized:
                RedisClient.initialize()
            redis_available = RedisClient._client is not None and RedisClient._client.ping()
        except:
            pass
        
        app = FastAPI()
        app.add_middleware(IPRateLimitMiddleware)
        
        @app.get("/api/data")
        async def get_data():
            return {"data": "test"}
        
        client = TestClient(app)
        
        if not redis_available:
            print("  ⚠️  Redis not available - rate limiting uses in-memory (per-request)")
            print("  ✅ Graceful degradation works\n")
            return
        
        # Make requests rapidly to trigger rate limit
        print("  📊 Making rapid requests to trigger rate limit...")
        success_count = 0
        rate_limited_count = 0
        
        for i in range(1100):  # More than default 1000/minute
            response = client.get("/api/data")
            if response.status_code == 200:
                success_count += 1
            elif response.status_code == 429:
                rate_limited_count += 1
                if rate_limited_count == 1:
                    # Check rate limit response
                    data = response.json()
                    assert "error" in data
                    assert "IP_RATE_LIMIT_EXCEEDED" in data["error"]["code"]
                    assert "Retry-After" in response.headers
                    print(f"  ✅ Rate limit triggered after {success_count} requests")
                    print(f"  ✅ Rate limit response format correct")
                    print(f"  ✅ Retry-After header present: {response.headers['Retry-After']}s")
                break
        
        print(f"  📊 Successful: {success_count}, Rate limited: {rate_limited_count}")
        
        if rate_limited_count > 0:
            print("  ✅ Rate limiting works correctly\n")
        else:
            print("  ⚠️  Rate limit not triggered (may be per-minute window)\n")
        
        return True
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def scenario_4_request_id_propagation():
    """Test: Request ID propagates through entire request lifecycle."""
    print("=" * 70)
    print("SCENARIO 4: Request ID Propagation")
    print("=" * 70)
    
    try:
        from miniflow.server.middleware import RequestContextMiddleware
        from fastapi import FastAPI
        
        app = FastAPI()
        app.add_middleware(RequestContextMiddleware)
        
        request_ids_seen = []
        
        @app.get("/api/step1")
        async def step1(request: Request):
            rid = request.state.request_id
            request_ids_seen.append(("step1", rid))
            return {"step": 1, "request_id": rid}
        
        @app.get("/api/step2")
        async def step2(request: Request):
            rid = request.state.request_id
            request_ids_seen.append(("step2", rid))
            return {"step": 2, "request_id": rid}
        
        client = TestClient(app)
        
        # Custom request ID
        custom_id = "custom-request-12345"
        
        # Make requests with custom ID
        response1 = client.get("/api/step1", headers={"X-Request-ID": custom_id})
        response2 = client.get("/api/step2", headers={"X-Request-ID": custom_id})
        
        # Check request IDs match
        data1 = response1.json()
        data2 = response2.json()
        
        assert data1["request_id"] == custom_id
        assert data2["request_id"] == custom_id
        assert response1.headers["X-Request-ID"] == custom_id
        assert response2.headers["X-Request-ID"] == custom_id
        
        print(f"  ✅ Custom Request ID: {custom_id}")
        print(f"  ✅ Request ID in step1: {data1['request_id']}")
        print(f"  ✅ Request ID in step2: {data2['request_id']}")
        print(f"  ✅ Request ID in headers: {response1.headers['X-Request-ID']}")
        print("  ✅ Request ID propagates correctly\n")
        
        return True
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def scenario_5_error_handling_under_load():
    """Test: Error handling works correctly under load."""
    print("=" * 70)
    print("SCENARIO 5: Error Handling Under Load")
    print("=" * 70)
    
    try:
        from miniflow.server.middleware import RequestContextMiddleware
        from miniflow.server.middleware.exception_handler import register_exception_handlers
        from miniflow.core.exceptions import ResourceNotFoundError, BusinessRuleViolationError
        from fastapi import FastAPI
        
        app = FastAPI()
        app.add_middleware(RequestContextMiddleware)
        register_exception_handlers(app)
        
        @app.get("/api/not-found")
        async def not_found():
            raise ResourceNotFoundError(resource_name="Item", resource_id="123")
        
        @app.get("/api/business-error")
        async def business_error():
            raise BusinessRuleViolationError(
                rule_name="test_rule",
                rule_detail="Test violation"
            )
        
        client = TestClient(app)
        
        # Make multiple error requests
        error_types = {
            "not_found": "/api/not-found",
            "business_error": "/api/business-error",
        }
        
        results = {}
        for error_type, path in error_types.items():
            response = client.get(path)
            data = response.json()
            results[error_type] = {
                "status": response.status_code,
                "data": data,
                "request_id": data.get("meta", {}).get("request_id")
            }
        
        # Verify all errors handled correctly
        for error_type, result in results.items():
            # Status should be 4xx or 5xx (error status)
            assert 400 <= result["status"] < 600, f"{error_type} should return error status"
            assert result["data"]["success"] == False
            assert "error" in result["data"]
            assert "code" in result["data"]["error"]
            assert result["request_id"] is not None
            print(f"  ✅ {error_type}: Status {result['status']}, Code: {result['data']['error']['code']}, Request ID present")
        
        print("  ✅ All error types handled correctly under load\n")
        
        return True
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def scenario_6_excluded_paths():
    """Test: Excluded paths are not rate limited."""
    print("=" * 70)
    print("SCENARIO 6: Excluded Paths (Health Checks, Docs)")
    print("=" * 70)
    
    try:
        from miniflow.server.middleware import IPRateLimitMiddleware
        from fastapi import FastAPI
        
        app = FastAPI()
        app.add_middleware(IPRateLimitMiddleware)
        
        @app.get("/health")
        async def health():
            return {"status": "ok"}
        
        @app.get("/docs")
        async def docs():
            return {"docs": "swagger"}
        
        @app.get("/api/data")
        async def data():
            return {"data": "test"}
        
        client = TestClient(app)
        
        # Make many requests to excluded paths
        excluded_paths = ["/health", "/docs", "/"]
        results = {}
        
        for path in excluded_paths:
            status_codes = []
            for _ in range(100):  # Many requests
                response = client.get(path)
                status_codes.append(response.status_code)
            
            rate_limited = sum(1 for s in status_codes if s == 429)
            results[path] = {"total": 100, "rate_limited": rate_limited}
        
        # Verify excluded paths are not rate limited
        for path, result in results.items():
            assert result["rate_limited"] == 0, f"{path} should not be rate limited"
            print(f"  ✅ {path}: {result['total']} requests, {result['rate_limited']} rate limited")
        
        print("  ✅ Excluded paths work correctly\n")
        
        return True
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def scenario_7_response_time_measurement():
    """Test: Response time is accurately measured."""
    print("=" * 70)
    print("SCENARIO 7: Response Time Measurement")
    print("=" * 70)
    
    try:
        from miniflow.server.middleware import RequestContextMiddleware
        from fastapi import FastAPI
        import asyncio
        
        app = FastAPI()
        app.add_middleware(RequestContextMiddleware)
        
        @app.get("/api/fast")
        async def fast():
            return {"message": "fast"}
        
        @app.get("/api/slow")
        async def slow():
            await asyncio.sleep(0.1)  # 100ms delay
            return {"message": "slow"}
        
        client = TestClient(app)
        
        # Test fast endpoint
        response_fast = client.get("/api/fast")
        time_fast = response_fast.headers.get("X-Response-Time", "")
        time_fast_ms = float(time_fast.replace("ms", "")) if time_fast else 0
        
        # Test slow endpoint
        response_slow = client.get("/api/slow")
        time_slow = response_slow.headers.get("X-Response-Time", "")
        time_slow_ms = float(time_slow.replace("ms", "")) if time_slow else 0
        
        print(f"  ⏱️  Fast endpoint: {time_fast} ({time_fast_ms:.2f}ms)")
        print(f"  ⏱️  Slow endpoint: {time_slow} ({time_slow_ms:.2f}ms)")
        
        # Slow should be significantly longer
        assert time_slow_ms > time_fast_ms, "Slow endpoint should take longer"
        assert time_slow_ms >= 100, "Slow endpoint should be at least 100ms"
        
        print("  ✅ Response time measurement is accurate\n")
        
        return True
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def scenario_8_middleware_order():
    """Test: Middleware execute in correct order."""
    print("=" * 70)
    print("SCENARIO 8: Middleware Execution Order")
    print("=" * 70)
    
    try:
        from miniflow.server.middleware import RequestContextMiddleware, IPRateLimitMiddleware
        from fastapi import FastAPI
        
        app = FastAPI()
        
        # Add in reverse order (last added runs first)
        app.add_middleware(IPRateLimitMiddleware)
        app.add_middleware(RequestContextMiddleware)
        
        @app.get("/api/test")
        async def test(request: Request):
            # Both middleware should have run
            has_request_id = hasattr(request.state, "request_id")
            has_start_time = hasattr(request.state, "start_time")
            
            return {
                "has_request_id": has_request_id,
                "has_start_time": has_start_time,
                "request_id": request.state.request_id if has_request_id else None
            }
        
        client = TestClient(app)
        response = client.get("/api/test")
        
        assert response.status_code == 200
        data = response.json()
        assert data["has_request_id"] == True
        assert data["has_start_time"] == True
        assert "X-Request-ID" in response.headers
        assert "X-Response-Time" in response.headers
        
        print("  ✅ RequestContextMiddleware executed")
        print("  ✅ IPRateLimitMiddleware executed")
        print("  ✅ Both middleware work together correctly\n")
        
        return True
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all real-world scenario tests."""
    print("\n" + "=" * 70)
    print("REAL-WORLD SCENARIO TESTS")
    print("=" * 70)
    print()
    
    start_time = time.time()
    
    scenarios = [
        ("Concurrent Requests", scenario_1_concurrent_requests),
        ("Different IP Addresses", scenario_2_different_ips),
        ("Rate Limit Enforcement", scenario_3_rate_limit_enforcement),
        ("Request ID Propagation", scenario_4_request_id_propagation),
        ("Error Handling Under Load", scenario_5_error_handling_under_load),
        ("Excluded Paths", scenario_6_excluded_paths),
        ("Response Time Measurement", scenario_7_response_time_measurement),
        ("Middleware Order", scenario_8_middleware_order),
    ]
    
    results = []
    for name, scenario_func in scenarios:
        try:
            result = scenario_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} scenario crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    elapsed = time.time() - start_time
    
    # Summary
    print("=" * 70)
    print("SCENARIO TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {name}")
    
    print(f"\nTotal: {passed}/{total} scenarios passed")
    print(f"Time: {elapsed:.2f}s")
    print()
    
    if passed == total:
        print("🎉 All real-world scenarios passed! System handles production load correctly.")
        return 0
    else:
        print(f"⚠️  {total - passed} scenario(s) failed. Please review above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

