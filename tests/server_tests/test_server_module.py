#!/usr/bin/env python3
"""
Server Module Comprehensive Tests
=================================

Tests for:
- Middleware (request_context, ip_rate_limiter, exception_handler)
- Dependencies (auth, access, service_providers)
- Schemas (base_schemas)
- Integration tests
"""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


# ============================================================================
# 1. IMPORT TESTS
# ============================================================================

def test_middleware_imports():
    """Test middleware imports."""
    print("=" * 70)
    print("1. MIDDLEWARE IMPORTS")
    print("=" * 70)
    
    results = []
    
    try:
        from miniflow.server.middleware.request_context import RequestContextMiddleware
        results.append(("RequestContextMiddleware", True))
        print("  ✅ RequestContextMiddleware")
    except Exception as e:
        results.append(("RequestContextMiddleware", False))
        print(f"  ❌ RequestContextMiddleware: {e}")
    
    try:
        from miniflow.server.middleware.ip_rate_limiter import IPRateLimitMiddleware
        results.append(("IPRateLimitMiddleware", True))
        print("  ✅ IPRateLimitMiddleware")
    except Exception as e:
        results.append(("IPRateLimitMiddleware", False))
        print(f"  ❌ IPRateLimitMiddleware: {e}")
    
    try:
        from miniflow.server.middleware.exception_handler import (
            ERROR_CODE_TO_HTTP_STATUS,
            app_exception_handler,
            validation_exception_handler,
            http_exception_handler,
            generic_exception_handler,
        )
        results.append(("exception_handler", True))
        print("  ✅ exception_handler")
    except Exception as e:
        results.append(("exception_handler", False))
        print(f"  ❌ exception_handler: {e}")
    
    print()
    assert all(r[1] for r in results), f"Some imports failed: {[r[0] for r in results if not r[1]]}"


def test_dependency_imports():
    """Test dependency imports."""
    print("=" * 70)
    print("2. DEPENDENCY IMPORTS")
    print("=" * 70)
    
    results = []
    
    # Auth dependencies
    try:
        from miniflow.server.dependencies.auth.jwt_auth import (
            authenticate_user,
            authenticate_admin,
            AuthenticatedUser,
        )
        results.append(("jwt_auth", True))
        print("  ✅ jwt_auth")
    except Exception as e:
        results.append(("jwt_auth", False))
        print(f"  ❌ jwt_auth: {e}")
    
    try:
        from miniflow.server.dependencies.auth.api_key_auth import (
            authenticate_api_key,
            ApiKeyCredentials,
        )
        results.append(("api_key_auth", True))
        print("  ✅ api_key_auth")
    except Exception as e:
        results.append(("api_key_auth", False))
        print(f"  ❌ api_key_auth: {e}")
    
    try:
        from miniflow.server.dependencies.auth.rate_limiters import (
            UserRateLimiter,
            WorkspaceRateLimiter,
        )
        results.append(("rate_limiters", True))
        print("  ✅ rate_limiters")
    except Exception as e:
        results.append(("rate_limiters", False))
        print(f"  ❌ rate_limiters: {e}")
    
    # Access dependencies
    try:
        from miniflow.server.dependencies.access.workspace_access import (
            extract_workspace_id,
            require_workspace_access,
            require_workspace_access_allow_suspended,
            require_workspace_owner,
        )
        results.append(("workspace_access", True))
        print("  ✅ workspace_access")
    except Exception as e:
        results.append(("workspace_access", False))
        print(f"  ❌ workspace_access: {e}")
    
    # Service providers
    try:
        from miniflow.server.dependencies.service_providers import (
            get_login_service,
            get_register_service,
            get_workspace_service,
            get_api_key_service,
        )
        results.append(("service_providers", True))
        print("  ✅ service_providers")
    except Exception as e:
        results.append(("service_providers", False))
        print(f"  ❌ service_providers: {e}")
    
    print()
    assert all(r[1] for r in results), f"Some imports failed: {[r[0] for r in results if not r[1]]}"


