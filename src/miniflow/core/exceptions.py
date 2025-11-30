from enum import Enum
from typing import Optional, Dict, Any


class ErrorCode(Enum):
     # Business Logic Errors (400-409) - Kullanıcı hatası
    VALIDATION_ERROR = "VALIDATION_ERROR"                                           # 422
    INVALID_INPUT = "INVALID_INPUT"                                                 # 400
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"                                       # 404
    RESOURCE_ALREADY_EXISTS = "RESOURCE_ALREADY_EXISTS"                             # 409
    BUSINESS_RULE_VIOLATION = "BUSINESS_RULE_VIOLATION"                             # 400

    # Authentication/Authorization Errors (401-403)                     
    AUTHENTICATION_FAILED = "AUTHENTICATION_FAILED"                                 # 401
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"                                     # 401
    TOKEN_EXPIRED = "TOKEN_EXPIRED"                                                 # 401
    TOKEN_INVALID = "TOKEN_INVALID"                                                 # 401
    UNAUTHORIZED = "UNAUTHORIZED"                                                   # 401
    FORBIDDEN = "FORBIDDEN"                                                         # 403
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"                           # 403
    INVALID_API_KEY = "INVALID_API_KEY"                                             # 401   

    # Rate Limiting (429)           
    IP_RATE_LIMIT_EXCEEDED = "IP_RATE_LIMIT_EXCEEDED"                               # 429
    USER_RATE_LIMIT_EXCEEDED = "USER_RATE_LIMIT_EXCEEDED"                           # 429
    API_KEY_MINUTE_RATE_LIMIT_EXCEEDED = "API_KEY_MINUTE_RATE_LIMIT_EXCEEDED"       # 429
    API_KEY_HOUR_RATE_LIMIT_EXCEEDED = "API_KEY_HOUR_RATE_LIMIT_EXCEEDED"           # 429
    API_KEY_DAY_RATE_LIMIT_EXCEEDED = "API_KEY_DAY_RATE_LIMIT_EXCEEDED"             # 429
    
    # Database Errors (500/503)
    DATABASE_CONNECTION_ERROR = "DATABASE_CONNECTION_ERROR"                         # 503
    DATABASE_QUERY_ERROR = "DATABASE_QUERY_ERROR"                                   # 500
    DATABASE_TRANSACTION_ERROR = "DATABASE_TRANSACTION_ERROR"                       # 500
    DATABASE_SESSION_ERROR = "DATABASE_SESSION_ERROR"                               # 503
    DATABASE_ENGINE_ERROR = "DATABASE_ENGINE_ERROR"                                 # 503
    DATABASE_CONFIGURATION_ERROR = "DATABASE_CONFIGURATION_ERROR"                   # 500
    DATABASE_VALIDATION_ERROR = "DATABASE_VALIDATION_ERROR"                         # 400 (kullanıcı hatası)

    # External Service Errors (502/503/504)         
    EXTERNAL_SERVICE_TIMEOUT = "EXTERNAL_SERVICE_TIMEOUT"                           # 504
    EXTERNAL_SERVICE_UNAVAILABLE = "EXTERNAL_SERVICE_UNAVAILABLE"                   # 503
    EXTERNAL_SERVICE_CONNECTION_ERROR = "EXTERNAL_SERVICE_CONNECTION_ERROR"         # 503
    EXTERNAL_SERVICE_REQUEST_ERROR = "EXTERNAL_SERVICE_REQUEST_ERROR"               # 500
    EXTERNAL_SERVICE_RESPONSE_ERROR = "EXTERNAL_SERVICE_RESPONSE_ERROR"             # 500
    EXTERNAL_SERVICE_VALIDATION_ERROR = "EXTERNAL_SERVICE_VALIDATION_ERROR"         # 400
    EXTERNAL_SERVICE_AUTHORIZATION_ERROR = "EXTERNAL_SERVICE_AUTHORIZATION_ERROR"   # 403
    EXTERNAL_SERVICE_RATE_LIMIT_ERROR = "EXTERNAL_SERVICE_RATE_LIMIT_ERROR"         # 429

    # Internal Server Errors (500)          
    INTERNAL_ERROR = "INTERNAL_ERROR"                                               # 500
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"                                             # 501

    # Scheduler Errors (500)
    SCHEDULER_ERROR = "SCHEDULER_ERROR"                                             # 500
    CONTEXT_CREATION_ERROR = "CONTEXT_CREATION_ERROR"                               # 500
    PAYLOAD_PREPARATION_ERROR = "PAYLOAD_PREPARATION_ERROR"                         # 500
    ENGINE_SUBMISSION_ERROR = "ENGINE_SUBMISSION_ERROR"                              # 500
    RESULT_PROCESSING_ERROR = "RESULT_PROCESSING_ERROR"                              # 500
    HANDLER_CONFIGURATION_ERROR = "HANDLER_CONFIGURATION_ERROR"                    # 500




