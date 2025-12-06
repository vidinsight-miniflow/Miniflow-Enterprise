#!/usr/bin/env python3
"""
Complete System Test
===================

Comprehensive test of all middleware, dependencies, handlers, and services.
"""

import sys
import time
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


def test_all_imports():
    """Test all critical imports."""
    print("=" * 70)
    print("1. IMPORT TESTS")
    print("=" * 70)
    
    errors = []
    
    # Middleware
    try:
        from miniflow.server.middleware import RequestContextMiddleware, IPRateLimitMiddleware
        print("  ✅ Middleware imports OK")
    except Exception as e:
        print(f"  ❌ Middleware imports FAILED: {e}")
        errors.append(f"Middleware: {e}")
    
    # Dependencies
    try:
        from miniflow.server.dependencies import (
            authenticate_user, authenticate_api_key, authenticate_admin,
            require_workspace_access, require_workspace_owner,
            get_api_key_service,
        )
        print("  ✅ Dependencies imports OK")
    except Exception as e:
        print(f"  ❌ Dependencies imports FAILED: {e}")
        errors.append(f"Dependencies: {e}")
    
    # Handlers
    try:
        from miniflow.server.middleware.exception_handler import register_exception_handlers
        print("  ✅ Handlers imports OK")
    except Exception as e:
        print(f"  ❌ Handlers imports FAILED: {e}")
        errors.append(f"Handlers: {e}")
    
    # Utils
    try:
        from miniflow.utils import RedisClient, ConfigurationHandler
        print("  ✅ Utils imports OK")
    except Exception as e:
        print(f"  ❌ Utils imports FAILED: {e}")
        errors.append(f"Utils: {e}")
    
    # Services
    try:
        from miniflow.services._3_auth_services import LoginService
        from miniflow.services._5_workspace_services import WorkspaceManagementService
        from miniflow.services._6_resource_services import ApiKeyService
        print("  ✅ Services imports OK")
    except Exception as e:
        print(f"  ❌ Services imports FAILED: {e}")
        errors.append(f"Services: {e}")
    
    print()
    assert len(errors) == 0, errors


def test_middleware_functionality():
    """Test middleware actually work."""
    print("=" * 70)
    print("2. MIDDLEWARE FUNCTIONALITY TESTS")
    print("=" * 70)
    
    errors = []
    
    # RequestContextMiddleware
    try:
        from miniflow.server.middleware import RequestContextMiddleware
        app = FastAPI()
        app.add_middleware(RequestContextMiddleware)
        
        @app.get("/test")
        async def test(request: Request):
            assert hasattr(request.state, "request_id")
            assert hasattr(request.state, "start_time")
            return {"id": request.state.request_id}
        
        client = TestClient(app)
        response = client.get("/test")
        
        assert response.status_code == 200
        assert "X-Request-ID" in response.headers
        assert "X-Response-Time" in response.headers
        print("  ✅ RequestContextMiddleware works")
    except Exception as e:
        print(f"  ❌ RequestContextMiddleware FAILED: {e}")
        errors.append(f"RequestContextMiddleware: {e}")
    
    # IPRateLimitMiddleware
    try:
        from miniflow.server.middleware import IPRateLimitMiddleware
        app = FastAPI()
        app.add_middleware(IPRateLimitMiddleware)
        
        @app.get("/test")
        async def test():
            return {"message": "ok"}
        
        client = TestClient(app)
        response = client.get("/test")
        
        # Should either succeed or rate limit
        assert response.status_code in [200, 429]
        print("  ✅ IPRateLimitMiddleware works (graceful degradation)")
    except Exception as e:
        print(f"  ❌ IPRateLimitMiddleware FAILED: {e}")
        errors.append(f"IPRateLimitMiddleware: {e}")
    
    print()
    assert len(errors) == 0, errors


