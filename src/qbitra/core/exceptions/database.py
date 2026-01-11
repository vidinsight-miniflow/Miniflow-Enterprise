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