def test_schema_imports():
    """Test schema imports."""
    print("=" * 70)
    print("3. SCHEMA IMPORTS")
    print("=" * 70)
    
    results = []
    
    try:
        from miniflow.server.schemas.base_schemas import (
            BaseResponse,
            SuccessResponse,
            FailuresResponse,
            get_trace_id,
            create_success_response,
            create_error_response,
        )
        results.append(("base_schemas", True))
        print("  ✅ base_schemas")
    except Exception as e:
        results.append(("base_schemas", False))
        print(f"  ❌ base_schemas: {e}")
    
    print()
    assert all(r[1] for r in results), f"Some imports failed: {[r[0] for r in results if not r[1]]}"


# ============================================================================
# 2. EXCEPTION HANDLER TESTS
# ============================================================================

def test_error_code_mapping():
    """Test all error codes are mapped to HTTP status."""
    print("=" * 70)
    print("4. ERROR CODE TO HTTP STATUS MAPPING")
    print("=" * 70)
    
    try:
        from miniflow.core.exceptions import ErrorCode
        from miniflow.server.middleware.exception_handler import ERROR_CODE_TO_HTTP_STATUS
        
        all_codes = set(ErrorCode)
        mapped_codes = set(ERROR_CODE_TO_HTTP_STATUS.keys())
        
        missing = all_codes - mapped_codes
        
        if missing:
            print(f"  ❌ Missing {len(missing)} error codes:")
            for code in list(missing)[:5]:
                print(f"     - {code.value}")
            if len(missing) > 5:
                print(f"     ... and {len(missing) - 5} more")
            print()
            assert False, f"Missing error code mappings: {missing}"
        else:
            print(f"  ✅ All {len(all_codes)} error codes mapped")
            print()
            
    except Exception as e:
        print(f"  ❌ Test failed: {e}")
        print()
        assert False, f"Error code mapping test failed: {e}"