class AppException(Exception):
    def __init__(self, error_code: ErrorCode, error_message: str, error_details: Optional[Dict[str, Any]] = None):
        self.error_code = error_code
        self.error_message = error_message
        self.error_details = error_details
        super().__init__(self.error_message)

    def __str__(self):
        return f"Message: {self.error_message}"

    def to_dict(self):
        return {
            "error_code": self.error_code.value,
            "error_message": self.error_message,
            "error_details": self.error_details
        }

class InternalError(AppException):
    def __init__(self, component_name: str, message: str = None, error_details: Optional[Dict[str, Any]] = None):
        self.component_name = component_name
        self.error_details = error_details
        message = message or f"An internal server error occurred in the {component_name} component. Our team has been notified. Please try again later or contact support if the issue persists."
        super().__init__(ErrorCode.INTERNAL_ERROR, message, error_details=error_details)

class NotImplementedError(AppException):
    def __init__(self, component_name: str, feature_name: str, message: str = None, error_details: Optional[Dict[str, Any]] = None):
        self.component_name = component_name
        self.feature_name = feature_name
        self.error_details = error_details
        message = message or f"The requested feature '{feature_name}' in component '{component_name}' is not yet implemented. This functionality may be available in a future update."
        super().__init__(ErrorCode.NOT_IMPLEMENTED, message, error_details=error_details)


class ValidationError(AppException):
    """Validation errors"""
    pass

class InvalidInputError(ValidationError):
    def __init__(self, field_name: str, message: str = None):
        self.field_name = field_name
        message = message or f"The provided value for '{field_name}' is invalid. Please check the input format and try again."
        super().__init__(ErrorCode.INVALID_INPUT, message, error_details={"field_name": field_name})

class ResourceNotFoundError(ValidationError):
    def __init__(self, resource_name: str, message: str = None, resource_id: str = None):
        self.resource_name = resource_name
        resource_id_text = f" with ID '{resource_id}'" if resource_id else ""
        message = message or f"The requested {resource_name}{resource_id_text} could not be found. Please verify the identifier and try again."
        super().__init__(ErrorCode.RESOURCE_NOT_FOUND, message, error_details={"resource_name": resource_name, "resource_id": resource_id})

class ResourceAlreadyExistsError(ValidationError):
    def __init__(self, resource_name: str, message: str = None, conflicting_field: str = None):
        self.resource_name = resource_name
        field_text = f" with the same {conflicting_field}" if conflicting_field else ""
        message = message or f"A {resource_name}{field_text} already exists. Please use a different value or update the existing resource."
        super().__init__(ErrorCode.RESOURCE_ALREADY_EXISTS, message, error_details={"resource_name": resource_name, "conflicting_field": conflicting_field})

class BusinessRuleViolationError(ValidationError):
    def __init__(self, rule_name: str, rule_detail: str, message: str = None):
        self.rule_name = rule_name
        self.rule_detail = rule_detail
        detail_text = f": {rule_detail}" if rule_detail else ""
        message = message or f"Business rule violation for '{rule_name}'{detail_text}. Please review the requirements and try again."
        super().__init__(ErrorCode.BUSINESS_RULE_VIOLATION, message, error_details={"rule_name": rule_name, "rule_detail": rule_detail})



class AuthenticationError(AppException):
    """Authentication errors"""
    pass

