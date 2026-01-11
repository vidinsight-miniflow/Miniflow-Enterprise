import mailtrap as mt
from typing import List, Optional, Dict, Any

from miniflow.utils.handlers import EnvironmentHandler, ConfigurationHandler
from miniflow.core.exceptions import (
    InternalError,
    InvalidInputError,
    ExternalServiceConnectionError,
    ExternalServiceTimeoutError,
    ExternalServiceRequestError,
    ExternalServiceValidationError,
    ExternalServiceAuthorizationError,
    ExternalServiceRateLimitError,
    ExternalServiceUnavailableError
)


class MailTrapClient:
    """
    Mailtrap client handler for sending emails via Mailtrap API.
    
    Supports both template-based and custom HTML email sending.
    Uses lazy loading pattern for configuration and client initialization.
    """
    _api_key: Optional[str] = None
    _sender_email: Optional[str] = None
    _sender_name: Optional[str] = None

    _welcome_template_id: Optional[str] = None
    _verification_template_id: Optional[str] = None
    _password_reset_template_id: Optional[str] = None
    _notification_template_id: Optional[str] = None

    _client: Optional[mt.MailtrapClient] = None
    _initialized: bool = False


    @classmethod
    def initialize(cls):
        """
        Initialize Mailtrap client with configuration.
        Uses lazy loading - only initializes once.
        """
        if cls._initialized:
            return
        
        try:
            cls._load_mailtrap_configurations()
        except Exception as e:
            raise InternalError(
                component_name="mailtrap_client",
                message=f"Failed to initialize Mailtrap client: {str(e)}",
                error_details={
                    "error_type": type(e).__name__,
                    "original_error": str(e)
                }
            )

    @classmethod
    def _load_mailtrap_configurations(cls):
        """Load Mailtrap configuration from environment and config files."""
        ConfigurationHandler.load_config()

        cls._api_key = EnvironmentHandler.get("MAILTRAP_API_KEY")
        cls._sender_email = ConfigurationHandler.get("Mailtrap", "sender_email", fallback="")
        cls._sender_name = ConfigurationHandler.get("Mailtrap", "sender_name", fallback="")

        cls._welcome_template_id = ConfigurationHandler.get("Mailtrap", "welcome_template_id", fallback="")
        cls._verification_template_id = ConfigurationHandler.get("Mailtrap", "verification_template_id", fallback="")
        cls._password_reset_template_id = ConfigurationHandler.get("Mailtrap", "password_reset_template_id", fallback="")
        cls._notification_template_id = ConfigurationHandler.get("Mailtrap", "notification_template_id", fallback="")

        if not cls._api_key:
            raise InternalError(
                component_name="mailtrap_client",
                message="MAILTRAP_API_KEY environment variable is not set",
                error_details={
                    "required_variable": "MAILTRAP_API_KEY"
                }
            )

        cls._client = mt.MailtrapClient(token=cls._api_key)
        cls._initialized = True

    @classmethod
    def _ensure_initialized(cls):
        """Ensure client is initialized before use (lazy loading)."""
        if not cls._initialized:
            cls.initialize()

    @classmethod
    def send_template_email(
        cls,
        to_email: str,
        template_uuid: str,
        template_variables: Dict[str, Any],
        category: str = "General",
    ) -> Dict[str, Any]:
        """
        Send email using Mailtrap template.
        
        Args:
            to_email: Recipient email address
            template_uuid: Mailtrap template UUID
            template_variables: Dictionary of template variables
            category: Email category (default: "General")
        
        Returns:
            Dict with success status, response, and email details
        
        Raises:
            InternalError: If client not initialized
            InvalidInputError: If template_uuid is empty
            ExternalServiceTimeoutError: If Mailtrap service times out
            ExternalServiceConnectionError: If connection to Mailtrap fails
            ExternalServiceRequestError: If request to Mailtrap fails
            ExternalServiceValidationError: If Mailtrap rejects request due to validation
            ExternalServiceAuthorizationError: If API key is invalid
            ExternalServiceRateLimitError: If rate limit exceeded
            ExternalServiceUnavailableError: If Mailtrap service is unavailable
        """
        cls._ensure_initialized()
        
        if not cls._client:
            raise InternalError(
                component_name="mailtrap_client",
                message="Mailtrap client not initialized"
            )
        
        if not template_uuid:
            raise InvalidInputError(
                field_name="template_uuid",
                message="Template UUID is required"
            )
        
        try:
            mail = mt.MailFromTemplate(
                sender=mt.Address(email=cls._sender_email, name=cls._sender_name),
                to=[mt.Address(email=to_email)],
                template_uuid=template_uuid,
                template_variables=template_variables,
                category=category
            )

            response = cls._client.send(mail)

            return response
            
        except TimeoutError as e:
            raise ExternalServiceTimeoutError(
                service_name="Mailtrap",
                operation_name="send_template_email",
                original_error=e
            )
        except ConnectionError as e:
            raise ExternalServiceConnectionError(
                service_name="Mailtrap",
                operation_name="send_template_email",
                original_error=e
            )
        except ValueError as e:
            # Validation errors from mailtrap library
            raise ExternalServiceValidationError(
                service_name="Mailtrap",
                operation_name="send_template_email",
                original_error=e
            )
        except Exception as e:
            error_str = str(e).lower()
            if "timeout" in error_str or "timed out" in error_str:
                raise ExternalServiceTimeoutError(
                    service_name="Mailtrap",
                    operation_name="send_template_email",
                    original_error=e
                )
            elif "connection" in error_str or "connect" in error_str:
                raise ExternalServiceConnectionError(
                    service_name="Mailtrap",
                    operation_name="send_template_email",
                    original_error=e
                )
            elif "unauthorized" in error_str or "auth" in error_str or "401" in error_str:
                raise ExternalServiceAuthorizationError(
                    service_name="Mailtrap",
                    operation_name="send_template_email",
                    original_error=e
                )
            elif "rate limit" in error_str or "429" in error_str:
                raise ExternalServiceRateLimitError(
                    service_name="Mailtrap",
                    operation_name="send_template_email",
                    original_error=e
                )
            elif "unavailable" in error_str or "503" in error_str:
                raise ExternalServiceUnavailableError(
                    service_name="Mailtrap",
                    operation_name="send_template_email",
                    original_error=e
                )
            elif "validation" in error_str or "invalid" in error_str or "400" in error_str:
                raise ExternalServiceValidationError(
                    service_name="Mailtrap",
                    operation_name="send_template_email",
                    original_error=e
                )
            else:
                # Generic request/response error
                raise ExternalServiceRequestError(
                    service_name="Mailtrap",
                    operation_name="send_template_email",
                    original_error=e
                )

    @classmethod
    def send_email(
        cls,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        category: str = "General",
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Send custom HTML email (without template).
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML content of the email
            text_content: Optional plain text content
            category: Email category (default: "General")
            cc: Optional list of CC email addresses
            bcc: Optional list of BCC email addresses
        
        Returns:
            Dict with success status, response, and email details
        
        Raises:
            InternalError: If client not initialized
            InvalidInputError: If to_email is empty
            ExternalServiceTimeoutError: If Mailtrap service times out
            ExternalServiceConnectionError: If connection to Mailtrap fails
            ExternalServiceRequestError: If request to Mailtrap fails
            ExternalServiceValidationError: If Mailtrap rejects request due to validation
            ExternalServiceAuthorizationError: If API key is invalid
            ExternalServiceRateLimitError: If rate limit exceeded
            ExternalServiceUnavailableError: If Mailtrap service is unavailable
        """
        cls._ensure_initialized()
        
        if not cls._client:
            raise InternalError(
                component_name="mailtrap_client",
                message="Mailtrap client not initialized"
            )
        
        if not to_email:
            raise InvalidInputError(
                field_name="to_email",
                message="Recipient email address is required"
            )
        
        try:
            # Prepare recipient lists
            to_addresses = [mt.Address(email=to_email)]
            cc_addresses = [mt.Address(email=email) for email in (cc or [])]
            bcc_addresses = [mt.Address(email=email) for email in (bcc or [])]
            
            # Create mail object
            mail = mt.Mail(
                sender=mt.Address(email=cls._sender_email, name=cls._sender_name),
                to=to_addresses,
                subject=subject,
                text=text_content or "",
                html=html_content,
                category=category
            )
            
            if cc_addresses:
                mail.cc = cc_addresses
            if bcc_addresses:
                mail.bcc = bcc_addresses
            
            # Send email
            response = cls._client.send(mail)

            return response
            
        except TimeoutError as e:
            raise ExternalServiceTimeoutError(
                service_name="Mailtrap",
                operation_name="send_email",
                original_error=e
            )
        except ConnectionError as e:
            raise ExternalServiceConnectionError(
                service_name="Mailtrap",
                operation_name="send_email",
                original_error=e
            )
        except ValueError as e:
            # Validation errors from mailtrap library
            raise ExternalServiceValidationError(
                service_name="Mailtrap",
                operation_name="send_email",
                original_error=e
            )
        except Exception as e:
            error_str = str(e).lower()
            if "timeout" in error_str or "timed out" in error_str:
                raise ExternalServiceTimeoutError(
                    service_name="Mailtrap",
                    operation_name="send_email",
                    original_error=e
                )
            elif "connection" in error_str or "connect" in error_str:
                raise ExternalServiceConnectionError(
                    service_name="Mailtrap",
                    operation_name="send_email",
                    original_error=e
                )
            elif "unauthorized" in error_str or "auth" in error_str or "401" in error_str:
                raise ExternalServiceAuthorizationError(
                    service_name="Mailtrap",
                    operation_name="send_email",
                    original_error=e
                )
            elif "rate limit" in error_str or "429" in error_str:
                raise ExternalServiceRateLimitError(
                    service_name="Mailtrap",
                    operation_name="send_email",
                    original_error=e
                )
            elif "unavailable" in error_str or "503" in error_str:
                raise ExternalServiceUnavailableError(
                    service_name="Mailtrap",
                    operation_name="send_email",
                    original_error=e
                )
            elif "validation" in error_str or "invalid" in error_str or "400" in error_str:
                raise ExternalServiceValidationError(
                    service_name="Mailtrap",
                    operation_name="send_email",
                    original_error=e
                )
            else:
                # Generic request/response error
                raise ExternalServiceRequestError(
                    service_name="Mailtrap",
                    operation_name="send_email",
                    original_error=e
                )

    @classmethod
    def send_welcome_email(cls, to_email: str, template_variables: Dict[str, Any], category: str = "General") -> Dict[str, Any]:
        """
        Send welcome email using welcome template.
        
        Args:
            to_email: Recipient email address
            template_variables: Template variables for welcome email
            category: Email category (default: "General")
        
        Returns:
            Dict with success status and email details
        
        Raises:
            InternalError: If client not initialized
            InvalidInputError: If welcome_template_id not configured
            ExternalServiceError: Various external service errors (see send_template_email)
        """
        cls._ensure_initialized()
        template_id = cls._welcome_template_id
        if not template_id:
            raise InvalidInputError(
                field_name="welcome_template_id",
                message="Welcome template ID not configured in Mailtrap section"
            )
        return cls.send_template_email(to_email, template_id, template_variables, category)
    
    @classmethod
    def send_verification_email(cls, to_email: str, template_variables: Dict[str, Any], category: str = "General") -> Dict[str, Any]:
        """
        Send verification email using verification template.
        
        Args:
            to_email: Recipient email address
            template_variables: Template variables for verification email
            category: Email category (default: "General")
        
        Returns:
            Dict with success status and email details
        
        Raises:
            InternalError: If client not initialized
            InvalidInputError: If verification_template_id not configured
            ExternalServiceError: Various external service errors (see send_template_email)
        """
        cls._ensure_initialized()
        template_id = cls._verification_template_id
        if not template_id:
            raise InvalidInputError(
                field_name="verification_template_id",
                message="Verification template ID not configured in Mailtrap section"
            )
        return cls.send_template_email(to_email, template_id, template_variables, category)

    @classmethod
    def send_password_reset_email(cls, to_email: str, template_variables: Dict[str, Any], category: str = "General") -> Dict[str, Any]:
        """
        Send password reset email using password reset template.
        
        Args:
            to_email: Recipient email address
            template_variables: Template variables for password reset email
            category: Email category (default: "General")
        
        Returns:
            Dict with success status and email details
        
        Raises:
            InternalError: If client not initialized
            InvalidInputError: If password_reset_template_id not configured
            ExternalServiceError: Various external service errors (see send_template_email)
        """
        cls._ensure_initialized()
        template_id = cls._password_reset_template_id
        if not template_id:
            raise InvalidInputError(
                field_name="password_reset_template_id",
                message="Password reset template ID not configured in Mailtrap section"
            )
        return cls.send_template_email(to_email, template_id, template_variables, category)

    @classmethod
    def send_notification_email(cls, to_email: str, template_variables: Dict[str, Any], category: str = "General") -> Dict[str, Any]:
        """
        Send notification email using notification template.
        
        Args:
            to_email: Recipient email address
            template_variables: Template variables for notification email
            category: Email category (default: "General")
        
        Returns:
            Dict with success status and email details
        
        Raises:
            InternalError: If client not initialized
            InvalidInputError: If notification_template_id not configured
            ExternalServiceError: Various external service errors (see send_template_email)
        """
        cls._ensure_initialized()
        template_id = cls._notification_template_id
        if not template_id:
            raise InvalidInputError(
                field_name="notification_template_id",
                message="Notification template ID not configured in Mailtrap section"
            )
        return cls.send_template_email(to_email, template_id, template_variables, category)