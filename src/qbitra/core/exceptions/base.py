from typing import Optional, Dict, Any


class QBitraException(Exception):
    """Base exception class for QBitra application errors."""
    
    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"
    error_message: str = "An internal server error occurred"
    error_details: Optional[Dict[str, Any]] = None

    def __init__(
        self, 
        status_code: Optional[int] = None, 
        error_code: Optional[str] = None, 
        error_message: Optional[str] = None, 
        error_details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        # Use provided values or fall back to class defaults
        self.status_code = status_code if status_code is not None else self.__class__.status_code
        self.error_code = error_code if error_code is not None else self.__class__.error_code
        self.error_message = error_message if error_message is not None else self.__class__.error_message
        self.error_details = error_details if error_details is not None else {}
        self.cause = cause

        super().__init__(self.error_message)

        # Add cause information if provided (Python 3.11+ compatible)
        if cause:
            self.error_details["cause"] = str(cause)
            self.error_details["cause_type"] = type(cause).__name__


    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        result = {
            "status_code": self.status_code,
            "error_code": self.error_code,
            "error_message": self.error_message,
        }
        
        if self.error_details:
            result["error_details"] = self.error_details
        
        return result