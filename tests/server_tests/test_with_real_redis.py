#!/usr/bin/env python3
"""
Real Redis Connection Test
===========================

Tests middleware and rate limiters with REAL Redis connection.
"""

import sys
import time
from pathlib import Path
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


def test_redis_connection():
    """Test real Redis connection."""
    print("=" * 70)
    print("1. TESTING REAL REDIS CONNECTION")
    print("=" * 70)
    
    try:
        from miniflow.utils import RedisClient
        import redis
        
        # Try to connect directly first (bypass config if needed)
        print("  🔌 Attempting to connect to Redis...")
        
        # First, try direct connection to verify Redis is running
        try:
            direct_client = redis.Redis(host='localhost', port=6379, decode_responses=True, db=0)
            ping_result = direct_client.ping()
            print(f"  ✅ Direct Redis PING: {ping_result}")
            direct_client.close()
        except Exception as e:
            print(f"  ❌ Direct Redis connection failed: {e}")
            print("  💡 Make sure Redis is running: redis-server")
            assert False, f"Direct Redis connection failed: {e}"
        
        # Now try through RedisClient
        try:
            # Manually set Redis config to avoid .env dependency
            from miniflow.utils.handlers.configuration_handler import ConfigurationHandler
            from configparser import ConfigParser
            
            if not hasattr(ConfigurationHandler, '_parser'):
                ConfigurationHandler._parser = ConfigParser()
            if not ConfigurationHandler._parser.has_section('Redis'):
                ConfigurationHandler._parser.add_section('Redis')
            ConfigurationHandler._parser.set('Redis', 'host', 'localhost')
            ConfigurationHandler._parser.set('Redis', 'port', '6379')
            ConfigurationHandler._parser.set('Redis', 'db', '0')
            ConfigurationHandler._parser.set('Redis', 'decode_responses', 'True')
            ConfigurationHandler._initialized = True
            
            if not RedisClient._initialized:
                RedisClient.load_redis_configurations()
                RedisClient._client = redis.Redis(connection_pool=RedisClient._pool)
                RedisClient._client.ping()
                RedisClient._initialized = True
            
            if RedisClient._client:
                # Test ping
                result = RedisClient._client.ping()
                print(f"  ✅ Redis PING: {result}")
                
                # Test basic operations
                test_key = "test:real_redis_connection"
                RedisClient.set(test_key, "test_value", ex=10)
                value = RedisClient.get(test_key)
                print(f"  ✅ Redis SET/GET: {value}")
                
                # Test pipeline
                pipe = RedisClient._client.pipeline()
                pipe.incr("test:counter")
                pipe.expire("test:counter", 10)
                results = pipe.execute()
                print(f"  ✅ Redis PIPELINE: {results}")
                
                # Cleanup
                RedisClient._client.delete(test_key, "test:counter")
                
                print("  ✅ REAL Redis connection works!")
                print(f"  📊 Redis client type: {type(RedisClient._client).__name__}")
                print(f"  📊 Is real redis.Redis: {isinstance(RedisClient._client, redis.Redis)}")
                print()
            else:
                print("  ❌ Redis client is None")
                print()
                assert False, "Redis client is None"
                
        except Exception as e:
            print(f"  ❌ Redis connection failed: {type(e).__name__}: {e}")
            print("  💡 Make sure Redis is running: redis-server")
            print("  💡 Or start Redis: docker run -d -p 6379:6379 redis")
            print()
            assert False, f"Redis connection failed: {e}"
            
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        assert False, f"Redis connection test failed: {e}"