class AuthenticationFailedError(AuthenticationError):
    def __init__(self, message: str = None):
        message = message or "Authentication failed. Please check your credentials and try again."
        super().__init__(ErrorCode.AUTHENTICATION_FAILED, message)

class InvalidCredentialsError(AuthenticationError):
    def __init__(self, message: str = None):
        message = message or "The provided credentials are incorrect. Please verify your email/username and password, then try again."
        super().__init__(ErrorCode.INVALID_CREDENTIALS, message)

class TokenExpiredError(AuthenticationError):
    def __init__(self, token_type: str = None, message: str = None):
        token_type_text = f" ({token_type})" if token_type else ""
        message = message or f"Your authentication token{token_type_text} has expired. Please log in again to obtain a new token."
        super().__init__(ErrorCode.TOKEN_EXPIRED, message, error_details={"token_type": token_type} if token_type else None)

class TokenInvalidError(AuthenticationError):
    def __init__(self, token_type: str = None, message: str = None):
        token_type_text = f" ({token_type})" if token_type else ""
        message = message or f"The provided authentication token{token_type_text} is invalid or malformed. Please log in again to obtain a valid token."
        super().__init__(ErrorCode.TOKEN_INVALID, message, error_details={"token_type": token_type} if token_type else None)

class UnauthorizedError(AuthenticationError):
    def __init__(self, resource_type: str, resource_id: str, message: str = None):
        self.resource_type = resource_type
        self.resource_id = resource_id
        message = message or f"Unauthorized access attempt to {resource_type} (ID: {resource_id}). Please authenticate with valid credentials to access this resource."
        super().__init__(ErrorCode.UNAUTHORIZED, message, error_details={"resource_type": resource_type, "resource_id": resource_id})

class ForbiddenError(AuthenticationError):
    def __init__(self, resource_type: str = None, resource_id: str = None, message: str = None):
        self.resource_type = resource_type
        self.resource_id = resource_id
        resource_text = f" to {resource_type}" + (f" (ID: {resource_id})" if resource_id else "") if resource_type else ""
        message = message or f"Access forbidden{resource_text}. You do not have permission to perform this action."
        super().__init__(ErrorCode.FORBIDDEN, message, error_details={"resource_type": resource_type, "resource_id": resource_id} if resource_type else None)

class InsufficientPermissionsError(AuthenticationError):
    def __init__(self, resource_type: str, resource_id: str, message: str = None, required_permission: str = None):
        self.resource_type = resource_type
        self.resource_id = resource_id
        permission_text = f" (Required: {required_permission})" if required_permission else ""
        message = message or f"Insufficient permissions to access {resource_type} (ID: {resource_id}){permission_text}. Please contact your administrator for access."
        super().__init__(ErrorCode.INSUFFICIENT_PERMISSIONS, message, error_details={"resource_type": resource_type, "resource_id": resource_id, "required_permission": required_permission})

class InvalidApiKeyError(AuthenticationError):
    def __init__(self, message: str = None):
        message = message or "The provided API key is invalid or has been revoked. Please verify your API key and try again."
        super().__init__(ErrorCode.INVALID_API_KEY, message)


class RateLimitError(AppException):
    """Rate limit errors"""
    pass

class IpRateLimitExceededError(RateLimitError):
    def __init__(self, message: str = None, retry_after: int = None):
        retry_text = f" Please try again after {retry_after} seconds." if retry_after else " Please try again later."
        message = message or f"Rate limit exceeded for your IP address.{retry_text}"
        super().__init__(ErrorCode.IP_RATE_LIMIT_EXCEEDED, message, error_details={"retry_after": retry_after} if retry_after else None)

class UserRateLimitExceededError(RateLimitError):
    def __init__(self, reset_time: str = None, message: str = None):
        reset_text = f" Rate limit will reset at {reset_time}." if reset_time else " Please try again later."
        message = message or f"You have exceeded the allowed number of requests for your account.{reset_text}"
        super().__init__(ErrorCode.USER_RATE_LIMIT_EXCEEDED, message, error_details={"reset_time": reset_time} if reset_time else None)

