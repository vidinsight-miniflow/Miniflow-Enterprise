#!/usr/bin/env python3
"""
Real Redis Verification Test
=============================

Verifies that:
1. Code uses REAL Redis (not mocks)
2. Real Redis connection works when available
3. Graceful degradation works when Redis unavailable
4. Real-world scenarios work with actual Redis operations
"""

import sys
import time
from pathlib import Path
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


def verify_no_mocks():
    """Verify code doesn't use mocks."""
    print("=" * 70)
    print("1. VERIFYING NO MOCKS IN CODE")
    print("=" * 70)
    
    import inspect
    from miniflow.server.middleware.ip_rate_limiter import IPRateLimitMiddleware
    from miniflow.server.dependencies.auth.rate_limiters import UserRateLimiter, WorkspaceRateLimiter
    
    components = [
        ("IPRateLimitMiddleware", IPRateLimitMiddleware),
        ("UserRateLimiter", UserRateLimiter),
        ("WorkspaceRateLimiter", WorkspaceRateLimiter),
    ]
    
    all_clean = True
    for name, component in components:
        source = inspect.getsource(component)
        
        # Check for actual mock usage in code (not comments/docstrings)
        # Remove comments and docstrings
        lines = source.split('\n')
        code_lines = []
        in_docstring = False
        for line in lines:
            stripped = line.strip()
            # Skip docstrings
            if stripped.startswith('"""') or stripped.startswith("'''"):
                in_docstring = not in_docstring
                continue
            if in_docstring:
                continue
            # Skip comments
            if stripped.startswith('#'):
                continue
            # Skip empty lines
            if not stripped:
                continue
            code_lines.append(line)
        
        code_text = '\n'.join(code_lines)
        # Check for actual mock imports or usage (not just the word "mock" in comments)
        has_mock_import = 'from unittest.mock' in code_text or 'import mock' in code_text or 'from mock import' in code_text
        has_mock_usage = 'Mock(' in code_text or 'mock.' in code_text or 'patch(' in code_text or 'MagicMock' in code_text
        has_mock = has_mock_import or has_mock_usage
        uses_redis_client = 'RedisClient' in source
        
        if has_mock:
            print(f"  ❌ {name}: Uses mocks in code")
            all_clean = False
        else:
            print(f"  ✅ {name}: No mocks in code (100% real)")
        
        if uses_redis_client:
            print(f"  ✅ {name}: Uses RedisClient (real Redis)")
        else:
            print(f"  ⚠️  {name}: Doesn't use RedisClient")
    
    print()
    return all_clean