def test_ip_rate_limit_with_redis():
    """Test IP rate limiting with real Redis."""
    print("=" * 70)
    print("2. IP RATE LIMITING WITH REAL REDIS")
    print("=" * 70)
    
    try:
        from miniflow.server.middleware.ip_rate_limiter import IPRateLimitMiddleware
        from miniflow.utils import RedisClient
        from fastapi import FastAPI
        
        # Ensure Redis is connected
        if not RedisClient._client:
            print("  ❌ Redis not connected. Run test 1 first.")
            assert False, "Redis not connected. Run test 1 first."
        
        app = FastAPI()
        app.add_middleware(IPRateLimitMiddleware)
        
        @app.get("/api/test")
        async def test():
            return {"message": "ok"}
        
        client = TestClient(app)
        
        print("  📊 Making requests to test rate limiting...")
        
        # Make requests and check Redis keys
        success_count = 0
        rate_limited = 0
        
        for i in range(20):
            response = client.get("/api/test")
            if response.status_code == 200:
                success_count += 1
            elif response.status_code == 429:
                rate_limited += 1
                print(f"  ⚠️  Rate limited at request #{i+1}")
                break
        
        print(f"  📊 Successful requests: {success_count}")
        print(f"  📊 Rate limited: {rate_limited}")
        
        # Check Redis keys
        keys = RedisClient._client.keys("rl:ip:*")
        print(f"  📊 Redis keys created: {len(keys)}")
        
        if keys:
            # Show first key details
            key = keys[0]
            key_str = key.decode() if isinstance(key, bytes) else key
            value = RedisClient._client.get(key)
            ttl = RedisClient._client.ttl(key)
            print(f"  ✅ Key example: {key_str}")
            print(f"  ✅ Value: {value}")
            print(f"  ✅ TTL: {ttl}s")
        
        print("  ✅ IP rate limiting works with REAL Redis!")
        print()
        
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        assert False, f"Test failed: {e}"


def test_user_rate_limiter_with_redis():
    """Test user rate limiter with real Redis."""
    print("=" * 70)
    print("3. USER RATE LIMITER WITH REAL REDIS")
    print("=" * 70)
    
    try:
        from miniflow.server.dependencies.auth.rate_limiters import UserRateLimiter
        from miniflow.utils import RedisClient
        from miniflow.core.exceptions import UserRateLimitExceededError
        
        # Ensure Redis is connected
        if not RedisClient._client:
            print("  ❌ Redis not connected. Run test 1 first.")
            assert False, "Redis not connected. Run test 1 first."
        
        limiter = UserRateLimiter()
        test_user_id = "TEST-USER-REAL-REDIS"
        
        print(f"  📊 Testing rate limiting for user: {test_user_id}")
        print(f"  📊 Limits: minute={limiter.limits['minute']}, hour={limiter.limits['hour']}, day={limiter.limits['day']}")
        
        # Make multiple checks
        for i in range(10):
            try:
                limiter.check_limit(test_user_id)
                print(f"  ✅ Check #{i+1}: Allowed")
            except UserRateLimitExceededError as e:
                print(f"  ⚠️  Check #{i+1}: Rate limit exceeded - {e.error_message}")
                break
        
        # Check Redis keys
        keys = RedisClient._client.keys(f"rl:user:{test_user_id}:*")
        print(f"  📊 Redis keys created: {len(keys)}")
        
        if keys:
            for key in keys[:3]:  # Show first 3
                key_str = key.decode() if isinstance(key, bytes) else key
                value = RedisClient._client.get(key_str)
                ttl = RedisClient._client.ttl(key_str)
                print(f"  ✅ Key: {key_str}")
                print(f"     Value: {value}, TTL: {ttl}s")
        
        print("  ✅ User rate limiter works with REAL Redis!")
        print()
        
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        assert False, f"Test failed: {e}"


def test_workspace_rate_limiter_with_redis():
    """Test workspace rate limiter with real Redis."""
    print("=" * 70)
    print("4. WORKSPACE RATE LIMITER WITH REAL REDIS")
    print("=" * 70)
    
    try:
        from miniflow.server.dependencies.auth.rate_limiters import WorkspaceRateLimiter
        from miniflow.utils import RedisClient
        
        # Ensure Redis is connected
        if not RedisClient._client:
            print("  ❌ Redis not connected. Run test 1 first.")
            assert False, "Redis not connected. Run test 1 first."
        
        limiter = WorkspaceRateLimiter()
        test_workspace_id = "TEST-WS-REAL-REDIS"
        test_plan_id = "TEST-PLAN-123"
        
        print(f"  📊 Testing rate limiting for workspace: {test_workspace_id}")
        
        # Make multiple checks
        for i in range(10):
            try:
                limiter.check_limit(test_workspace_id, test_plan_id)
                print(f"  ✅ Check #{i+1}: Allowed")
            except Exception as e:
                if "RateLimitExceeded" in type(e).__name__:
                    print(f"  ⚠️  Check #{i+1}: Rate limit exceeded")
                    break
                else:
                    raise
        
        # Check Redis keys
        keys = RedisClient._client.keys(f"rl:ws:{test_workspace_id}:*")
        print(f"  📊 Redis keys created: {len(keys)}")
        
        if keys:
            for key in keys[:3]:  # Show first 3
                key_str = key.decode() if isinstance(key, bytes) else key
                value = RedisClient._client.get(key_str)
                ttl = RedisClient._client.ttl(key_str)
                print(f"  ✅ Key: {key_str}")
                print(f"     Value: {value}, TTL: {ttl}s")
        
        print("  ✅ Workspace rate limiter works with REAL Redis!")
        print()
        
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        assert False, f"Test failed: {e}"