class ApiKeyMinuteRateLimitExceededError(RateLimitError):
    def __init__(self, reset_time: str = None, message: str = None):
        reset_text = f" Rate limit will reset at {reset_time}." if reset_time else " Please try again in the next minute."
        message = message or f"Your API key has exceeded the per-minute rate limit.{reset_text}"
        super().__init__(ErrorCode.API_KEY_MINUTE_RATE_LIMIT_EXCEEDED, message, error_details={"reset_time": reset_time} if reset_time else None)

class ApiKeyHourRateLimitExceededError(RateLimitError):
    def __init__(self, reset_time: str = None, message: str = None):
        reset_text = f" Rate limit will reset at {reset_time}." if reset_time else " Please try again in the next hour."
        message = message or f"Your API key has exceeded the per-hour rate limit.{reset_text}"
        super().__init__(ErrorCode.API_KEY_HOUR_RATE_LIMIT_EXCEEDED, message, error_details={"reset_time": reset_time} if reset_time else None)

class ApiKeyDayRateLimitExceededError(RateLimitError):
    def __init__(self, reset_time: str = None, message: str = None):
        reset_text = f" Rate limit will reset at {reset_time}." if reset_time else " Please try again tomorrow."
        message = message or f"Your API key has exceeded the daily rate limit.{reset_text}"
        super().__init__(ErrorCode.API_KEY_DAY_RATE_LIMIT_EXCEEDED, message, error_details={"reset_time": reset_time} if reset_time else None)

        
class DatabaseError(AppException):
    """Veritabanı hataları için özel exception"""
    pass

class DatabaseConnectionError(DatabaseError):
    def __init__(self, message: str = None):
        message = message or "Unable to establish a connection to the database. The service may be temporarily unavailable. Please try again later."
        super().__init__(ErrorCode.DATABASE_CONNECTION_ERROR, message)

class DatabaseQueryError(DatabaseError):
    def __init__(self, message: str = None):
        message = message or "A database query operation failed. This may be due to invalid data or a temporary database issue. Please try again or contact support if the problem persists."
        super().__init__(ErrorCode.DATABASE_QUERY_ERROR, message)

class DatabaseTransactionError(DatabaseError):
    def __init__(self, message: str = None):
        message = message or "A database transaction failed to complete. All changes have been rolled back. Please try again or contact support if the problem persists."
        super().__init__(ErrorCode.DATABASE_TRANSACTION_ERROR, message)

class DatabaseSessionError(DatabaseError):
    def __init__(self, message: str = None):
        message = message or "A database session error occurred. The connection may have been lost or timed out. Please try again."
        super().__init__(ErrorCode.DATABASE_SESSION_ERROR, message)

class DatabaseEngineError(DatabaseError):
    def __init__(self, message: str = None):
        message = message or "A critical database engine error occurred. The database service may be experiencing issues. Please try again later or contact support."
        super().__init__(ErrorCode.DATABASE_ENGINE_ERROR, message)

class DatabaseConfigurationError(DatabaseError):
    def __init__(self, config_name: Dict[str, Any], message: str = None):
        self.config_name = config_name
        message = message or "A database configuration error was detected. The database settings may be incorrect or incomplete. Please contact system administrator."
        super().__init__(ErrorCode.DATABASE_CONFIGURATION_ERROR, message, error_details={"config_name": config_name})

class DatabaseValidationError(ValidationError):
    """Database validation error - Kullanıcı hatası (400)"""
    def __init__(self, message: str = None, error_message: str = None, field_name: str = None):
        if not message and not error_message:
            if field_name:
                message = f"Validation failed for field '{field_name}'. Please check the input value and ensure it meets the required criteria."
            else:
                message = "A validation error occurred. Please review your input and ensure all required fields are correctly filled."
        else:
            message = message or error_message
        super(ValidationError, self).__init__(ErrorCode.DATABASE_VALIDATION_ERROR, message, error_details={"field_name": field_name} if field_name else None)
        

class ExternalServiceError(AppException):
    """External service errors"""
    pass

