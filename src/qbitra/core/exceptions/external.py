"""
External service exception classes for QBitra.
These exceptions are used for external service errors like Mailtrap, Redis, etc.
"""

from typing import Optional, Dict, Any
from .base import QBitraException


class ExternalServiceException(QBitraException):
    """Base exception class for external service errors."""
    pass


class ExternalServiceConnectionError(ExternalServiceException):
    """Raised when unable to connect to an external service."""
    
    status_code = 503
    error_code = "EXTERNAL_SERVICE_CONNECTION_ERROR"
    error_message = "External service connection error"

    def __init__(
        self,
        service_name: Optional[str] = None,
        operation_name: Optional[str] = None,
        message: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        if not error_details:
            error_details = {}
        if service_name:
            error_details["service_name"] = service_name
        if operation_name:
            error_details["operation_name"] = operation_name
        
        if not message:
            if service_name and operation_name:
                message = (
                    f"Unable to connect to {service_name} service during {operation_name}. "
                    "The service may be temporarily unavailable. Please try again later."
                )
            elif service_name:
                message = (
                    f"Unable to connect to {service_name} service. "
                    "The service may be temporarily unavailable. Please try again later."
                )
            else:
                message = (
                    "Unable to connect to external service. "
                    "The service may be temporarily unavailable. Please try again later."
                )
        
        super().__init__(
            error_message=message,
            error_details=error_details,
            cause=cause
        )


class ExternalServiceTimeoutError(ExternalServiceException):
    """Raised when an external service request times out."""
    
    status_code = 504
    error_code = "EXTERNAL_SERVICE_TIMEOUT_ERROR"
    error_message = "External service timeout error"

    def __init__(
        self,
        service_name: Optional[str] = None,
        operation_name: Optional[str] = None,
        message: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        if not error_details:
            error_details = {}
        if service_name:
            error_details["service_name"] = service_name
        if operation_name:
            error_details["operation_name"] = operation_name
        
        if not message:
            if service_name and operation_name:
                message = (
                    f"Request to {service_name} service timed out during {operation_name}. "
                    "Please try again later."
                )
            elif service_name:
                message = (
                    f"Request to {service_name} service timed out. "
                    "Please try again later."
                )
            else:
                message = (
                    "External service request timed out. "
                    "Please try again later."
                )
        
        super().__init__(
            error_message=message,
            error_details=error_details,
            cause=cause
        )


class ExternalServiceValidationError(ExternalServiceException):
    """Raised when external service rejects request due to validation error."""
    
    status_code = 400
    error_code = "EXTERNAL_SERVICE_VALIDATION_ERROR"
    error_message = "External service validation error"

    def __init__(
        self,
        service_name: Optional[str] = None,
        operation_name: Optional[str] = None,
        message: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        if not error_details:
            error_details = {}
        if service_name:
            error_details["service_name"] = service_name
        if operation_name:
            error_details["operation_name"] = operation_name
        
        if not message:
            if service_name and operation_name:
                message = (
                    f"{service_name} service rejected the request during {operation_name} due to validation error. "
                    "Please check your input and try again."
                )
            elif service_name:
                message = (
                    f"{service_name} service rejected the request due to validation error. "
                    "Please check your input and try again."
                )
            else:
                message = (
                    "External service rejected the request due to validation error. "
                    "Please check your input and try again."
                )
        
        super().__init__(
            error_message=message,
            error_details=error_details,
            cause=cause
        )


class ExternalServiceAuthorizationError(ExternalServiceException):
    """Raised when external service authorization fails."""
    
    status_code = 401
    error_code = "EXTERNAL_SERVICE_AUTHORIZATION_ERROR"
    error_message = "External service authorization error"

    def __init__(
        self,
        service_name: Optional[str] = None,
        operation_name: Optional[str] = None,
        message: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        if not error_details:
            error_details = {}
        if service_name:
            error_details["service_name"] = service_name
        if operation_name:
            error_details["operation_name"] = operation_name
        
        if not message:
            if service_name and operation_name:
                message = (
                    f"Authorization failed for {service_name} service during {operation_name}. "
                    "Please check your API key or credentials."
                )
            elif service_name:
                message = (
                    f"Authorization failed for {service_name} service. "
                    "Please check your API key or credentials."
                )
            else:
                message = (
                    "External service authorization failed. "
                    "Please check your API key or credentials."
                )
        
        super().__init__(
            error_message=message,
            error_details=error_details,
            cause=cause
        )


class ExternalServiceRateLimitError(ExternalServiceException):
    """Raised when external service rate limit is exceeded."""
    
    status_code = 429
    error_code = "EXTERNAL_SERVICE_RATE_LIMIT_ERROR"
    error_message = "External service rate limit error"

    def __init__(
        self,
        service_name: Optional[str] = None,
        operation_name: Optional[str] = None,
        message: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        if not error_details:
            error_details = {}
        if service_name:
            error_details["service_name"] = service_name
        if operation_name:
            error_details["operation_name"] = operation_name
        
        if not message:
            if service_name and operation_name:
                message = (
                    f"Rate limit exceeded for {service_name} service during {operation_name}. "
                    "Please try again later."
                )
            elif service_name:
                message = (
                    f"Rate limit exceeded for {service_name} service. "
                    "Please try again later."
                )
            else:
                message = (
                    "External service rate limit exceeded. "
                    "Please try again later."
                )
        
        super().__init__(
            error_message=message,
            error_details=error_details,
            cause=cause
        )


class ExternalServiceUnavailableError(ExternalServiceException):
    """Raised when external service is unavailable."""
    
    status_code = 503
    error_code = "EXTERNAL_SERVICE_UNAVAILABLE_ERROR"
    error_message = "External service unavailable"

    def __init__(
        self,
        service_name: Optional[str] = None,
        operation_name: Optional[str] = None,
        message: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        if not error_details:
            error_details = {}
        if service_name:
            error_details["service_name"] = service_name
        if operation_name:
            error_details["operation_name"] = operation_name
        
        if not message:
            if service_name and operation_name:
                message = (
                    f"{service_name} service is unavailable during {operation_name}. "
                    "Please try again later."
                )
            elif service_name:
                message = (
                    f"{service_name} service is unavailable. "
                    "Please try again later."
                )
            else:
                message = (
                    "External service is unavailable. "
                    "Please try again later."
                )
        
        super().__init__(
            error_message=message,
            error_details=error_details,
            cause=cause
        )


# MailTrap-specific exceptions
class MailTrapError(ExternalServiceException):
    """Base exception class for MailTrap-specific errors."""
    pass


class MailTrapClientError(MailTrapError):
    """Raised when MailTrap client operations fail (initialization, configuration, etc.)."""
    
    status_code = 500
    error_code = "MAILTRAP_CLIENT_ERROR"
    error_message = "MailTrap client error"

    def __init__(
        self,
        operation: Optional[str] = None,
        message: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        if not error_details:
            error_details = {}
        if operation:
            error_details["operation"] = operation
        
        if not message:
            if operation:
                message = f"MailTrap client error during {operation}. Please check your configuration."
            else:
                message = "MailTrap client error. Please check your configuration."
        
        super().__init__(
            error_message=message,
            error_details=error_details,
            cause=cause
        )


class MailTrapSendError(MailTrapError):
    """Raised when MailTrap email sending fails."""
    
    status_code = 502
    error_code = "MAILTRAP_SEND_ERROR"
    error_message = "MailTrap email send error"

    def __init__(
        self,
        to_email: Optional[str] = None,
        operation: Optional[str] = None,
        message: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        if not error_details:
            error_details = {}
        if to_email:
            error_details["to_email"] = to_email
        if operation:
            error_details["operation"] = operation
        
        if not message:
            if to_email and operation:
                message = f"Failed to send email to {to_email} during {operation}. Please try again or contact support."
            elif to_email:
                message = f"Failed to send email to {to_email}. Please try again or contact support."
            else:
                message = "Failed to send email. Please try again or contact support."
        
        super().__init__(
            error_message=message,
            error_details=error_details,
            cause=cause
        )


# Redis-specific exceptions
class RedisError(ExternalServiceException):
    """Base exception class for Redis-specific errors."""
    pass


class RedisClientError(RedisError):
    """Raised when Redis client operations fail (initialization, configuration, etc.)."""
    
    status_code = 500
    error_code = "REDIS_CLIENT_ERROR"
    error_message = "Redis client error"

    def __init__(
        self,
        operation: Optional[str] = None,
        message: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        if not error_details:
            error_details = {}
        if operation:
            error_details["operation"] = operation
        
        if not message:
            if operation:
                message = f"Redis client error during {operation}. Please check your configuration."
            else:
                message = "Redis client error. Please check your configuration."
        
        super().__init__(
            error_message=message,
            error_details=error_details,
            cause=cause
        )


class RedisOperationError(RedisError):
    """Raised when Redis operation fails."""
    
    status_code = 502
    error_code = "REDIS_OPERATION_ERROR"
    error_message = "Redis operation error"

    def __init__(
        self,
        operation: Optional[str] = None,
        key: Optional[str] = None,
        message: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        if not error_details:
            error_details = {}
        if operation:
            error_details["operation"] = operation
        if key:
            error_details["key"] = key
        
        if not message:
            if operation and key:
                message = f"Redis {operation} operation failed for key '{key}'. Please try again or contact support."
            elif operation:
                message = f"Redis {operation} operation failed. Please try again or contact support."
            else:
                message = "Redis operation failed. Please try again or contact support."
        
        super().__init__(
            error_message=message,
            error_details=error_details,
            cause=cause
        )


# Prometheus-specific exceptions
class PrometheusError(ExternalServiceException):
    """Base exception class for Prometheus-specific errors."""
    pass


class PrometheusClientError(PrometheusError):
    """Raised when Prometheus client operations fail (initialization, configuration, etc.)."""
    
    status_code = 500
    error_code = "PROMETHEUS_CLIENT_ERROR"
    error_message = "Prometheus client error"

    def __init__(
        self,
        operation: Optional[str] = None,
        message: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        if not error_details:
            error_details = {}
        if operation:
            error_details["operation"] = operation
        
        if not message:
            if operation:
                message = f"Prometheus client error during {operation}. Please check your configuration."
            else:
                message = "Prometheus client error. Please check your configuration."
        
        super().__init__(
            error_message=message,
            error_details=error_details,
            cause=cause
        )


class PrometheusMetricError(PrometheusError):
    """Raised when Prometheus metric operations fail."""
    
    status_code = 400
    error_code = "PROMETHEUS_METRIC_ERROR"
    error_message = "Prometheus metric error"

    def __init__(
        self,
        metric_name: Optional[str] = None,
        metric_type: Optional[str] = None,
        operation: Optional[str] = None,
        message: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        if not error_details:
            error_details = {}
        if metric_name:
            error_details["metric_name"] = metric_name
        if metric_type:
            error_details["metric_type"] = metric_type
        if operation:
            error_details["operation"] = operation
        
        if not message:
            if metric_name and operation:
                message = f"Prometheus metric error: {operation} failed for '{metric_name}'. Please verify the metric configuration."
            elif metric_name:
                message = f"Prometheus metric error: '{metric_name}'. Please verify the metric configuration."
            else:
                message = "Prometheus metric error. Please verify the metric configuration."
        
        super().__init__(
            error_message=message,
            error_details=error_details,
            cause=cause
        )