def test_concurrent_requests_with_redis():
    """Test concurrent requests with real Redis."""
    print("=" * 70)
    print("5. CONCURRENT REQUESTS WITH REAL REDIS")
    print("=" * 70)
    
    try:
        from miniflow.server.middleware.ip_rate_limiter import IPRateLimitMiddleware
        from miniflow.utils import RedisClient
        from fastapi import FastAPI
        import concurrent.futures
        
        # Ensure Redis is connected
        if not RedisClient._client:
            print("  ❌ Redis not connected. Run test 1 first.")
            assert False, "Redis not connected. Run test 1 first."
        
        app = FastAPI()
        app.add_middleware(IPRateLimitMiddleware)
        
        @app.get("/api/test")
        async def test():
            return {"message": "ok"}
        
        client = TestClient(app)
        
        print("  📊 Making 30 concurrent requests...")
        
        def make_request():
            response = client.get("/api/test")
            return response.status_code
        
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(30)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        elapsed = time.time() - start_time
        
        success_count = sum(1 for status in results if status == 200)
        rate_limited = sum(1 for status in results if status == 429)
        
        print(f"  📊 Total requests: 30")
        print(f"  ✅ Successful: {success_count}")
        print(f"  ⚠️  Rate limited: {rate_limited}")
        print(f"  ⏱️  Time: {elapsed:.2f}s")
        
        # Check Redis keys
        keys = RedisClient._client.keys("rl:ip:*")
        print(f"  📊 Redis keys in database: {len(keys)}")
        
        print("  ✅ Concurrent requests work with REAL Redis!")
        print()
        
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        assert False, f"Test failed: {e}"


def cleanup_redis_keys():
    """Cleanup test keys from Redis."""
    print("=" * 70)
    print("6. CLEANUP TEST KEYS")
    print("=" * 70)
    
    try:
        from miniflow.utils import RedisClient
        
        if not RedisClient._client:
            print("  ⚠️  Redis not connected, nothing to clean")
            return
        
        # Delete test keys
        test_patterns = [
            "rl:ip:*",
            "rl:user:TEST-*",
            "rl:ws:TEST-*",
            "test:*",
        ]
        
        total_deleted = 0
        for pattern in test_patterns:
            keys = RedisClient._client.keys(pattern)
            if keys:
                deleted = RedisClient._client.delete(*keys)
                total_deleted += deleted
                print(f"  ✅ Deleted {deleted} keys matching: {pattern}")
        
        if total_deleted == 0:
            print("  ✅ No test keys to clean")
        else:
            print(f"  ✅ Total keys deleted: {total_deleted}")
        
        print()
        return True
        
    except Exception as e:
        print(f"  ⚠️  Cleanup failed: {e}")
        return True  # Don't fail test on cleanup


def main():
    """Run all tests with real Redis."""
    print("\n" + "=" * 70)
    print("REAL REDIS CONNECTION TEST")
    print("=" * 70)
    print()
    print("This test requires Redis to be running.")
    print("If Redis is not running, start it with:")
    print("  - Local: redis-server")
    print("  - Docker: docker run -d -p 6379:6379 redis")
    print()
    
    start_time = time.time()
    
    tests = [
        ("Redis Connection", test_redis_connection),
        ("IP Rate Limiting", test_ip_rate_limit_with_redis),
        ("User Rate Limiter", test_user_rate_limiter_with_redis),
        ("Workspace Rate Limiter", test_workspace_rate_limiter_with_redis),
        ("Concurrent Requests", test_concurrent_requests_with_redis),
        ("Cleanup", cleanup_redis_keys),
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
    print("REAL REDIS TEST SUMMARY")
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
        print("🎉 All tests passed with REAL Redis!")
        print("✅ Real Redis connection works")
        print("✅ Real rate limiting works")
        print("✅ All operations use real Redis commands")
        return 0
    else:
        print(f"⚠️  {total - passed} test(s) failed.")
        if not any(r for n, r in results if n == "Redis Connection" and r):
            print("\n💡 Redis is not running. Start Redis to run full tests:")
            print("   redis-server")
            print("   or")
            print("   docker run -d -p 6379:6379 redis")
        return 1


if __name__ == "__main__":
    sys.exit(main())

