import pytest
import mailtrap as mt
from unittest.mock import patch, MagicMock
from qbitra.utils.handlers.mailtrap_handler import MailTrapClient
from qbitra.utils.handlers import EnvironmentHandler, ConfigurationHandler
from qbitra.core.exceptions import (
    MailTrapClientError,
    MailTrapSendError,
    ExternalServiceConnectionError,
    ExternalServiceTimeoutError,
    ExternalServiceValidationError,
    ExternalServiceAuthorizationError,
    ExternalServiceRateLimitError,
    ExternalServiceUnavailableError,
)

@pytest.fixture(autouse=True)
def reset_mailtrap_client():
    """Reset MailTrapClient class variables before each test."""
    MailTrapClient._api_key = None
    MailTrapClient._sender_name = None
    MailTrapClient._sender_email = None
    MailTrapClient._client = None
    MailTrapClient._initialized = False
    yield
    MailTrapClient._api_key = None
    MailTrapClient._sender_name = None
    MailTrapClient._sender_email = None
    MailTrapClient._client = None
    MailTrapClient._initialized = False

def test_load_success():
    """Test successful client loading and configuration."""
    with patch.object(EnvironmentHandler, "get_value_as_str", return_value="test_api_key"), \
         patch.object(ConfigurationHandler, "get_value_as_str", side_effect=["sender@test.com", "Test Sender"]), \
         patch("mailtrap.MailtrapClient") as mock_mt_client:
        
        MailTrapClient.load()
        
        assert MailTrapClient._api_key == "test_api_key"
        assert MailTrapClient._sender_email == "sender@test.com"
        assert MailTrapClient._sender_name == "Test Sender"
        assert MailTrapClient._initialized is True
        mock_mt_client.assert_called_once_with(token="test_api_key")

def test_load_failure():
    """Test client loading failure."""
    with patch.object(EnvironmentHandler, "get_value_as_str", side_effect=Exception("Env Error")):
        with pytest.raises(MailTrapClientError) as exc:
            MailTrapClient.load()
        assert "başlatılamadı" in str(exc.value)

def test_init_success():
    """Test successful initialization with validation."""
    def mock_load():
        MailTrapClient._initialized = True

    with patch.object(MailTrapClient, "load", side_effect=mock_load), \
         patch.object(MailTrapClient, "test", return_value=(True, "sender@test.com")):
        
        success = MailTrapClient.init()
        assert success is True
        assert MailTrapClient.is_initialized() is True

def test_init_failure():
    """Test initialization failure when test fails."""
    with patch.object(MailTrapClient, "load"), \
         patch.object(MailTrapClient, "test", return_value=(False, None)):
        
        with pytest.raises(MailTrapClientError) as exc:
            MailTrapClient.init()
        assert "test başarısız" in str(exc.value)

def test_ensure_initialized_error():
    """Test error when calling send before initialization."""
    MailTrapClient._initialized = False
    with pytest.raises(MailTrapClientError) as exc:
        MailTrapClient.send_email("to@test.com", "Sub", "Content")
    assert "başlatılmadan e-posta gönderilemez" in str(exc.value)

@patch("mailtrap.Mail")
@patch("mailtrap.Address")
def test_send_email_success(mock_address, mock_mail):
    """Test successful email sending."""
    MailTrapClient._initialized = True
    MailTrapClient._client = MagicMock()
    MailTrapClient._sender_email = "sender@test.com"
    MailTrapClient._sender_name = "Sender"
    
    # Mocking mt.Address returns to simulate behavior
    mock_address.side_effect = lambda email, name=None: MagicMock(email=email, name=name)
    
    response = MailTrapClient.send_email(
        to_email="user@test.com",
        subject="Hello",
        html_content="<h1>Hi</h1>",
        text_content="Hi",
        cc=["cc@test.com"],
        bcc=["bcc@test.com"]
    )
    
    MailTrapClient._client.send.assert_called_once()
    assert response == MailTrapClient._client.send.return_value

@patch("mailtrap.MailFromTemplate")
@patch("mailtrap.Address")
def test_send_template_email_success(mock_address, mock_template_mail):
    """Test successful template email sending."""
    MailTrapClient._initialized = True
    MailTrapClient._client = MagicMock()
    MailTrapClient._sender_email = "sender@test.com"
    
    response = MailTrapClient.send_template_email(
        to_email="user@test.com",
        template_uuid="uuid-123",
        template_variables={"name": "Test"}
    )
    
    MailTrapClient._client.send.assert_called_once()
    assert response == MailTrapClient._client.send.return_value

def test_send_bulk_email():
    """Test bulk email sending handles successes and failures."""
    MailTrapClient._initialized = True
    
    # Mock send_email to succeed for first, fail for second
    def mock_send_email(to_email, **kwargs):
        if to_email == "fail@test.com":
            raise MailTrapSendError(to_email=to_email, operation="send", message="Fail")
        return {"success": True}

    with patch.object(MailTrapClient, "send_email", side_effect=mock_send_email):
        results = MailTrapClient.send_bulk_email(
            to_emails=["success@test.com", "fail@test.com"],
            subject="Bulk",
            html_content="Content"
        )
        
        assert len(results) == 2
        assert results[0]["success"] is True
        assert results[1]["success"] is False
        assert "Fail" in results[1]["error"]

@pytest.mark.parametrize("exception_type, error_str, expected_qbitra_exc", [
    (TimeoutError, "timeout", ExternalServiceTimeoutError),
    (ConnectionError, "connection", ExternalServiceConnectionError),
    (ValueError, "validation", ExternalServiceValidationError),
    (Exception, "unauthorized", ExternalServiceAuthorizationError),
    (Exception, "rate limit", ExternalServiceRateLimitError),
    (Exception, "unavailable", ExternalServiceUnavailableError),
    (Exception, "random", MailTrapSendError),
])
def test_handle_send_exception_mapping(exception_type, error_str, expected_qbitra_exc):
    """Test that low-level exceptions are correctly mapped to QBitra exceptions."""
    with pytest.raises(expected_qbitra_exc):
        MailTrapClient._handle_send_exception(
            exception_type(error_str), 
            "test_op", 
            "to@test.com"
        )

def test_reload():
    """Test reload functionality resets and reloads state."""
    with patch.object(MailTrapClient, "load") as mock_load:
        MailTrapClient._initialized = True
        MailTrapClient.reload()
        assert MailTrapClient._initialized is False # Reset before load
        mock_load.assert_called_once()

def test_get_sender_info():
    """Test getting sender info."""
    MailTrapClient._initialized = True
    MailTrapClient._sender_email = "test@qbitra.io"
    MailTrapClient._sender_name = "QBitra"
    
    info = MailTrapClient.get_sender_info()
    assert info["email"] == "test@qbitra.io"
    assert info["name"] == "QBitra"
