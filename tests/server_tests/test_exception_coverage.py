#!/usr/bin/env python3
"""
Exception Coverage Test
======================

Tests if exception handler covers ALL miniflow exceptions correctly.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from miniflow.core.exceptions import ErrorCode
from miniflow.server.middleware.exception_handler import ERROR_CODE_TO_HTTP_STATUS


def test_all_error_codes_mapped():
    """Test that all ErrorCode enum values are mapped to HTTP status codes."""
    print("=" * 70)
    print("1. ERROR CODE MAPPING COVERAGE")
    print("=" * 70)
    
    all_error_codes = list(ErrorCode)
    mapped_codes = set(ERROR_CODE_TO_HTTP_STATUS.keys())
    all_codes_set = set(all_error_codes)
    
    missing = all_codes_set - mapped_codes
    extra = mapped_codes - all_codes_set
    
    print(f"  📊 Total ErrorCodes: {len(all_error_codes)}")
    print(f"  📊 Mapped ErrorCodes: {len(mapped_codes)}")
    
    if missing:
        print(f"\n  ❌ MISSING MAPPINGS ({len(missing)}):")
        for code in sorted(missing, key=lambda x: x.value):
            print(f"     - {code.value}")
        assert False, f"Missing mappings: {missing}"
    else:
        print(f"  ✅ All error codes are mapped")
    
    if extra:
        print(f"\n  ⚠️  EXTRA MAPPINGS ({len(extra)}):")
        for code in sorted(extra, key=lambda x: x.value):
            print(f"     - {code.value}")
    
    print()


def test_all_exception_classes():
    """Test that all exception classes are AppException subclasses."""
    print("=" * 70)
    print("2. EXCEPTION CLASS HIERARCHY")
    print("=" * 70)
    
    from miniflow.core.exceptions import (
        AppException,
        ValidationError,
        InvalidInputError,
        ResourceNotFoundError,
        ResourceAlreadyExistsError,
        BusinessRuleViolationError,
        DatabaseValidationError,
        AuthenticationError,
        AuthenticationFailedError,
        InvalidCredentialsError,
        TokenExpiredError,
        TokenInvalidError,
        UnauthorizedError,
        ForbiddenError,
        InsufficientPermissionsError,
        InvalidApiKeyError,
        RateLimitError,
        IpRateLimitExceededError,
        UserRateLimitExceededError,
        ApiKeyMinuteRateLimitExceededError,
        ApiKeyHourRateLimitExceededError,
        ApiKeyDayRateLimitExceededError,
        DatabaseError,
        DatabaseConnectionError,
        DatabaseQueryError,
        DatabaseTransactionError,
        DatabaseSessionError,
        DatabaseEngineError,
        DatabaseConfigurationError,
        ExternalServiceError,
        ExternalServiceTimeoutError,
        ExternalServiceUnavailableError,
        ExternalServiceConnectionError,
        ExternalServiceRequestError,
        ExternalServiceResponseError,
        ExternalServiceValidationError,
        ExternalServiceAuthorizationError,
        ExternalServiceRateLimitError,
        SchedulerError,
        ContextCreationError,
        PayloadPreparationError,
        EngineSubmissionError,
        ResultProcessingError,
        HandlerConfigurationError,
        InternalError,
        NotImplementedError,
    )
    
    exception_classes = [
        ValidationError,
        InvalidInputError,
        ResourceNotFoundError,
        ResourceAlreadyExistsError,
        BusinessRuleViolationError,
        DatabaseValidationError,
        AuthenticationError,
        AuthenticationFailedError,
        InvalidCredentialsError,
        TokenExpiredError,
        TokenInvalidError,
        UnauthorizedError,
        ForbiddenError,
        InsufficientPermissionsError,
        InvalidApiKeyError,
        RateLimitError,
        IpRateLimitExceededError,
        UserRateLimitExceededError,
        ApiKeyMinuteRateLimitExceededError,
        ApiKeyHourRateLimitExceededError,
        ApiKeyDayRateLimitExceededError,
        DatabaseError,
        DatabaseConnectionError,
        DatabaseQueryError,
        DatabaseTransactionError,
        DatabaseSessionError,
        DatabaseEngineError,
        DatabaseConfigurationError,
        ExternalServiceError,
        ExternalServiceTimeoutError,
        ExternalServiceUnavailableError,
        ExternalServiceConnectionError,
        ExternalServiceRequestError,
        ExternalServiceResponseError,
        ExternalServiceValidationError,
        ExternalServiceAuthorizationError,
        ExternalServiceRateLimitError,
        SchedulerError,
        ContextCreationError,
        PayloadPreparationError,
        EngineSubmissionError,
        ResultProcessingError,
        HandlerConfigurationError,
        InternalError,
        NotImplementedError,
    ]
    
    all_valid = True
    for exc_class in exception_classes:
        if not issubclass(exc_class, AppException):
            print(f"  ❌ {exc_class.__name__} is not an AppException subclass")
            all_valid = False
    
    if all_valid:
        print(f"  ✅ All {len(exception_classes)} exception classes are AppException subclasses")
    else:
        assert False, "Some exception classes are not AppException subclasses"
    
    print()


def test_exception_handler_registration():
    """Test that all exception types are handled."""
    print("=" * 70)
    print("3. EXCEPTION HANDLER REGISTRATION")
    print("=" * 70)
    
    from fastapi import FastAPI
    from miniflow.server.middleware.exception_handler import register_exception_handlers
    from miniflow.core.exceptions import AppException
    from fastapi.exceptions import RequestValidationError
    from starlette.exceptions import HTTPException as StarletteHTTPException
    
    app = FastAPI()
    register_exception_handlers(app)
    
    # Check registered handlers
    handlers = app.exception_handlers
    
    required_handlers = {
        AppException,
        RequestValidationError,
        StarletteHTTPException,
        Exception,  # Generic catch-all
    }
    
    registered = set(handlers.keys())
    missing = required_handlers - registered
    
    if missing:
        print(f"  ❌ MISSING HANDLERS ({len(missing)}):")
        for handler_type in missing:
            print(f"     - {handler_type.__name__}")
        assert False, f"Missing handlers: {missing}"
    else:
        print(f"  ✅ All required handlers registered ({len(required_handlers)})")
        for handler_type in required_handlers:
            print(f"     - {handler_type.__name__}")
    
    print()


def test_http_status_mapping_accuracy():
    """Test that HTTP status codes are correctly mapped."""
    print("=" * 70)
    print("4. HTTP STATUS CODE MAPPING ACCURACY")
    print("=" * 70)
    
    from fastapi import status
    
    # Expected mappings based on error categories
    expected_mappings = {
        # Validation (400-422)
        ErrorCode.VALIDATION_ERROR: status.HTTP_422_UNPROCESSABLE_ENTITY,
        ErrorCode.INVALID_INPUT: status.HTTP_400_BAD_REQUEST,
        ErrorCode.RESOURCE_NOT_FOUND: status.HTTP_404_NOT_FOUND,
        ErrorCode.RESOURCE_ALREADY_EXISTS: status.HTTP_409_CONFLICT,
        ErrorCode.BUSINESS_RULE_VIOLATION: status.HTTP_400_BAD_REQUEST,
        ErrorCode.DATABASE_VALIDATION_ERROR: status.HTTP_400_BAD_REQUEST,
        
        # Auth (401-403)
        ErrorCode.AUTHENTICATION_FAILED: status.HTTP_401_UNAUTHORIZED,
        ErrorCode.INVALID_CREDENTIALS: status.HTTP_401_UNAUTHORIZED,
        ErrorCode.TOKEN_EXPIRED: status.HTTP_401_UNAUTHORIZED,
        ErrorCode.TOKEN_INVALID: status.HTTP_401_UNAUTHORIZED,
        ErrorCode.UNAUTHORIZED: status.HTTP_401_UNAUTHORIZED,
        ErrorCode.FORBIDDEN: status.HTTP_403_FORBIDDEN,
        ErrorCode.INSUFFICIENT_PERMISSIONS: status.HTTP_403_FORBIDDEN,
        ErrorCode.INVALID_API_KEY: status.HTTP_401_UNAUTHORIZED,
        
        # Rate Limit (429)
        ErrorCode.IP_RATE_LIMIT_EXCEEDED: status.HTTP_429_TOO_MANY_REQUESTS,
        ErrorCode.USER_RATE_LIMIT_EXCEEDED: status.HTTP_429_TOO_MANY_REQUESTS,
        ErrorCode.API_KEY_MINUTE_RATE_LIMIT_EXCEEDED: status.HTTP_429_TOO_MANY_REQUESTS,
        ErrorCode.API_KEY_HOUR_RATE_LIMIT_EXCEEDED: status.HTTP_429_TOO_MANY_REQUESTS,
        ErrorCode.API_KEY_DAY_RATE_LIMIT_EXCEEDED: status.HTTP_429_TOO_MANY_REQUESTS,
        
        # Database (500/503)
        ErrorCode.DATABASE_CONNECTION_ERROR: status.HTTP_503_SERVICE_UNAVAILABLE,
        ErrorCode.DATABASE_QUERY_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
        ErrorCode.DATABASE_TRANSACTION_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
        ErrorCode.DATABASE_SESSION_ERROR: status.HTTP_503_SERVICE_UNAVAILABLE,
        ErrorCode.DATABASE_ENGINE_ERROR: status.HTTP_503_SERVICE_UNAVAILABLE,
        ErrorCode.DATABASE_CONFIGURATION_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
        
        # External Services (400-504)
        ErrorCode.EXTERNAL_SERVICE_TIMEOUT: status.HTTP_504_GATEWAY_TIMEOUT,
        ErrorCode.EXTERNAL_SERVICE_UNAVAILABLE: status.HTTP_503_SERVICE_UNAVAILABLE,
        ErrorCode.EXTERNAL_SERVICE_CONNECTION_ERROR: status.HTTP_503_SERVICE_UNAVAILABLE,
        ErrorCode.EXTERNAL_SERVICE_REQUEST_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
        ErrorCode.EXTERNAL_SERVICE_RESPONSE_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
        ErrorCode.EXTERNAL_SERVICE_VALIDATION_ERROR: status.HTTP_400_BAD_REQUEST,
        ErrorCode.EXTERNAL_SERVICE_AUTHORIZATION_ERROR: status.HTTP_403_FORBIDDEN,
        ErrorCode.EXTERNAL_SERVICE_RATE_LIMIT_ERROR: status.HTTP_429_TOO_MANY_REQUESTS,
        
        # Internal (500/501)
        ErrorCode.INTERNAL_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
        ErrorCode.NOT_IMPLEMENTED: status.HTTP_501_NOT_IMPLEMENTED,
        
        # Scheduler (500)
        ErrorCode.SCHEDULER_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
        ErrorCode.CONTEXT_CREATION_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
        ErrorCode.PAYLOAD_PREPARATION_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
        ErrorCode.ENGINE_SUBMISSION_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
        ErrorCode.RESULT_PROCESSING_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
        ErrorCode.HANDLER_CONFIGURATION_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
    }
    
    incorrect = []
    for code, expected_status in expected_mappings.items():
        actual_status = ERROR_CODE_TO_HTTP_STATUS.get(code)
        if actual_status != expected_status:
            incorrect.append((code, expected_status, actual_status))
    
    if incorrect:
        print(f"  ❌ INCORRECT MAPPINGS ({len(incorrect)}):")
        for code, expected, actual in incorrect:
            print(f"     - {code.value}: Expected {expected}, Got {actual}")
        assert False, f"Incorrect mappings: {incorrect}"
    else:
        print(f"  ✅ All {len(expected_mappings)} mappings are correct")
    
    print()


def test_exception_inheritance_handling():
    """Test that exception handler handles inheritance correctly."""
    print("=" * 70)
    print("5. EXCEPTION INHERITANCE HANDLING")
    print("=" * 70)
    
    from miniflow.core.exceptions import (
        AppException,
        ValidationError,
        InvalidInputError,
        AuthenticationError,
        AuthenticationFailedError,
        DatabaseError,
        DatabaseConnectionError,
    )
    
    # Test that subclasses are handled by parent handler
    test_cases = [
        (InvalidInputError("test"), AppException),
        (AuthenticationFailedError(), AppException),
        (DatabaseConnectionError(), AppException),
    ]
    
    all_handled = True
    for exception, parent_class in test_cases:
        if not isinstance(exception, parent_class):
            print(f"  ❌ {exception.__class__.__name__} is not instance of {parent_class.__name__}")
            all_handled = False
    
    if all_handled:
        print(f"  ✅ All exception subclasses inherit from AppException")
        print(f"  ✅ Exception handler will catch all via AppException handler")
    else:
        assert False, "Some exceptions are not properly handled"
    
    print()


def main():
    """Run all coverage tests."""
    print("\n" + "=" * 70)
    print("EXCEPTION COVERAGE TEST")
    print("=" * 70)
    print()
    
    tests = [
        ("Error Code Mapping", test_all_error_codes_mapped),
        ("Exception Class Hierarchy", test_all_exception_classes),
        ("Exception Handler Registration", test_exception_handler_registration),
        ("HTTP Status Mapping Accuracy", test_http_status_mapping_accuracy),
        ("Exception Inheritance Handling", test_exception_inheritance_handling),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"  ❌ {name} test crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("=" * 70)
    print("COVERAGE TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    print()
    
    if passed == total:
        print("🎉 Exception handler covers ALL miniflow exceptions!")
        print("✅ All error codes mapped")
        print("✅ All exception classes handled")
        print("✅ All handlers registered")
        print("✅ HTTP status codes correct")
        print("✅ Inheritance handled correctly")
        return 0
    else:
        print(f"⚠️  {total - passed} test(s) failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

