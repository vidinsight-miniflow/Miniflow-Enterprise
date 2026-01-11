from typing import Optional, Dict, Any
from .base import QBitraException


class DatabaseException(QBitraException):
    """Base exception class for database-related errors."""
    pass


class DatabaseConfigurationError(DatabaseException):
    """Raised when there is a database configuration error."""
    
    status_code = 500
    error_code = "DATABASE_CONFIGURATION_ERROR"
    error_message = "Database configuration error"

    def __init__(
        self,
        config_name: Optional[str] = None,
        message: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        if not error_details:
            error_details = {}
        if config_name:
            error_details["config_name"] = config_name
        
        default_message = (
            "The database settings may be incorrect or incomplete. "
            "Please contact system administrator."
        )
        if config_name:
            default_message = f"Database configuration error for '{config_name}'. {default_message}"
        
        super().__init__(
            error_message=message or default_message,
            error_details=error_details,
            cause=cause
        )


class DatabaseValidationError(DatabaseException):
    """Raised when database validation fails (user input error)."""
    
    status_code = 400
    error_code = "DATABASE_VALIDATION_ERROR"
    error_message = "Database validation error"

    def __init__(
        self,
        field_name: Optional[str] = None,
        message: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        if not error_details:
            error_details = {}
        if field_name:
            error_details["field_name"] = field_name
        
        if not message:
            if field_name:
                message = (
                    f"Validation failed for field '{field_name}'. "
                    "Please check the input value and ensure it meets the required criteria."
                )
            else:
                message = (
                    "A validation error occurred. "
                    "Please review your input and ensure all required fields are correctly filled."
                )
        
        super().__init__(
            error_message=message,
            error_details=error_details,
            cause=cause
        )


class DatabaseConnectionError(DatabaseException):
    """Raised when unable to establish a database connection."""
    
    status_code = 503
    error_code = "DATABASE_CONNECTION_ERROR"
    error_message = "Database connection error"

    def __init__(
        self,
        message: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        default_message = (
            "Unable to establish a connection to the database. "
            "The service may be temporarily unavailable. Please try again later."
        )
        
        super().__init__(
            error_message=message or default_message,
            error_details=error_details,
            cause=cause
        )


class DatabaseQueryError(DatabaseException):
    """Raised when a database query operation fails."""
    
    status_code = 500
    error_code = "DATABASE_QUERY_ERROR"
    error_message = "Database query error"

    def __init__(
        self,
        query: Optional[str] = None,
        message: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        if not error_details:
            error_details = {}
        if query:
            error_details["query"] = query
        
        default_message = (
            "A database query operation failed. "
            "This may be due to invalid data or a temporary database issue. "
            "Please try again or contact support if the problem persists."
        )
        
        super().__init__(
            error_message=message or default_message,
            error_details=error_details,
            cause=cause
        )


class DatabaseTransactionError(DatabaseException):
    """Raised when a database transaction fails."""
    
    status_code = 500
    error_code = "DATABASE_TRANSACTION_ERROR"
    error_message = "Database transaction error"

    def __init__(
        self,
        message: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        default_message = (
            "A database transaction failed to complete. "
            "All changes have been rolled back. "
            "Please try again or contact support if the problem persists."
        )
        
        super().__init__(
            error_message=message or default_message,
            error_details=error_details,
            cause=cause
        )


class DatabaseSessionError(DatabaseException):
    """Raised when a database session error occurs."""
    
    status_code = 503
    error_code = "DATABASE_SESSION_ERROR"
    error_message = "Database session error"

    def __init__(
        self,
        message: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        default_message = (
            "A database session error occurred. "
            "The connection may have been lost or timed out. Please try again."
        )
        
        super().__init__(
            error_message=message or default_message,
            error_details=error_details,
            cause=cause
        )


class DatabaseEngineError(DatabaseException):
    """Raised when a database engine error occurs."""
    
    status_code = 503
    error_code = "DATABASE_ENGINE_ERROR"
    error_message = "Database engine error"

    def __init__(
        self,
        message: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        default_message = (
            "A critical database engine error occurred. "
            "The database service may be experiencing issues. Please try again later or contact support."
        )
        
        super().__init__(
            error_message=message or default_message,
            error_details=error_details,
            cause=cause
        )


class DatabaseManagerNotInitializedError(DatabaseException):
    """Raised when DatabaseManager is not initialized."""
    
    status_code = 500
    error_code = "DATABASE_MANAGER_NOT_INITIALIZED_ERROR"
    error_message = "Database manager not initialized"

    def __init__(
        self,
        message: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        default_message = (
            "DatabaseManager has not been initialized. "
            "Please call DatabaseManager().initialize(config) first."
        )
        
        super().__init__(
            error_message=message or default_message,
            error_details=error_details,
            cause=cause
        )


class DatabaseManagerAlreadyInitializedError(DatabaseException):
    """Raised when DatabaseManager is already initialized."""
    
    status_code = 500
    error_code = "DATABASE_MANAGER_ALREADY_INITIALIZED_ERROR"
    error_message = "Database manager already initialized"

    def __init__(
        self,
        message: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        default_message = (
            "DatabaseManager has already been initialized. "
            "Use force_reinitialize=True to reinitialize."
        )
        
        super().__init__(
            error_message=message or default_message,
            error_details=error_details,
            cause=cause
        )


class DatabaseDecoratorManagerError(DatabaseException):
    """Raised when a database decorator manager error occurs."""
    
    status_code = 500
    error_code = "DATABASE_DECORATOR_MANAGER_ERROR"
    error_message = "Database decorator manager error"

    def __init__(
        self,
        decorator_name: Optional[str] = None,
        message: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        if not error_details:
            error_details = {}
        if decorator_name:
            error_details["decorator_name"] = decorator_name
        
        default_message = (
            "DatabaseManager not initialized. "
            "Call DatabaseManager().initialize(config) first."
        )
        if decorator_name:
            default_message = f"Database decorator '{decorator_name}' error: {default_message}"
        
        super().__init__(
            error_message=message or default_message,
            error_details=error_details,
            cause=cause
        )


class DatabaseDecoratorSignatureError(DatabaseException):
    """Raised when a database decorator signature error occurs."""
    
    status_code = 400
    error_code = "DATABASE_DECORATOR_SIGNATURE_ERROR"
    error_message = "Database decorator signature error"

    def __init__(
        self,
        decorator_name: Optional[str] = None,
        function_name: Optional[str] = None,
        expected: Optional[str] = None,
        received: Optional[str] = None,
        message: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        if not error_details:
            error_details = {}
        if decorator_name:
            error_details["decorator_name"] = decorator_name
        if function_name:
            error_details["function_name"] = function_name
        if expected:
            error_details["expected"] = expected
        if received:
            error_details["received"] = received
        
        if not message:
            if decorator_name and function_name:
                message = (
                    f"Function '{function_name}' decorated with '{decorator_name}' "
                    f"does not have the expected signature. "
                    f"Expected: {expected or 'session parameter'}, "
                    f"Received: {received or 'unknown'}."
                )
            else:
                message = (
                    "Database decorator signature error. "
                    "Please check the function signature and ensure it matches the decorator requirements."
                )
        
        super().__init__(
            error_message=message,
            error_details=error_details,
            cause=cause
        )


class DatabaseResourceNotFoundError(DatabaseException):
    """Raised when a database resource is not found."""
    
    status_code = 404
    error_code = "DATABASE_RESOURCE_NOT_FOUND_ERROR"
    error_message = "Database resource not found"

    def __init__(
        self,
        resource_name: Optional[str] = None,
        resource_id: Optional[str] = None,
        message: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        if not error_details:
            error_details = {}
        if resource_name:
            error_details["resource_name"] = resource_name
        if resource_id:
            error_details["resource_id"] = resource_id
        
        if not message:
            if resource_name and resource_id:
                message = (
                    f"Resource '{resource_name}' with ID '{resource_id}' not found. "
                    "Please verify the identifier and try again."
                )
            elif resource_name:
                message = (
                    f"Resource '{resource_name}' not found. "
                    "Please verify the identifier and try again."
                )
            else:
                message = (
                    "The requested resource was not found. "
                    "Please verify the identifier and try again."
                )
        
        super().__init__(
            error_message=message,
            error_details=error_details,
            cause=cause
        )