class ExternalServiceTimeoutError(ExternalServiceError):
    def __init__(self, service_name: str, operation_name: str, original_error: Exception, message: str = None):
        self.service_name = service_name
        self.operation_name = operation_name
        self.original_error = original_error
        message = message or f"The external service '{service_name}' did not respond in time while executing '{operation_name}'. The service may be experiencing high load. Please try again later."
        super().__init__(ErrorCode.EXTERNAL_SERVICE_TIMEOUT, message, error_details={"service_name": service_name, "operation_name": operation_name, "original_error": original_error})

class ExternalServiceUnavailableError(ExternalServiceError):
    def __init__(self, service_name: str, operation_name: str, original_error: Exception, message: str = None):
        self.service_name = service_name
        self.operation_name = operation_name
        self.original_error = original_error
        message = message or f"The external service '{service_name}' is currently unavailable for operation '{operation_name}'. The service may be undergoing maintenance. Please try again later."
        super().__init__(ErrorCode.EXTERNAL_SERVICE_UNAVAILABLE, message, error_details={"service_name": service_name, "operation_name": operation_name, "original_error": original_error})

class ExternalServiceConnectionError(ExternalServiceError):
    def __init__(self, service_name: str, operation_name: str, original_error: Exception, message: str = None):
        self.service_name = service_name
        self.operation_name = operation_name
        self.original_error = original_error
        message = message or f"Unable to establish a connection to the external service '{service_name}' for operation '{operation_name}'. Please check your network connection and try again."
        super().__init__(ErrorCode.EXTERNAL_SERVICE_CONNECTION_ERROR, message, error_details={"service_name": service_name, "operation_name": operation_name, "original_error": original_error})

class ExternalServiceRequestError(ExternalServiceError):
    def __init__(self, service_name: str, operation_name: str, original_error: Exception, message: str = None):
        self.service_name = service_name
        self.operation_name = operation_name
        self.original_error = original_error
        message = message or f"An error occurred while sending a request to the external service '{service_name}' for operation '{operation_name}'. The request may be malformed or the service may have rejected it. Please verify your request parameters."
        super().__init__(ErrorCode.EXTERNAL_SERVICE_REQUEST_ERROR, message, error_details={"service_name": service_name, "operation_name": operation_name, "original_error": original_error})

class ExternalServiceResponseError(ExternalServiceError):
    def __init__(self, service_name: str, operation_name: str, original_error: Exception, message: str = None):
        self.service_name = service_name
        self.operation_name = operation_name
        self.original_error = original_error
        message = message or f"The external service '{service_name}' returned an invalid or unexpected response for operation '{operation_name}'. The service may be experiencing issues. Please try again later or contact support."
        super().__init__(ErrorCode.EXTERNAL_SERVICE_RESPONSE_ERROR, message, error_details={"service_name": service_name, "operation_name": operation_name, "original_error": original_error})

class ExternalServiceValidationError(ExternalServiceError):
    def __init__(self, service_name: str, operation_name: str, original_error: Exception, message: str = None):
        self.service_name = service_name
        self.operation_name = operation_name
        self.original_error = original_error
        message = message or f"The external service '{service_name}' rejected the request for operation '{operation_name}' due to validation errors. Please check your input parameters and ensure they meet the service requirements."
        super().__init__(ErrorCode.EXTERNAL_SERVICE_VALIDATION_ERROR, message, error_details={"service_name": service_name, "operation_name": operation_name, "original_error": original_error})

class ExternalServiceAuthorizationError(ExternalServiceError):
    def __init__(self, service_name: str, operation_name: str, original_error: Exception, message: str = None):
        self.service_name = service_name
        self.operation_name = operation_name
        self.original_error = original_error
        message = message or f"The external service '{service_name}' denied access to operation '{operation_name}' due to authorization failure. Please verify your API credentials and permissions."
        super().__init__(ErrorCode.EXTERNAL_SERVICE_AUTHORIZATION_ERROR, message, error_details={"service_name": service_name, "operation_name": operation_name, "original_error": original_error})