def test_exception_handlers():
    """Test exception handlers work correctly."""
    print("=" * 70)
    print("5. EXCEPTION HANDLERS")
    print("=" * 70)
    
    try:
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from miniflow.core.exceptions import (
            ResourceNotFoundError,
            InvalidInputError,
            BusinessRuleViolationError,
            AuthenticationFailedError,
        )
        from miniflow.server.middleware.exception_handler import (
            app_exception_handler,
            validation_exception_handler,
            http_exception_handler,
            generic_exception_handler,
        )
        from miniflow.core.exceptions import AppException
        from fastapi.exceptions import RequestValidationError
        from starlette.exceptions import HTTPException as StarletteHTTPException
        
        app = FastAPI()
        
        # Register handlers
        app.add_exception_handler(AppException, app_exception_handler)
        app.add_exception_handler(RequestValidationError, validation_exception_handler)
        app.add_exception_handler(StarletteHTTPException, http_exception_handler)
        app.add_exception_handler(Exception, generic_exception_handler)
        
        # Test endpoints
        @app.get("/test/not-found")
        async def test_not_found():
            raise ResourceNotFoundError(resource_name="User", resource_id="123")
        
        @app.get("/test/invalid-input")
        async def test_invalid_input():
            raise InvalidInputError(field_name="email", message="Invalid email format")
        
        @app.get("/test/business-rule")
        async def test_business_rule():
            raise BusinessRuleViolationError(
                rule_name="max_users", 
                rule_detail="Maximum users exceeded"
            )
        
        @app.get("/test/auth-failed")
        async def test_auth_failed():
            raise AuthenticationFailedError(message="Invalid credentials")
        
        client = TestClient(app, raise_server_exceptions=False)
        
        # Test ResourceNotFoundError -> 404
        response = client.get("/test/not-found")
        if response.status_code == 404:
            print("  ✅ ResourceNotFoundError -> 404")
        else:
            print(f"  ❌ ResourceNotFoundError -> {response.status_code} (expected 404)")
            assert False, f"ResourceNotFoundError returned {response.status_code}, expected 404"
        
        # Test InvalidInputError -> 400
        response = client.get("/test/invalid-input")
        if response.status_code == 400:
            print("  ✅ InvalidInputError -> 400")
        else:
            print(f"  ❌ InvalidInputError -> {response.status_code} (expected 400)")
            assert False, f"InvalidInputError returned {response.status_code}, expected 400"
        
        # Test BusinessRuleViolationError -> 400
        response = client.get("/test/business-rule")
        if response.status_code == 400:
            print("  ✅ BusinessRuleViolationError -> 400")
        else:
            print(f"  ❌ BusinessRuleViolationError -> {response.status_code} (expected 400)")
            assert False, f"BusinessRuleViolationError returned {response.status_code}, expected 400"
        
        # Test AuthenticationFailedError -> 401
        response = client.get("/test/auth-failed")
        if response.status_code == 401:
            print("  ✅ AuthenticationFailedError -> 401")
        else:
            print(f"  ❌ AuthenticationFailedError -> {response.status_code} (expected 401)")
            assert False, f"AuthenticationFailedError returned {response.status_code}, expected 401"
        
        print()
        
    except Exception as e:
        print(f"  ❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        print()
        assert False, f"Exception handlers test failed: {e}"


# ============================================================================
# 3. MIDDLEWARE TESTS
# ============================================================================

def test_request_context_middleware():
    """Test request context middleware."""
    print("=" * 70)
    print("6. REQUEST CONTEXT MIDDLEWARE")
    print("=" * 70)
    
    try:
        from fastapi import FastAPI, Request
        from fastapi.testclient import TestClient
        from miniflow.server.middleware.request_context import RequestContextMiddleware
        
        app = FastAPI()
        app.add_middleware(RequestContextMiddleware)
        
        @app.get("/test")
        async def test_endpoint(request: Request):
            return {
                "request_id": getattr(request.state, "request_id", None),
                "has_start_time": hasattr(request.state, "start_time"),
            }
        
        client = TestClient(app)
        
        # Test 1: Auto-generated request ID
        response = client.get("/test")
        assert response.status_code == 200
        data = response.json()
        
        if data["request_id"] is not None:
            print(f"  ✅ Request ID generated: {data['request_id'][:8]}...")
        else:
            print("  ❌ Request ID not generated")
            assert False, "Request ID not generated"
        
        if data["has_start_time"]:
            print("  ✅ Start time set")
        else:
            print("  ❌ Start time not set")
            assert False, "Start time not set"
        
        # Test 2: Custom request ID
        custom_id = "CUSTOM-REQUEST-ID-12345"
        response = client.get("/test", headers={"X-Request-ID": custom_id})
        data = response.json()
        
        if data["request_id"] == custom_id:
            print(f"  ✅ Custom request ID preserved: {custom_id[:15]}...")
        else:
            print(f"  ❌ Custom request ID not preserved")
            assert False, f"Custom request ID not preserved: got {data['request_id']}, expected {custom_id}"
        
        # Test 3: Response headers
        if "X-Request-ID" in response.headers:
            print("  ✅ X-Request-ID in response headers")
        else:
            print("  ❌ X-Request-ID not in response headers")
            assert False, "X-Request-ID not in response headers"
        
        if "X-Response-Time" in response.headers:
            print(f"  ✅ X-Response-Time: {response.headers['X-Response-Time']}")
        else:
            print("  ❌ X-Response-Time not in response headers")
            assert False, "X-Response-Time not in response headers"
        
        print()
        
    except Exception as e:
        print(f"  ❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        print()
        assert False, f"Request context middleware test failed: {e}"


def test_ip_rate_limiter_middleware():
    """Test IP rate limiter middleware."""
    print("=" * 70)
    print("7. IP RATE LIMITER MIDDLEWARE")
    print("=" * 70)
    
    try:
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from miniflow.server.middleware.ip_rate_limiter import IPRateLimitMiddleware
        
        app = FastAPI()
        app.add_middleware(IPRateLimitMiddleware)
        
        @app.get("/test")
        async def test_endpoint():
            return {"status": "ok"}
        
        @app.get("/health")
        async def health():
            return {"status": "healthy"}
        
        client = TestClient(app)
        
        # Test 1: Normal request
        response = client.get("/test")
        if response.status_code == 200:
            print("  ✅ Normal request successful")
        else:
            print(f"  ❌ Normal request failed: {response.status_code}")
            assert False, f"Normal request failed with status {response.status_code}"
        
        # Test 2: Excluded path
        response = client.get("/health")
        if response.status_code == 200:
            print("  ✅ Excluded path (/health) works")
        else:
            print(f"  ❌ Excluded path failed: {response.status_code}")
            assert False, f"Excluded path failed with status {response.status_code}"
        
        # Test 3: Multiple requests (should not hit rate limit with high defaults)
        success_count = 0
        for i in range(10):
            response = client.get("/test")
            if response.status_code == 200:
                success_count += 1
        
        print(f"  ✅ {success_count}/10 requests successful")
        
        print()
        
    except Exception as e:
        print(f"  ❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        print()
        assert False, f"IP rate limiter middleware test failed: {e}"


# ============================================================================
# 4. DEPENDENCY TESTS
# ============================================================================

def test_workspace_access_validation():
    """Test workspace ID validation."""
    print("=" * 70)
    print("8. WORKSPACE ACCESS VALIDATION")
    print("=" * 70)
    
    try:
        from miniflow.server.dependencies.access.workspace_access import WORKSPACE_ID_PATTERN
        
        # Valid IDs
        valid_ids = [
            "WSP-1234567890ABCDEF",
            "WSP-ABCDEF1234567890",
            "WSP-0000000000000000",
            "WSP-FFFFFFFFFFFFFFFF",
        ]
        
        for wid in valid_ids:
            if WORKSPACE_ID_PATTERN.match(wid):
                print(f"  ✅ Valid: {wid}")
            else:
                print(f"  ❌ Should be valid: {wid}")
                assert False, f"Workspace ID {wid} should be valid but pattern didn't match"
        
        # Invalid IDs
        invalid_ids = [
            "WSP-123",  # Too short
            "WSP-1234567890ABCDEFG",  # Too long
            "WS-1234567890ABCDEF",  # Wrong prefix
            "WSP-1234567890abcdef",  # Lowercase
            "1234567890ABCDEF",  # No prefix
            "WSP1234567890ABCDEF",  # No dash
        ]
        
        for wid in invalid_ids:
            if not WORKSPACE_ID_PATTERN.match(wid):
                print(f"  ✅ Invalid: {wid}")
            else:
                print(f"  ❌ Should be invalid: {wid}")
                assert False, f"Workspace ID {wid} should be invalid but pattern matched"
        
        print()
        
    except Exception as e:
        print(f"  ❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        print()
        assert False, f"Workspace access validation test failed: {e}"


def test_rate_limiter_classes():
    """Test rate limiter class structure."""
    print("=" * 70)
    print("9. RATE LIMITER CLASSES")
    print("=" * 70)
    
    try:
        from miniflow.server.dependencies.auth.rate_limiters import (
            BaseRateLimiter,
            UserRateLimiter,
            WorkspaceRateLimiter,
        )
        
        # Test UserRateLimiter
        user_limiter = UserRateLimiter()
        
        if hasattr(user_limiter, 'limits'):
            print(f"  ✅ UserRateLimiter has limits")
            print(f"     minute: {user_limiter.limits.get('minute', 'N/A')}")
            print(f"     hour: {user_limiter.limits.get('hour', 'N/A')}")
            print(f"     day: {user_limiter.limits.get('day', 'N/A')}")
        else:
            print("  ❌ UserRateLimiter missing limits")
            assert False, "UserRateLimiter missing limits attribute"
        
        if hasattr(user_limiter, 'check_limit'):
            print("  ✅ UserRateLimiter has check_limit method")
        else:
            print("  ❌ UserRateLimiter missing check_limit method")
            assert False, "UserRateLimiter missing check_limit method"
        
        # Test WorkspaceRateLimiter
        ws_limiter = WorkspaceRateLimiter()
        
        if hasattr(ws_limiter, 'check_limit'):
            print("  ✅ WorkspaceRateLimiter has check_limit method")
        else:
            print("  ❌ WorkspaceRateLimiter missing check_limit method")
            assert False, "WorkspaceRateLimiter missing check_limit method"
        
        if hasattr(ws_limiter, '_load_plan_limits'):
            print("  ✅ WorkspaceRateLimiter has _load_plan_limits method")
        else:
            print("  ❌ WorkspaceRateLimiter missing _load_plan_limits method")
            assert False, "WorkspaceRateLimiter missing _load_plan_limits method"
        
        print()
        
    except Exception as e:
        print(f"  ❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        print()
        assert False, f"Rate limiter classes test failed: {e}"


# ============================================================================
# 5. SCHEMA TESTS
# ============================================================================

def test_response_schemas():
    """Test response schema creation."""
    print("=" * 70)
    print("10. RESPONSE SCHEMAS")
    print("=" * 70)
    
    try:
        from fastapi import FastAPI, Request
        from fastapi.testclient import TestClient
        from miniflow.server.schemas.base_schemas import (
            create_success_response,
            create_error_response,
        )
        from miniflow.server.middleware.request_context import RequestContextMiddleware
        
        app = FastAPI()
        app.add_middleware(RequestContextMiddleware)
        
        @app.get("/success")
        async def success_endpoint(request: Request):
            response = create_success_response(
                request,
                data={"user": "test"},
                message="Operation successful",
            )
            return response.model_dump()
        
        @app.get("/error")
        async def error_endpoint(request: Request):
            response = create_error_response(
                request,
                error_message="Something went wrong",
                error_code="TEST_ERROR",
            )
            return response.model_dump()
        
        client = TestClient(app)
        
        # Test success response
        response = client.get("/success")
        data = response.json()
        
        if data.get("status") == "success":
            print("  ✅ Success response: status=success")
        else:
            print(f"  ❌ Success response status: {data.get('status')}")
            assert False, f"Success response status is {data.get('status')}, expected 'success'"
        
        if "traceId" in data:
            print(f"  ✅ Success response has traceId")
        else:
            print("  ❌ Success response missing traceId")
            assert False, "Success response missing traceId"
        
        if "timestamp" in data:
            print(f"  ✅ Success response has timestamp")
        else:
            print("  ❌ Success response missing timestamp")
            assert False, "Success response missing timestamp"
        
        if data.get("data") == {"user": "test"}:
            print("  ✅ Success response has correct data")
        else:
            print(f"  ❌ Success response data: {data.get('data')}")
            assert False, f"Success response data is {data.get('data')}, expected {{'user': 'test'}}"
        
        # Test error response
        response = client.get("/error")
        data = response.json()
        
        if data.get("status") == "error":
            print("  ✅ Error response: status=error")
        else:
            print(f"  ❌ Error response status: {data.get('status')}")
            assert False, f"Error response status is {data.get('status')}, expected 'error'"
        
        if data.get("error_code") == "TEST_ERROR":
            print("  ✅ Error response has correct error_code")
        else:
            print(f"  ❌ Error response error_code: {data.get('error_code')}")
            assert False, f"Error response error_code is {data.get('error_code')}, expected 'TEST_ERROR'"
        
        print()
        
    except Exception as e:
        print(f"  ❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        print()
        assert False, f"Response schemas test failed: {e}"


# ============================================================================
# 6. INTEGRATION TESTS
# ============================================================================

def test_full_integration():
    """Test full server integration."""
    print("=" * 70)
    print("11. FULL SERVER INTEGRATION")
    print("=" * 70)
    
    try:
        from fastapi import FastAPI, Request
        from fastapi.testclient import TestClient
        from miniflow.server.middleware.request_context import RequestContextMiddleware
        from miniflow.server.middleware.ip_rate_limiter import IPRateLimitMiddleware
        from miniflow.server.middleware.exception_handler import (
            app_exception_handler,
            http_exception_handler,
            generic_exception_handler,
        )
        from miniflow.server.schemas.base_schemas import create_success_response
        from miniflow.core.exceptions import AppException, ResourceNotFoundError
        from starlette.exceptions import HTTPException as StarletteHTTPException
        
        # Create app with all middleware
        app = FastAPI()
        
        # Add exception handlers
        app.add_exception_handler(AppException, app_exception_handler)
        app.add_exception_handler(StarletteHTTPException, http_exception_handler)
        app.add_exception_handler(Exception, generic_exception_handler)
        
        # Add middleware (reverse order)
        app.add_middleware(IPRateLimitMiddleware)
        app.add_middleware(RequestContextMiddleware)
        
        @app.get("/api/test")
        async def test_endpoint(request: Request):
            return create_success_response(
                request,
                data={"message": "Hello, World!"},
            ).model_dump()
        
        @app.get("/api/error")
        async def error_endpoint():
            raise ResourceNotFoundError(resource_name="Test", resource_id="123")
        
        client = TestClient(app, raise_server_exceptions=False)
        
        # Test 1: Successful request
        response = client.get("/api/test")
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                print("  ✅ Successful request works")
            else:
                print(f"  ❌ Unexpected response: {data}")
                assert False, f"Unexpected response: {data}"
        else:
            print(f"  ❌ Request failed: {response.status_code}")
            assert False, f"Request failed with status {response.status_code}"
        
        # Test 2: Request ID in response
        if "X-Request-ID" in response.headers:
            print(f"  ✅ X-Request-ID: {response.headers['X-Request-ID'][:8]}...")
        else:
            print("  ❌ X-Request-ID missing")
            assert False, "X-Request-ID missing from response headers"
        
        # Test 3: Response time in headers
        if "X-Response-Time" in response.headers:
            print(f"  ✅ X-Response-Time: {response.headers['X-Response-Time']}")
        else:
            print("  ❌ X-Response-Time missing")
            assert False, "X-Response-Time missing from response headers"
        
        # Test 4: Error handling
        response = client.get("/api/error")
        if response.status_code == 404:
            print("  ✅ Error handling works (404)")
        else:
            print(f"  ❌ Error handling failed: {response.status_code}")
            assert False, f"Error handling failed with status {response.status_code}"
        
        print()
        
    except Exception as e:
        print(f"  ❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        print()
        assert False, f"Full integration test failed: {e}"


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("SERVER MODULE COMPREHENSIVE TESTS")
    print("=" * 70)
    print()
    
    start_time = time.time()
    
    tests = [
        ("Middleware Imports", test_middleware_imports),
        ("Dependency Imports", test_dependency_imports),
        ("Schema Imports", test_schema_imports),
        ("Error Code Mapping", test_error_code_mapping),
        ("Exception Handlers", test_exception_handlers),
        ("Request Context Middleware", test_request_context_middleware),
        ("IP Rate Limiter Middleware", test_ip_rate_limiter_middleware),
        ("Workspace Access Validation", test_workspace_access_validation),
        ("Rate Limiter Classes", test_rate_limiter_classes),
        ("Response Schemas", test_response_schemas),
        ("Full Integration", test_full_integration),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    elapsed = time.time() - start_time
    
    # Summary
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    print(f"Time: {elapsed:.2f}s")
    print()
    
    if passed == total:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Server module is fully functional")
        return 0
    else:
        print(f"⚠️  {total - passed} test(s) failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