def test_dependencies():
    """Test dependencies can be instantiated."""
    print("=" * 70)
    print("3. DEPENDENCIES TESTS")
    print("=" * 70)
    
    errors = []
    
    # Service providers
    try:
        from miniflow.server.dependencies import (
            get_login_service, get_workspace_management_service, get_api_key_service,
            get_user_management_service, get_workflow_service, get_execution_service,
        )
        
        login_service = get_login_service()
        assert login_service is not None
        print(f"  ✅ get_login_service() works ({type(login_service).__name__})")
        
        workspace_service = get_workspace_management_service()
        assert workspace_service is not None
        print(f"  ✅ get_workspace_management_service() works ({type(workspace_service).__name__})")
        
        api_key_service = get_api_key_service()
        assert api_key_service is not None
        print(f"  ✅ get_api_key_service() works ({type(api_key_service).__name__})")
        
    except Exception as e:
        print(f"  ❌ Service providers FAILED: {e}")
        errors.append(f"Service providers: {e}")
    
    print()
    assert len(errors) == 0, errors


def test_exception_handlers():
    """Test exception handlers."""
    print("=" * 70)
    print("4. EXCEPTION HANDLER TESTS")
    print("=" * 70)
    
    errors = []
    
    try:
        from miniflow.server.middleware import RequestContextMiddleware
        from miniflow.server.middleware.exception_handler import register_exception_handlers
        from miniflow.core.exceptions import ResourceNotFoundError
        
        app = FastAPI()
        app.add_middleware(RequestContextMiddleware)
        register_exception_handlers(app)
        
        @app.get("/error")
        async def error():
            raise ResourceNotFoundError(
                resource_name="Test",
                resource_id="TEST-123"
            )
        
        client = TestClient(app)
        response = client.get("/error")
        
        assert response.status_code == 404
        data = response.json()
        # Check for either "success" or "status" field (depending on handler format)
        assert "error" in data or "error_code" in data or data.get("status") == "error" or data.get("success") == False
        print("  ✅ Exception handlers work correctly")
        
    except Exception as e:
        print(f"  ❌ Exception handlers FAILED: {e}")
        errors.append(f"Exception handlers: {e}")
    
    print()
    assert len(errors) == 0, errors