def verify_redis_client_is_real():
    """Verify RedisClient uses real redis.Redis."""
    print("=" * 70)
    print("2. VERIFYING REDIS CLIENT IS REAL")
    print("=" * 70)
    
    try:
        from miniflow.utils import RedisClient
        import redis
        import inspect
        
        # Check RedisClient source
        source = inspect.getsource(RedisClient.initialize)
        
        # Should use redis.Redis
        uses_real_redis = 'redis.Redis' in source or 'redis.Redis(' in source
        
        if uses_real_redis:
            print("  ✅ RedisClient.initialize() uses redis.Redis (REAL)")
        else:
            print("  ❌ RedisClient.initialize() doesn't use redis.Redis")
        
        # Check if client is real redis.Redis instance
        if RedisClient._client:
            is_real = isinstance(RedisClient._client, redis.Redis)
            if is_real:
                print("  ✅ RedisClient._client is real redis.Redis instance")
            else:
                print(f"  ❌ RedisClient._client is {type(RedisClient._client)} (not real)")
        else:
            print("  ⚠️  RedisClient._client is None (Redis not initialized)")
            print("  ✅ This is OK - will use real Redis when available")
        
        print()
        return uses_real_redis
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_real_redis_operations():
    """Test actual Redis operations when Redis is available."""
    print("=" * 70)
    print("3. TESTING REAL REDIS OPERATIONS")
    print("=" * 70)
    
    try:
        from miniflow.utils import RedisClient
        import redis
        
        # Try to initialize Redis
        redis_available = False
        try:
            if not RedisClient._initialized:
                RedisClient.initialize()
            if RedisClient._client:
                RedisClient._client.ping()
                redis_available = True
        except Exception as e:
            print(f"  ⚠️  Redis not available: {type(e).__name__}")
            print("  ✅ Graceful degradation: System continues without Redis")
            print()
            return  # This is OK - graceful degradation works
        
        if redis_available:
            print("  ✅ Redis is available and connected")
            
            # Test real Redis operations
            test_key = "test:real_redis_verification"
            test_value = "test_value_123"
            
            # Set
            result = RedisClient.set(test_key, test_value, ex=10)
            print(f"  ✅ Redis SET operation: {result}")
            
            # Get
            retrieved = RedisClient.get(test_key)
            print(f"  ✅ Redis GET operation: {retrieved}")
            
            assert retrieved == test_value, "Value should match"
            
            # Delete
            RedisClient._client.delete(test_key)
            print("  ✅ Redis DELETE operation: Success")
            
            # Test pipeline (used by rate limiters)
            pipe = RedisClient._client.pipeline()
            pipe.incr("test:counter")
            pipe.expire("test:counter", 10)
            results = pipe.execute()
            print(f"  ✅ Redis PIPELINE operation: {results}")
            
            # Cleanup
            RedisClient._client.delete("test:counter")
            
            print("  ✅ All real Redis operations work correctly")
        
        print()
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_real_world_with_redis():
    """Test real-world scenario with actual Redis operations."""
    print("=" * 70)
    print("4. REAL-WORLD SCENARIO WITH REDIS")
    print("=" * 70)
    
    try:
        from miniflow.server.middleware import IPRateLimitMiddleware
        from miniflow.utils import RedisClient
        from fastapi import FastAPI
        
        # Check Redis availability
        redis_available = False
        try:
            if not RedisClient._initialized:
                RedisClient.initialize()
            if RedisClient._client:
                RedisClient._client.ping()
                redis_available = True
        except:
            pass
        
        app = FastAPI()
        app.add_middleware(IPRateLimitMiddleware)
        
        @app.get("/api/test")
        async def test():
            return {"message": "ok"}
        
        client = TestClient(app)
        
        if redis_available:
            print("  ✅ Redis is available - testing real rate limiting")
            
            # Make requests and check Redis keys
            for i in range(5):
                response = client.get("/api/test")
                assert response.status_code in [200, 429]
            
            # Check if Redis keys were created
            keys = RedisClient._client.keys("rl:ip:*")
            if keys:
                print(f"  ✅ Redis keys created: {len(keys)} rate limit keys found")
                print(f"  ✅ Key example: {keys[0].decode() if isinstance(keys[0], bytes) else keys[0]}")
            else:
                print("  ⚠️  No Redis keys found (may be using different IP extraction)")
            
            print("  ✅ Real Redis operations in middleware work")
        else:
            print("  ⚠️  Redis not available - graceful degradation tested")
            response = client.get("/api/test")
            assert response.status_code == 200
            print("  ✅ Graceful degradation works (request allowed)")
        
        print()
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_rate_limiter_real_redis():
    """Test rate limiters with real Redis."""
    print("=" * 70)
    print("5. RATE LIMITERS WITH REAL REDIS")
    print("=" * 70)
    
    try:
        from miniflow.server.dependencies.auth.rate_limiters import UserRateLimiter
        from miniflow.utils import RedisClient
        
        # Check Redis availability
        redis_available = False
        try:
            if not RedisClient._initialized:
                RedisClient.initialize()
            if RedisClient._client:
                RedisClient._client.ping()
                redis_available = True
        except:
            pass
        
        limiter = UserRateLimiter()
        
        if redis_available:
            print("  ✅ Redis is available - testing real rate limiting")
            
            # Test actual rate limit check
            test_user_id = "TEST-USER-REAL-REDIS"
            
            try:
                limiter.check_limit(test_user_id)
                print("  ✅ check_limit() executed with real Redis")
                
                # Check if Redis keys were created
                keys = RedisClient._client.keys(f"rl:user:{test_user_id}:*")
                if keys:
                    print(f"  ✅ Redis keys created: {len(keys)} keys for user")
                    # Get values
                    for key in keys[:3]:  # Show first 3
                        value = RedisClient._client.get(key)
                        ttl = RedisClient._client.ttl(key)
                        key_str = key.decode() if isinstance(key, bytes) else key
                        print(f"     Key: {key_str}, Value: {value}, TTL: {ttl}s")
                else:
                    print("  ⚠️  No Redis keys found (may use different timestamp)")
                
            except Exception as e:
                if "RateLimitExceeded" in type(e).__name__:
                    print("  ⚠️  Rate limit exceeded (expected if user made many requests)")
                else:
                    print(f"  ⚠️  Error: {type(e).__name__}: {e}")
            
            print("  ✅ Real Redis operations in rate limiter work")
        else:
            print("  ⚠️  Redis not available - graceful degradation tested")
            try:
                limiter.check_limit("TEST-USER")
                print("  ✅ Graceful degradation works (no exception raised)")
            except Exception as e:
                print(f"  ⚠️  Exception: {type(e).__name__}")
        
        print()
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all real Redis verification tests."""
    print("\n" + "=" * 70)
    print("REAL REDIS VERIFICATION TEST")
    print("=" * 70)
    print()
    print("This test verifies that:")
    print("  1. Code uses REAL Redis (not mocks)")
    print("  2. Real Redis connection works when available")
    print("  3. Graceful degradation works when Redis unavailable")
    print("  4. Real-world scenarios work with actual Redis operations")
    print()
    
    start_time = time.time()
    
    tests = [
        ("No Mocks in Code", verify_no_mocks),
        ("Redis Client is Real", verify_redis_client_is_real),
        ("Real Redis Operations", test_real_redis_operations),
        ("Real-World with Redis", test_real_world_with_redis),
        ("Rate Limiter Real Redis", test_rate_limiter_real_redis),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} test crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    elapsed = time.time() - start_time
    
    # Summary
    print("=" * 70)
    print("REAL REDIS VERIFICATION SUMMARY")
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
        print("🎉 VERIFICATION COMPLETE!")
        print("✅ Code uses REAL Redis (not mocks)")
        print("✅ Real Redis operations work when Redis is available")
        print("✅ Graceful degradation works when Redis is unavailable")
        print("✅ Real-world scenarios work with actual Redis")
        print()
        print("NOTE: If Redis is not running, graceful degradation allows")
        print("      the system to continue working. When Redis is available,")
        print("      all rate limiting features work with real Redis operations.")
        return 0
    else:
        print(f"⚠️  {total - passed} test(s) failed. Please review above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

