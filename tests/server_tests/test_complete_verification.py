#!/usr/bin/env python3
"""
Complete System Verification
============================

Comprehensive verification of:
- Exception handler coverage
- Real-world scenario tests
- Exception handler comparison
- System integration
"""

import sys
import subprocess
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


def run_test(test_file: str, description: str) -> tuple[bool, str]:
    """Run a test file and return result."""
    try:
        result = subprocess.run(
            ["python3", test_file],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Check if test passed
        passed = result.returncode == 0
        
        # Extract summary from output
        output_lines = result.stdout.split('\n')
        summary = None
        for line in output_lines:
            if "Total:" in line or "passed" in line.lower() or "✅" in line or "❌" in line:
                summary = line.strip()
                break
        
        return passed, summary or "No summary found"
    except subprocess.TimeoutExpired:
        return False, "Test timed out"
    except Exception as e:
        return False, f"Error: {str(e)}"


def check_exception_handler_imports():
    """Check if exception handler can be imported."""
    print("=" * 70)
    print("1. IMPORT CHECK")
    print("=" * 70)
    
    try:
        from miniflow.server.middleware.exception_handler import (
            ERROR_CODE_TO_HTTP_STATUS,
            app_exception_handler,
            validation_exception_handler,
            http_exception_handler,
            generic_exception_handler,
        )
        print("  ✅ All exception handler imports successful")
        print(f"  ✅ Error code mappings: {len(ERROR_CODE_TO_HTTP_STATUS)}")
        print()
    except Exception as e:
        print(f"  ❌ Import failed: {e}")
        print()
        assert False, f"Import check failed: {e}"


def check_exception_coverage():
    """Check exception coverage."""
    print("=" * 70)
    print("2. EXCEPTION COVERAGE CHECK")
    print("=" * 70)
    
    try:
        from miniflow.core.exceptions import ErrorCode
        from miniflow.server.middleware.exception_handler import ERROR_CODE_TO_HTTP_STATUS
        
        all_codes = set(ErrorCode)
        mapped_codes = set(ERROR_CODE_TO_HTTP_STATUS.keys())
        
        missing = all_codes - mapped_codes
        
        if missing:
            print(f"  ❌ Missing mappings: {len(missing)}")
            for code in missing:
                print(f"     - {code.value}")
            print()
            assert False, f"Missing error code mappings: {missing}"
        else:
            print(f"  ✅ All {len(all_codes)} error codes mapped")
            print()
    except Exception as e:
        print(f"  ❌ Check failed: {e}")
        print()
        assert False, f"Error code mapping check failed: {e}"


def check_handler_registration():
    """Check handler registration."""
    print("=" * 70)
    print("3. HANDLER REGISTRATION CHECK")
    print("=" * 70)
    
    try:
        from fastapi import FastAPI
        from miniflow.server.middleware.exception_handler import register_exception_handlers
        from miniflow.core.exceptions import AppException
        from fastapi.exceptions import RequestValidationError
        from starlette.exceptions import HTTPException as StarletteHTTPException
        
        app = FastAPI()
        register_exception_handlers(app)
        
        handlers = app.exception_handlers
        required = {AppException, RequestValidationError, StarletteHTTPException, Exception}
        registered = set(handlers.keys())
        
        missing = required - registered
        
        if missing:
            print(f"  ❌ Missing handlers: {len(missing)}")
            for handler in missing:
                print(f"     - {handler.__name__}")
            print()
            assert False, f"Missing handlers: {missing}"
        else:
            print(f"  ✅ All {len(required)} handlers registered")
            for handler in required:
                print(f"     - {handler.__name__}")
            print()
    except Exception as e:
        print(f"  ❌ Check failed: {e}")
        print()
        assert False, f"Handler registration check failed: {e}"


def run_all_tests():
    """Run all test suites."""
    print("=" * 70)
    print("4. TEST SUITE EXECUTION")
    print("=" * 70)
    
    # Get the directory where this test file is located
    test_dir = Path(__file__).parent
    
    tests = [
        (test_dir / "test_exception_coverage.py", "Exception Coverage Test"),
        (test_dir / "test_exception_handler_comparison.py", "Exception Handler Comparison"),
        (test_dir / "test_real_life_exception_scenarios.py", "Real-Life Scenarios Test"),
    ]
    
    results = []
    for test_file, description in tests:
        if not test_file.exists():
            print(f"  ⚠️  {description}: File not found ({test_file})")
            results.append((description, False, "File not found"))
            continue
        
        print(f"  Running: {description}...")
        passed, summary = run_test(str(test_file), description)
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status} - {description}")
        if summary:
            print(f"    {summary}")
        results.append((description, passed, summary))
        print()
    
    return results


