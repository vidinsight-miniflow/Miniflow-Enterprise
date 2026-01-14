import mailtrap as mt
from typing import List, Optional, Dict, Any

from qbitra.utils.handlers import EnvironmentHandler, ConfigurationHandler
from qbitra.core.qbitra_logger import get_logger
from qbitra.core.exceptions import (
    MailTrapError,
    MailTrapClientError,
    MailTrapSendError,
    ExternalServiceConnectionError,
    ExternalServiceTimeoutError,
    ExternalServiceValidationError,
    ExternalServiceAuthorizationError,
    ExternalServiceRateLimitError,
    ExternalServiceUnavailableError,
)


class MailTrapClient:
    """MailTrap client for sending emails."""

    _api_key: str = None
    _sender_name: Optional[str] = None
    _sender_email: str = None

    _client: mt.MailtrapClient = None
    _initialized: bool = False
    # Infrastructure katmanı logger'ı (logs/infrastructure/smtp/service.log)
    _logger = get_logger("smtp", parent_folder="infrastructure")

    @classmethod
    def _load_configuration(cls):
        """Load configuration from environment and config files."""
        cls._api_key = EnvironmentHandler.get_value_as_str("MAILTRAP_API_KEY")
        cls._sender_email = ConfigurationHandler.get_value_as_str("Mailtrap", "sender_email", fallback="info@qbitra.io")
        cls._sender_name = ConfigurationHandler.get_value_as_str("Mailtrap", "sender_name", fallback="QBitra")
        
        cls._logger.debug(
            "MailTrap configuration yüklendi",
            extra={
                "api_key_set": cls._api_key is not None,
                "sender_email": cls._sender_email,
                "sender_name": cls._sender_name
            }
        )

    @classmethod
    def _handle_send_exception(cls, e: Exception, operation: str, to_email: str, **extra_context):
        """
        Standart hata yönetimi helper metodu.
        Original exception'ı cause olarak tutar, tipine göre uygun exception fırlatır.
        """
        error_str = str(e).lower()
        
        # Context bilgilerini hazırla
        context = {
            "to_email": to_email,
            "operation": operation,
            "error": str(e),
            "error_type": type(e).__name__,
            **extra_context
        }
        
        cls._logger.error(
            f"MailTrap {operation} hatası: {to_email}",
            extra=context,
        )
        
        # Exception tipine göre uygun exception fırlat
        if isinstance(e, (TimeoutError,)) or "timeout" in error_str or "timed out" in error_str:
            raise ExternalServiceTimeoutError(
                service_name="MailTrap",
                operation_name=operation,
                message=f"MailTrap {operation} timeout oluştu ({to_email}): {e}",
                cause=e
            ) from e
        elif isinstance(e, (ConnectionError,)) or "connection" in error_str or "connect" in error_str:
            raise ExternalServiceConnectionError(
                service_name="MailTrap",
                operation_name=operation,
                message=f"MailTrap {operation} bağlantı hatası ({to_email}): {e}",
                cause=e
            ) from e
        elif isinstance(e, (ValueError,)) or "validation" in error_str or "invalid" in error_str or "400" in error_str:
            raise ExternalServiceValidationError(
                service_name="MailTrap",
                operation_name=operation,
                message=f"MailTrap {operation} validation hatası ({to_email}): {e}",
                cause=e
            ) from e
        elif "unauthorized" in error_str or "auth" in error_str or "401" in error_str:
            raise ExternalServiceAuthorizationError(
                service_name="MailTrap",
                operation_name=operation,
                message=f"MailTrap {operation} yetkilendirme hatası ({to_email}): {e}",
                cause=e
            ) from e
        elif "rate limit" in error_str or "429" in error_str:
            raise ExternalServiceRateLimitError(
                service_name="MailTrap",
                operation_name=operation,
                message=f"MailTrap {operation} rate limit hatası ({to_email}): {e}",
                cause=e
            ) from e
        elif "unavailable" in error_str or "503" in error_str:
            raise ExternalServiceUnavailableError(
                service_name="MailTrap",
                operation_name=operation,
                message=f"MailTrap servisi kullanılamıyor ({to_email}): {e}",
                cause=e
            ) from e
        else:
            # Genel send error - original exception cause olarak tutulur
            raise MailTrapSendError(
                to_email=to_email,
                operation=operation,
                message=f"MailTrap {operation} başarısız ({to_email}): {e}",
                cause=e
            ) from e

    @classmethod
    def load(cls):
        """Load MailTrap client configuration and create client instance."""
        if cls._initialized:
            cls._logger.info("MailTrap client daha önce başlatılmış, tekrar başlatılamaz")
            return

        try:
            cls._load_configuration()
            cls._client = mt.MailtrapClient(token=cls._api_key)
            cls._logger.debug(
                "MailTrap client başarıyla yüklendi",
                extra={
                    "sender_email": cls._sender_email,
                    "sender_name": cls._sender_name,
                    "initialized": True
                }
            )
            cls._initialized = True
        except Exception as e:
            cls._logger.error(
                f"MailTrap client başlatılırken hata oluştu: {e}",
                extra={"error": str(e), "error_type": type(e).__name__},
            )
            raise MailTrapClientError(
                operation="initialization",
                message=f"MailTrap client başlatılamadı: {e}",
                cause=e
            ) from e

    @classmethod
    def test(cls, test_email: str = None) -> tuple[bool, Optional[str]]:
        """Test MailTrap client by checking configuration validity."""
        if not cls._initialized:
            cls._logger.error("Test işlemi yapılmadan önce MailTrap client başlatılmalıdır")
            cls._logger.debug("MailTrap client başlatılıyor...")
            cls.load()

        is_valid = all([
            cls._api_key is not None,
            cls._sender_email is not None,
            cls._client is not None
        ])

        cls._logger.debug(
            f"MailTrap test - API Key: {'set' if cls._api_key else 'missing'}, "
            f"Sender: {cls._sender_email}, Client: {'initialized' if cls._client else 'missing'}",
            extra={
                "api_key_set": cls._api_key is not None,
                "sender_email": cls._sender_email,
                "sender_name": cls._sender_name,
                "client_initialized": cls._client is not None,
                "is_valid": is_valid
            }
        )

        return is_valid, cls._sender_email if is_valid else None

    @classmethod
    def init(cls) -> bool:
        """Initialize MailTrap client with validation test."""
        if cls._initialized:
            cls._logger.info("MailTrap client daha önce başlatılmış, tekrar başlatılamaz")
            return True

        cls.load()

        success, sender_email = cls.test()
        if not success:
            cls._logger.error(
                "MailTrap client test başarısız, konfigürasyonu kontrol ediniz",
                extra={
                    "api_key_set": cls._api_key is not None,
                    "sender_email": cls._sender_email,
                    "client_initialized": cls._client is not None
                }
            )
            raise MailTrapClientError(
                operation="test",
                message="MailTrap client test başarısız. API key ve sender bilgilerini kontrol ediniz."
            )

        cls._logger.info(
            f"MailTrap client başarıyla başlatıldı: {sender_email}",
            extra={
                "sender_email": sender_email,
                "sender_name": cls._sender_name,
                "initialized": True
            }
        )
        return cls._initialized

    @classmethod
    def is_initialized(cls) -> bool:
        """Check if MailTrap client is initialized."""
        return cls._initialized

    @classmethod
    def _ensure_initialized(cls):
        """Ensure client is initialized before operations."""
        if not cls._initialized:
            cls._logger.error("MailTrap client başlatılmadan işlem yapılamaz")
            raise MailTrapClientError(
                operation="operation",
                message="MailTrap client başlatılmadan e-posta gönderilemez"
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
        """Send an email with HTML content."""
        cls._ensure_initialized()

        try:
            to_addresses = [mt.Address(email=to_email)]
            cc_addresses = [mt.Address(email=email) for email in (cc or [])]
            bcc_addresses = [mt.Address(email=email) for email in (bcc or [])]

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

            response = cls._client.send(mail)
            cls._logger.debug(
                f"E-posta başarıyla gönderildi: {to_email}",
                extra={
                    "to_email": to_email,
                    "subject": subject,
                    "category": category,
                    "cc_count": len(cc_addresses),
                    "bcc_count": len(bcc_addresses),
                    "has_text_content": text_content is not None,
                    "has_html_content": bool(html_content),
                    "sender_email": cls._sender_email,
                    "sender_name": cls._sender_name
                }
            )
            return response

        except MailTrapError:
            raise
        except Exception as e:
            cls._handle_send_exception(e, "send_email", to_email)

    @classmethod
    def send_template_email(
        cls,
        to_email: str,
        template_uuid: str,
        template_variables: Dict[str, Any],
        category: str = "General",
    ) -> Dict[str, Any]:
        """Send an email using a template."""
        cls._ensure_initialized()

        try:
            mail = mt.MailFromTemplate(
                sender=mt.Address(email=cls._sender_email, name=cls._sender_name),
                to=[mt.Address(email=to_email)],
                template_uuid=template_uuid,
                template_variables=template_variables,
                category=category
            )

            response = cls._client.send(mail)
            cls._logger.debug(
                f"Template e-posta başarıyla gönderildi: {to_email} (template: {template_uuid})",
                extra={
                    "to_email": to_email,
                    "template_uuid": template_uuid,
                    "category": category,
                    "template_variables_count": len(template_variables),
                    "sender_email": cls._sender_email,
                    "sender_name": cls._sender_name
                }
            )
            return response

        except MailTrapError:
            raise
        except Exception as e:
            cls._handle_send_exception(e, "send_template_email", to_email, template_uuid=template_uuid)

    @classmethod
    def send_bulk_email(
        cls,
        to_emails: List[str],
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        category: str = "Bulk",
    ) -> List[Dict[str, Any]]:
        """Send the same email to multiple recipients individually."""
        cls._ensure_initialized()

        cls._logger.debug(
            f"Bulk e-posta gönderimi başlatılıyor: {len(to_emails)} alıcı",
            extra={
                "total_recipients": len(to_emails),
                "subject": subject,
                "category": category,
                "has_text_content": text_content is not None,
                "has_html_content": bool(html_content)
            }
        )
        
        results = []
        for email in to_emails:
            try:
                response = cls.send_email(
                    to_email=email,
                    subject=subject,
                    html_content=html_content,
                    text_content=text_content,
                    category=category
                )
                results.append({"email": email, "success": True, "response": response})
            except (MailTrapSendError, MailTrapError) as e:
                cls._logger.warning(
                    f"Bulk e-posta gönderilemedi: {email}",
                    extra={
                        "email": email,
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "subject": subject
                    }
                )
                results.append({"email": email, "success": False, "error": str(e)})

        success_count = sum(1 for r in results if r["success"])
        failure_count = len(to_emails) - success_count
        cls._logger.info(
            f"Bulk e-posta tamamlandı: {success_count}/{len(to_emails)} başarılı",
            extra={
                "total_recipients": len(to_emails),
                "success_count": success_count,
                "failure_count": failure_count,
                "subject": subject,
                "category": category
            }
        )
        return results

    @classmethod
    def get_sender_info(cls) -> Dict[str, str]:
        """Get current sender information."""
        cls._ensure_initialized()
        return {
            "email": cls._sender_email,
            "name": cls._sender_name
        }

    @classmethod
    def reload(cls):
        """Reload MailTrap client configuration."""
        old_sender_email = cls._sender_email
        old_sender_name = cls._sender_name
        
        cls._logger.info(
            "MailTrap client yeniden yükleniyor...",
            extra={
                "old_sender_email": old_sender_email,
                "old_sender_name": old_sender_name
            }
        )
        cls._initialized = False
        cls._client = None
        cls._api_key = None
        cls._sender_email = None
        cls._sender_name = None
        cls.load()
        cls._logger.info(
            "MailTrap client başarıyla yeniden yüklendi",
            extra={
                "new_sender_email": cls._sender_email,
                "new_sender_name": cls._sender_name,
                "old_sender_email": old_sender_email,
                "old_sender_name": old_sender_name
            }
        )
