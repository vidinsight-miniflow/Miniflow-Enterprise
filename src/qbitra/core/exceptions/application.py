"""
Application-level exception classes for QBitra.
These exceptions are used for application-level errors like configuration, environment, etc.
"""

from typing import Optional, Dict, Any
from .base import QBitraException


class ApplicationException(QBitraException):
    """Base exception class for application-level errors."""
    pass


class EnvironmentFileNotFoundError(ApplicationException):
    """Raised when environment file is not found."""
    
    status_code = 404
    error_code = "ENVIRONMENT_FILE_NOT_FOUND_ERROR"
    error_message = "Environment file not found"

    def __init__(
        self,
        file_path: Optional[str] = None,
        message: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        if not error_details:
            error_details = {}
        if file_path:
            error_details["file_path"] = file_path
        
        if not message:
            if file_path:
                message = f"Environment file not found at path: {file_path}"
            else:
                message = "Environment file not found. Please ensure the .env file exists."
        
        super().__init__(
            error_message=message,
            error_details=error_details,
            cause=cause
        )


class EnvironmentTestFailedError(ApplicationException):
    """Raised when environment validation test fails."""
    
    status_code = 500
    error_code = "ENVIRONMENT_TEST_FAILED_ERROR"
    error_message = "Environment validation test failed"

    def __init__(
        self,
        test_key: Optional[str] = None,
        expected_value: Optional[str] = None,
        actual_value: Optional[str] = None,
        message: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        if not error_details:
            error_details = {}
        if test_key:
            error_details["test_key"] = test_key
        if expected_value:
            error_details["expected_value"] = expected_value
        if actual_value:
            error_details["actual_value"] = actual_value
        
        if not message:
            if test_key and expected_value and actual_value:
                message = (
                    f"Environment test failed for key '{test_key}'. "
                    f"Expected: '{expected_value}', Actual: '{actual_value}'"
                )
            else:
                message = (
                    "Environment validation test failed. "
                    "Please check the environment file and ensure all required variables are set correctly."
                )
        
        super().__init__(
            error_message=message,
            error_details=error_details,
            cause=cause
        )


class EnvironmentNotInitializedError(ApplicationException):
    """Raised when environment handler is not initialized."""
    
    status_code = 500
    error_code = "ENVIRONMENT_NOT_INITIALIZED_ERROR"
    error_message = "Environment handler not initialized"

    def __init__(
        self,
        message: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        default_message = (
            "Environment handler has not been initialized. "
            "Please call EnvironmentHandler.init() or EnvironmentHandler.load() first."
        )
        
        super().__init__(
            error_message=message or default_message,
            error_details=error_details,
            cause=cause
        )


class EnvironmentTypeConversionError(ApplicationException):
    """Raised when environment variable type conversion fails."""
    
    status_code = 400
    error_code = "ENVIRONMENT_TYPE_CONVERSION_ERROR"
    error_message = "Environment variable type conversion failed"

    def __init__(
        self,
        key: Optional[str] = None,
        target_type: Optional[str] = None,
        message: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        if not error_details:
            error_details = {}
        if key:
            error_details["key"] = key
        if target_type:
            error_details["target_type"] = target_type
        
        if not message:
            if key and target_type:
                message = (
                    f"Failed to convert environment variable '{key}' to type '{target_type}'. "
                    "Please check the value format and try again."
                )
            elif key:
                message = (
                    f"Failed to convert environment variable '{key}'. "
                    "Please check the value format and try again."
                )
            else:
                message = (
                    "Environment variable type conversion failed. "
                    "Please check the value format and try again."
                )
        
        super().__init__(
            error_message=message,
            error_details=error_details,
            cause=cause
        )


class ConfigurationError(ApplicationException):
    """Base exception class for configuration-related errors."""
    pass


class ConfigurationDirectoryNotFoundError(ApplicationException):
    """Raised when configuration directory is not found."""
    
    status_code = 404
    error_code = "CONFIGURATION_DIRECTORY_NOT_FOUND_ERROR"
    error_message = "Configuration directory not found"

    def __init__(
        self,
        directory_path: Optional[str] = None,
        message: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        if not error_details:
            error_details = {}
        if directory_path:
            error_details["directory_path"] = directory_path
        
        if not message:
            if directory_path:
                message = f"Configuration directory not found at path: {directory_path}"
            else:
                message = "Configuration directory not found. Please ensure the configurations directory exists."
        
        super().__init__(
            error_message=message,
            error_details=error_details,
            cause=cause
        )


class ConfigurationFileNotFoundError(ApplicationException):
    """Raised when configuration file is not found."""
    
    status_code = 404
    error_code = "CONFIGURATION_FILE_NOT_FOUND_ERROR"
    error_message = "Configuration file not found"

    def __init__(
        self,
        file_path: Optional[str] = None,
        message: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        if not error_details:
            error_details = {}
        if file_path:
            error_details["file_path"] = file_path
        
        if not message:
            if file_path:
                message = f"Configuration file not found at path: {file_path}"
            else:
                message = "Configuration file not found. Please ensure the configuration file exists."
        
        super().__init__(
            error_message=message,
            error_details=error_details,
            cause=cause
        )


class ConfigurationInvalidAppEnvError(ApplicationException):
    """Raised when APP_ENV environment variable is invalid or missing."""
    
    status_code = 400
    error_code = "CONFIGURATION_INVALID_APP_ENV_ERROR"
    error_message = "Invalid APP_ENV environment variable"

    def __init__(
        self,
        app_env: Optional[str] = None,
        valid_environments: Optional[list] = None,
        message: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        if not error_details:
            error_details = {}
        if app_env:
            error_details["app_env"] = app_env
        if valid_environments:
            error_details["valid_environments"] = valid_environments
        
        if not message:
            if app_env and valid_environments:
                message = (
                    f"Invalid APP_ENV value: '{app_env}'. "
                    f"Valid values are: {', '.join(valid_environments)}"
                )
            elif app_env:
                message = f"Invalid APP_ENV value: '{app_env}'"
            else:
                message = "APP_ENV environment variable is not set or is invalid."
        
        super().__init__(
            error_message=message,
            error_details=error_details,
            cause=cause
        )


class ConfigurationTestFailedError(ApplicationException):
    """Raised when configuration validation test fails."""
    
    status_code = 500
    error_code = "CONFIGURATION_TEST_FAILED_ERROR"
    error_message = "Configuration validation test failed"

    def __init__(
        self,
        test_section: Optional[str] = None,
        test_key: Optional[str] = None,
        expected_value: Optional[str] = None,
        actual_value: Optional[str] = None,
        message: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        if not error_details:
            error_details = {}
        if test_section:
            error_details["test_section"] = test_section
        if test_key:
            error_details["test_key"] = test_key
        if expected_value:
            error_details["expected_value"] = expected_value
        if actual_value:
            error_details["actual_value"] = actual_value
        
        if not message:
            if test_key and expected_value and actual_value:
                message = (
                    f"Configuration test failed for [{test_section or 'N/A'}] {test_key}. "
                    f"Expected: '{expected_value}', Actual: '{actual_value}'"
                )
            else:
                message = (
                    "Configuration validation test failed. "
                    "Please check the configuration file and ensure all required values are set correctly."
                )
        
        super().__init__(
            error_message=message,
            error_details=error_details,
            cause=cause
        )


class ConfigurationNotInitializedError(ApplicationException):
    """Raised when configuration handler is not initialized."""
    
    status_code = 500
    error_code = "CONFIGURATION_NOT_INITIALIZED_ERROR"
    error_message = "Configuration handler not initialized"

    def __init__(
        self,
        message: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        default_message = (
            "Configuration handler has not been initialized. "
            "Please call ConfigurationHandler.init() or ConfigurationHandler.load() first."
        )
        
        super().__init__(
            error_message=message or default_message,
            error_details=error_details,
            cause=cause
        )


class ConfigurationTypeConversionError(ApplicationException):
    """Raised when configuration value type conversion fails."""
    
    status_code = 400
    error_code = "CONFIGURATION_TYPE_CONVERSION_ERROR"
    error_message = "Configuration value type conversion failed"

    def __init__(
        self,
        section: Optional[str] = None,
        key: Optional[str] = None,
        target_type: Optional[str] = None,
        message: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        if not error_details:
            error_details = {}
        if section:
            error_details["section"] = section
        if key:
            error_details["key"] = key
        if target_type:
            error_details["target_type"] = target_type
        
        if not message:
            if section and key and target_type:
                message = (
                    f"Failed to convert configuration value '[{section}] {key}' to type '{target_type}'. "
                    "Please check the value format and try again."
                )
            elif section and key:
                message = (
                    f"Failed to convert configuration value '[{section}] {key}'. "
                    "Please check the value format and try again."
                )
            else:
                message = (
                    "Configuration value type conversion failed. "
                    "Please check the value format and try again."
                )
        
        super().__init__(
            error_message=message,
            error_details=error_details,
            cause=cause
        )