def check_system_integration():
    """Check system integration."""
    print("=" * 70)
    print("5. SYSTEM INTEGRATION CHECK")
    print("=" * 70)
    
    try:
        from fastapi import FastAPI
        from miniflow.server.middleware.exception_handler import register_exception_handlers
        from miniflow.core.exceptions import ResourceNotFoundError
        from fastapi.testclient import TestClient
        
        app = FastAPI()
        register_exception_handlers(app)
        
        @app.get("/test")
        async def test_endpoint():
            raise ResourceNotFoundError(resource_name="Test", resource_id="123")
        
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/test")
        
        if response.status_code == 404:
            data = response.json()
            if data.get("status") == "error" and data.get("error_code") == "RESOURCE_NOT_FOUND":
                print("  ✅ Exception handler integrated correctly")
                print(f"  ✅ Status: {response.status_code}")
                print(f"  ✅ Error Code: {data['error_code']}")
                print()
            else:
                print("  ❌ Unexpected response format")
                print(f"  Response: {data}")
                print()
                assert False, f"Unexpected response format: {data}"
        else:
            print(f"  ❌ Unexpected status code: {response.status_code}")
            print()
            assert False, f"Unexpected status code: {response.status_code}"
    except Exception as e:
        print(f"  ❌ Integration check failed: {e}")
        import traceback
        traceback.print_exc()
        print()
        assert False, f"Integration check failed: {e}"


def main():
    """Run complete verification."""
    print("\n" + "=" * 70)
    print("COMPLETE SYSTEM VERIFICATION")
    print("=" * 70)
    print()
    
    checks = [
        ("Import Check", check_exception_handler_imports),
        ("Exception Coverage", check_exception_coverage),
        ("Handler Registration", check_handler_registration),
        ("System Integration", check_system_integration),
    ]
    
    check_results = []
    for name, check_func in checks:
        try:
            result = check_func()
            check_results.append((name, result))
        except Exception as e:
            print(f"  ❌ {name} crashed: {e}")
            check_results.append((name, False))
    
    # Run test suites
    test_results = run_all_tests()
    
    # Summary
    print("=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)
    
    print("\n📋 CHECKS:")
    check_passed = sum(1 for _, result in check_results if result)
    check_total = len(check_results)
    for name, result in check_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {name}")
    
    print("\n📋 TEST SUITES:")
    test_passed = sum(1 for _, result, _ in test_results if result)
    test_total = len(test_results)
    for name, result, summary in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {name}")
        if summary and not result:
            print(f"    {summary}")
    
    total_passed = check_passed + test_passed
    total_total = check_total + test_total
    
    print(f"\n{'=' * 70}")
    print(f"OVERALL: {total_passed}/{total_total} checks passed")
    print(f"{'=' * 70}\n")
    
    if total_passed == total_total:
        print("🎉 ALL CHECKS PASSED!")
        print("✅ Exception handler is fully functional")
        print("✅ All error codes mapped")
        print("✅ All handlers registered")
        print("✅ System integration working")
        print("✅ All tests passing")
        print("\n✅ SYSTEM IS PRODUCTION-READY!")
        return 0
    else:
        print(f"⚠️  {total_total - total_passed} check(s) failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

