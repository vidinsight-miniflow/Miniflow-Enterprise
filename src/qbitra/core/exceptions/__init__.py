"""
QBitra Exception Classes
========================

This module provides exception classes for the QBitra application.
All exceptions inherit from QBitraException base class.
"""

from .base import QBitraException
from .database import (
    DatabaseException,
    DatabaseConfigurationError,
    DatabaseValidationError,
    DatabaseConnectionError,
    DatabaseQueryError,
    DatabaseTransactionError,
    DatabaseSessionError,
    DatabaseEngineError,
    DatabaseManagerNotInitializedError,
    DatabaseManagerAlreadyInitializedError,
    DatabaseDecoratorManagerError,
    DatabaseDecoratorSignatureError,
    DatabaseResourceNotFoundError,
)
from .application import (
    ApplicationException,
    EnvironmentFileNotFoundError,
    EnvironmentTestFailedError,
    EnvironmentNotInitializedError,
    EnvironmentTypeConversionError,
    ConfigurationError,
    ConfigurationDirectoryNotFoundError,
    ConfigurationFileNotFoundError,
    ConfigurationInvalidAppEnvError,
    ConfigurationTestFailedError,
    ConfigurationNotInitializedError,
    ConfigurationTypeConversionError,
)
from .external import (
    ExternalServiceException,
    ExternalServiceConnectionError,
    ExternalServiceTimeoutError,
    ExternalServiceValidationError,
    ExternalServiceAuthorizationError,
    ExternalServiceRateLimitError,
    ExternalServiceUnavailableError,
    MailTrapError,
    MailTrapClientError,
    MailTrapSendError,
    RedisError,
    RedisClientError,
    RedisOperationError,
    PrometheusError,
    PrometheusClientError,
    PrometheusMetricError,
)

__all__ = [
    # Base exception
    "QBitraException",
    # Database exceptions
    "DatabaseException",
    "DatabaseConfigurationError",
    "DatabaseValidationError",
    "DatabaseConnectionError",
    "DatabaseQueryError",
    "DatabaseTransactionError",
    "DatabaseSessionError",
    "DatabaseEngineError",
    "DatabaseManagerNotInitializedError",
    "DatabaseManagerAlreadyInitializedError",
    "DatabaseDecoratorManagerError",
    "DatabaseDecoratorSignatureError",
    "DatabaseResourceNotFoundError",
    # Application exceptions
    "ApplicationException",
    # Environment exceptions
    "EnvironmentFileNotFoundError",
    "EnvironmentTestFailedError",
    "EnvironmentNotInitializedError",
    "EnvironmentTypeConversionError",
    # Configuration exceptions
    "ConfigurationError",
    "ConfigurationDirectoryNotFoundError",
    "ConfigurationFileNotFoundError",
    "ConfigurationInvalidAppEnvError",
    "ConfigurationTestFailedError",
    "ConfigurationNotInitializedError",
    "ConfigurationTypeConversionError",
    # External service exceptions
    "ExternalServiceException",
    "ExternalServiceConnectionError",
    "ExternalServiceTimeoutError",
    "ExternalServiceValidationError",
    "ExternalServiceAuthorizationError",
    "ExternalServiceRateLimitError",
    "ExternalServiceUnavailableError",
    # MailTrap exceptions
    "MailTrapError",
    "MailTrapClientError",
    "MailTrapSendError",
    # Redis exceptions
    "RedisError",
    "RedisClientError",
    "RedisOperationError",
    # Prometheus exceptions
    "PrometheusError",
    "PrometheusClientError",
    "PrometheusMetricError",
]