class ExternalServiceRateLimitError(ExternalServiceError):
    def __init__(self, service_name: str, operation_name: str, original_error: Exception, message: str = None):
        self.service_name = service_name
        self.operation_name = operation_name
        self.original_error = original_error
        message = message or f"The external service '{service_name}' has rate-limited requests for operation '{operation_name}'. Please reduce your request frequency and try again later."
        super().__init__(ErrorCode.EXTERNAL_SERVICE_RATE_LIMIT_ERROR, message, error_details={"service_name": service_name, "operation_name": operation_name, "original_error": original_error})


class SchedulerError(AppException):
    """Scheduler errors"""
    pass


class ContextCreationError(SchedulerError):
    def __init__(self, execution_input_id: str, original_error: Exception = None, message: str = None):
        self.execution_input_id = execution_input_id
        self.original_error = original_error
        message = message or f"Failed to create execution context for execution input '{execution_input_id}'. The input may be invalid or the service may be experiencing issues."
        error_details = {"execution_input_id": execution_input_id}
        if original_error:
            error_details["original_error"] = str(original_error)
        super().__init__(ErrorCode.CONTEXT_CREATION_ERROR, message, error_details=error_details)


class PayloadPreparationError(SchedulerError):
    def __init__(self, execution_input_id: str, reason: str = None, original_error: Exception = None, message: str = None):
        self.execution_input_id = execution_input_id
        self.reason = reason
        self.original_error = original_error
        reason_text = f": {reason}" if reason else ""
        message = message or f"Failed to prepare payload for execution input '{execution_input_id}'{reason_text}. The input data may be invalid or incomplete."
        error_details = {"execution_input_id": execution_input_id}
        if reason:
            error_details["reason"] = reason
        if original_error:
            error_details["original_error"] = str(original_error)
        super().__init__(ErrorCode.PAYLOAD_PREPARATION_ERROR, message, error_details=error_details)


class EngineSubmissionError(SchedulerError):
    def __init__(self, payload_count: int, attempt: int = None, original_error: Exception = None, message: str = None):
        self.payload_count = payload_count
        self.attempt = attempt
        self.original_error = original_error
        attempt_text = f" (attempt {attempt})" if attempt else ""
        message = message or f"Failed to submit {payload_count} payload(s) to execution engine{attempt_text}. The engine may be unavailable or overloaded."
        error_details = {"payload_count": payload_count}
        if attempt:
            error_details["attempt"] = attempt
        if original_error:
            error_details["original_error"] = str(original_error)
        super().__init__(ErrorCode.ENGINE_SUBMISSION_ERROR, message, error_details=error_details)


class ResultProcessingError(SchedulerError):
    def __init__(self, execution_id: str = None, node_id: str = None, attempt: int = None, original_error: Exception = None, message: str = None):
        self.execution_id = execution_id
        self.node_id = node_id
        self.attempt = attempt
        self.original_error = original_error
        ids_text = ""
        if execution_id and node_id:
            ids_text = f" for execution '{execution_id}', node '{node_id}'"
        elif execution_id:
            ids_text = f" for execution '{execution_id}'"
        attempt_text = f" (attempt {attempt})" if attempt else ""
        message = message or f"Failed to process execution result{ids_text}{attempt_text}. The result data may be invalid or the service may be experiencing issues."
        error_details = {}
        if execution_id:
            error_details["execution_id"] = execution_id
        if node_id:
            error_details["node_id"] = node_id
        if attempt:
            error_details["attempt"] = attempt
        if original_error:
            error_details["original_error"] = str(original_error)
        super().__init__(ErrorCode.RESULT_PROCESSING_ERROR, message, error_details=error_details)


class HandlerConfigurationError(SchedulerError):
    def __init__(self, handler_name: str, config_key: str = None, original_error: Exception = None, message: str = None):
        self.handler_name = handler_name
        self.config_key = config_key
        self.original_error = original_error
        key_text = f" (key: '{config_key}')" if config_key else ""
        message = message or f"Failed to load configuration for handler '{handler_name}'{key_text}. Using default values."
        error_details = {"handler_name": handler_name}
        if config_key:
            error_details["config_key"] = config_key
        if original_error:
            error_details["original_error"] = str(original_error)
        super().__init__(ErrorCode.HANDLER_CONFIGURATION_ERROR, message, error_details=error_details)