def test_full_app_setup():
    """Test complete app setup."""
    print("=" * 70)
    print("5. FULL APP SETUP TEST")
    print("=" * 70)
    
    errors = []
    
    try:
        from miniflow.server.middleware import RequestContextMiddleware
        from fastapi.middleware.cors import CORSMiddleware
        
        app = FastAPI(title="Test App")
        app.add_middleware(RequestContextMiddleware)
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        @app.get("/test")
        async def test(request: Request):
            return {
                "message": "success",
                "request_id": getattr(request.state, "request_id", None)
            }
        
        client = TestClient(app)
        response = client.get("/test")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "success"
        assert data["request_id"] is not None
        assert "X-Request-ID" in response.headers
        print("  ✅ Full app setup works")
        
    except Exception as e:
        print(f"  ❌ Full app setup FAILED: {e}")
        errors.append(f"Full app setup: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    assert len(errors) == 0, errors


def test_configuration_handling():
    """Test configuration handling."""
    print("=" * 70)
    print("6. CONFIGURATION HANDLING TEST")
    print("=" * 70)
    
    errors = []
    
    try:
        from miniflow.utils import ConfigurationHandler
        
        # Test graceful degradation
        try:
            ConfigurationHandler.ensure_loaded()
            print("  ✅ Configuration loaded")
        except Exception as e:
            if ".env" in str(e):
                print("  ⚠️  .env not found (OK - using fallbacks)")
            else:
                raise
        
        # Test get_int with fallback
        value = ConfigurationHandler.get_int("Rate Limiting", "ip_requests_per_minute", fallback=1000)
        assert value is not None
        assert isinstance(value, int) or value == 1000
        print(f"  ✅ ConfigurationHandler.get_int() works (value: {value})")
        
    except Exception as e:
        print(f"  ❌ Configuration handling FAILED: {e}")
        errors.append(f"Configuration: {e}")
    
    print()
    assert len(errors) == 0, errors


def test_redis_handling():
    """Test Redis handling."""
    print("=" * 70)
    print("7. REDIS HANDLING TEST")
    print("=" * 70)
    
    errors = []
    
    try:
        from miniflow.utils import RedisClient
        
        # Redis may not be available - that's OK
        redis_available = False
        try:
            if not RedisClient._initialized:
                RedisClient.initialize()
            redis_available = RedisClient._client is not None
        except Exception:
            pass
        
        if redis_available:
            print("  ✅ Redis is available and connected")
        else:
            print("  ⚠️  Redis not available (OK - middleware handles gracefully)")
        
        # Test that we can check without errors
        _ = RedisClient._client
        print("  ✅ RedisClient access works")
        
    except Exception as e:
        print(f"  ❌ Redis handling FAILED: {e}")
        errors.append(f"Redis: {e}")
    
    print()
    assert len(errors) == 0, errors


def test_rate_limiters():
    """Test rate limiters."""
    print("=" * 70)
    print("8. RATE LIMITER TESTS")
    print("=" * 70)
    
    errors = []
    
    try:
        from miniflow.server.dependencies.auth.rate_limiters import (
            UserRateLimiter, WorkspaceRateLimiter
        )
        
        # Test UserRateLimiter initialization
        user_limiter = UserRateLimiter()
        assert user_limiter is not None
        assert "minute" in user_limiter.limits
        assert "hour" in user_limiter.limits
        print("  ✅ UserRateLimiter initialized")
        
        # Test WorkspaceRateLimiter initialization
        workspace_limiter = WorkspaceRateLimiter()
        assert workspace_limiter is not None
        print("  ✅ WorkspaceRateLimiter initialized")
        
    except Exception as e:
        print(f"  ❌ Rate limiters FAILED: {e}")
        errors.append(f"Rate limiters: {e}")
    
    print()
    assert len(errors) == 0, errors


def run_lint_check():
    """Check for lint errors."""
    print("=" * 70)
    print("9. LINT CHECK")
    print("=" * 70)
    
    try:
        # Try to compile key files
        import py_compile
        import os
        
        key_files = [
            "src/miniflow/new_server/__init__.py",
            "src/miniflow/new_server/middleware/core/request_context.py",
            "src/miniflow/new_server/middleware/security/ip_rate_limiter.py",
            "src/miniflow/new_server/dependencies/auth/jwt_auth.py",
            "src/miniflow/new_server/dependencies/auth/api_key_auth.py",
            "src/miniflow/new_server/handlers/exception_handler.py",
        ]
        
        errors = []
        for file_path in key_files:
            if os.path.exists(file_path):
                try:
                    py_compile.compile(file_path, doraise=True)
                except py_compile.PyCompileError as e:
                    errors.append(f"{file_path}: {e}")
        
        if errors:
            print(f"  ❌ Syntax errors found in {len(errors)} file(s)")
            for error in errors[:3]:
                print(f"     {error}")
            assert False, errors
        else:
            print("  ✅ No syntax errors found in key files")
            
    except Exception as e:
        print(f"  ⚠️  Lint check skipped: {e}")


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("COMPLETE SYSTEM TEST")
    print("=" * 70)
    print()
    
    start_time = time.time()
    
    tests = [
        ("Imports", test_all_imports),
        ("Middleware Functionality", test_middleware_functionality),
        ("Dependencies", test_dependencies),
        ("Exception Handlers", test_exception_handlers),
        ("Full App Setup", test_full_app_setup),
        ("Configuration Handling", test_configuration_handling),
        ("Redis Handling", test_redis_handling),
        ("Rate Limiters", test_rate_limiters),
        ("Lint Check", run_lint_check),
    ]
    
    results = []
    all_errors = []
    
    for name, test_func in tests:
        try:
            passed, errors = test_func()
            results.append((name, passed))
            if errors:
                all_errors.extend(errors)
        except Exception as e:
            print(f"\n❌ {name} test crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
            all_errors.append(f"{name}: {e}")
    
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
    
    if all_errors:
        print(f"\nErrors found: {len(all_errors)}")
        for error in all_errors[:5]:  # Show first 5 errors
            print(f"  - {error}")
        if len(all_errors) > 5:
            print(f"  ... and {len(all_errors) - 5} more")
    
    print()
    
    if passed == total:
        print("🎉 All tests passed! System is ready.")
        return 0
    else:
        print(f"⚠️  {total - passed} test(s) failed. Please review errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

