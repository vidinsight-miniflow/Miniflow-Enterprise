"""
MiniFlow Test Configuration & Fixtures
======================================

Bu dosya tüm testler için ortak fixture'ları ve konfigürasyonu içerir.
"""

import pytest
import os
import sys
from typing import Generator, Dict, Any
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Project root'u path'e ekle
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))


# ==============================================================================
# Mock Script Content
# ==============================================================================

MOCK_SCRIPTS = {
    "simple_echo": {
        "name": "Simple Echo Script",
        "description": "Gelen veriyi aynen döndürür",
        "content": '''
def main(params):
    """Gelen parametreleri aynen döndürür."""
    return {
        "status": "success",
        "data": params
    }
''',
        "input_schema": {
            "message": {"type": "string", "required": True, "description": "Echo edilecek mesaj"}
        },
        "output_schema": {
            "status": {"type": "string"},
            "data": {"type": "object"}
        }
    },
    
    "data_transformer": {
        "name": "Data Transformer Script",
        "description": "Veriyi dönüştürür ve sonraki node'a aktarır",
        "content": '''
def main(params):
    """Veriyi dönüştürür."""
    input_value = params.get("input_value", "")
    prefix = params.get("prefix", "processed_")
    
    return {
        "status": "success",
        "output_value": f"{prefix}{input_value}",
        "timestamp": params.get("timestamp", "unknown")
    }
''',
        "input_schema": {
            "input_value": {"type": "string", "required": True, "description": "Dönüştürülecek değer"},
            "prefix": {"type": "string", "required": False, "default": "processed_", "description": "Prefix"}
        },
        "output_schema": {
            "status": {"type": "string"},
            "output_value": {"type": "string"},
            "timestamp": {"type": "string"}
        }
    },
    
    "accumulator": {
        "name": "Accumulator Script",
        "description": "Birden fazla değeri birleştirir",
        "content": '''
def main(params):
    """Değerleri birleştirir."""
    values = params.get("values", [])
    separator = params.get("separator", ", ")
    
    if isinstance(values, list):
        result = separator.join(str(v) for v in values)
    else:
        result = str(values)
    
    return {
        "status": "success",
        "combined_result": result,
        "item_count": len(values) if isinstance(values, list) else 1
    }
''',
        "input_schema": {
            "values": {"type": "array", "required": True, "description": "Birleştirilecek değerler"},
            "separator": {"type": "string", "required": False, "default": ", ", "description": "Ayırıcı"}
        },
        "output_schema": {
            "status": {"type": "string"},
            "combined_result": {"type": "string"},
            "item_count": {"type": "integer"}
        }
    },
    
    "calculator": {
        "name": "Calculator Script",
        "description": "Basit matematiksel işlemler yapar",
        "content": '''
def main(params):
    """Matematiksel işlem yapar."""
    a = float(params.get("a", 0))
    b = float(params.get("b", 0))
    operation = params.get("operation", "add")
    
    if operation == "add":
        result = a + b
    elif operation == "subtract":
        result = a - b
    elif operation == "multiply":
        result = a * b
    elif operation == "divide":
        result = a / b if b != 0 else 0
    else:
        result = 0
    
    return {
        "status": "success",
        "result": result,
        "operation": operation
    }
''',
        "input_schema": {
            "a": {"type": "number", "required": True, "description": "İlk sayı"},
            "b": {"type": "number", "required": True, "description": "İkinci sayı"},
            "operation": {"type": "string", "required": False, "default": "add", "description": "İşlem tipi"}
        },
        "output_schema": {
            "status": {"type": "string"},
            "result": {"type": "number"},
            "operation": {"type": "string"}
        }
    },
    
    "delay_script": {
        "name": "Delay Script",
        "description": "Belirtilen süre bekler (concurrent test için)",
        "content": '''
import time

def main(params):
    """Belirtilen süre bekler."""
    delay_seconds = float(params.get("delay_seconds", 1))
    workflow_id = params.get("workflow_id", "unknown")
    
    time.sleep(delay_seconds)
    
    return {
        "status": "success",
        "workflow_id": workflow_id,
        "delayed_for": delay_seconds,
        "completed_at": time.time()
    }
''',
        "input_schema": {
            "delay_seconds": {"type": "number", "required": False, "default": 1, "description": "Bekleme süresi"},
            "workflow_id": {"type": "string", "required": False, "description": "Workflow ID"}
        },
        "output_schema": {
            "status": {"type": "string"},
            "workflow_id": {"type": "string"},
            "delayed_for": {"type": "number"},
            "completed_at": {"type": "number"}
        }
    }
}


@pytest.fixture(scope="session")
def mock_scripts():
    """Mock script tanımları."""
    return MOCK_SCRIPTS


# ==============================================================================
# DATABASE TEST FIXTURES
# ==============================================================================

@pytest.fixture(scope="function")
def test_db_setup():
    """Setup test database and return session."""
    import os
    from miniflow.database.engine import DatabaseManager
    from miniflow.database.config import DatabaseConfig, DatabaseType
    
    # Set environment variables for testing
    os.environ.setdefault('APP_ENV', 'test')
    os.environ.setdefault('JWT_SECRET_KEY', 'test_jwt_secret_key_32chars_min!')
    os.environ.setdefault('ENCRYPTION_KEY', 'test_encryption_key_32chars!!')
    os.environ.setdefault('MAILTRAP_API_TOKEN', 'dummy_token')
    os.environ.setdefault('MAILTRAP_SENDER_EMAIL', 'test@example.com')
    
    # Setup configuration handler
    from miniflow.utils.handlers.configuration_handler import ConfigurationHandler
    from miniflow.utils.handlers.environment_handler import EnvironmentHandler
    
    EnvironmentHandler._initialized = True
    
    config_path = os.path.join(PROJECT_ROOT, 'configurations', 'test.ini')
    if os.path.exists(config_path):
        import configparser
        from pathlib import Path
        
        ConfigurationHandler._parser = configparser.ConfigParser()
        ConfigurationHandler._parser.read(config_path)
        ConfigurationHandler._config_dir = Path(PROJECT_ROOT) / "configurations"
        ConfigurationHandler._initialized = True
    
    # Initialize database
    db_config = DatabaseConfig(
        db_type=DatabaseType.SQLITE,
        db_name=":memory:"
    )
    
    manager = DatabaseManager()
    manager.initialize(db_config, auto_start=True, create_tables=True, force_reinitialize=True)
    
    # Get session
    session = manager.engine.get_session()
    
    yield session
    
    # Cleanup
    session.close()
    try:
        manager.reset()
    except Exception:
        pass  # Ignore reset errors in tests


@pytest.fixture(scope="function")
def test_agreements(test_db_setup):
    """Create default agreements for testing."""
    from miniflow.services._1_info_service.agreement_service import AgreementService
    from datetime import datetime, timezone
    
    session = test_db_setup
    
    # Create default agreements
    agreements_data = [
        {
            "agreement_type": "terms",
            "version": "1.0",
            "locale": "tr-TR",
            "content": "# Terms of Service\n\nTest terms content.",
            "effective_date": datetime.now(timezone.utc),
            "is_active": True,
            "created_by": "SYSTEM"
        },
        {
            "agreement_type": "privacy_policy",
            "version": "1.0",
            "locale": "tr-TR",
            "content": "# Privacy Policy\n\nTest privacy policy content.",
            "effective_date": datetime.now(timezone.utc),
            "is_active": True,
            "created_by": "SYSTEM"
        }
    ]
    
    AgreementService.seed_default_agreements(agreements_data=agreements_data)
    
    # Get active agreement IDs
    active_agreements = AgreementService.get_active_agreements(locale="tr-TR")
    terms_id = next((a["id"] for a in active_agreements if a["agreement_type"] == "terms"), None)
    privacy_id = next((a["id"] for a in active_agreements if a["agreement_type"] == "privacy_policy"), None)
    
    return {
        "terms_id": terms_id,
        "privacy_id": privacy_id
    }


# ==============================================================================
# API TEST FIXTURES
# ==============================================================================

@pytest.fixture(scope="function")
def test_app(test_db_setup) -> FastAPI:
    """Create FastAPI app for testing."""
    from fastapi import FastAPI, Request
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.responses import Response
    from miniflow.server.middleware import RequestContextMiddleware, IPRateLimitMiddleware
    from miniflow.server.middleware.exception_handler import register_exception_handlers
    
    # Create test app
    app = FastAPI(
        title="MiniFlow Test API",
        description="Test API for endpoint testing",
        version="1.0.0-test"
    )
    
    # Test middleware to inject session into request.state
    class TestSessionMiddleware(BaseHTTPMiddleware):
        def __init__(self, app, session):
            super().__init__(app)
            self.session = session
        
        async def dispatch(self, request: Request, call_next) -> Response:
            request.state.session = self.session
            response = await call_next(request)
            return response
    
    # Configure middleware (order matters!)
    app.add_middleware(TestSessionMiddleware, session=test_db_setup)
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(IPRateLimitMiddleware)
    register_exception_handlers(app)
    
    # Include frontend routes
    from miniflow.server.routes.frontend import router as frontend_router
    app.include_router(frontend_router)
    
    return app


@pytest.fixture(scope="function")
def client(test_app: FastAPI) -> TestClient:
    """Test client for API requests."""
    return TestClient(test_app, raise_server_exceptions=False)


@pytest.fixture(scope="function")
def auth_headers(client: TestClient, test_agreements: Dict[str, str], test_db_setup) -> Dict[str, str]:
    """Create authenticated user and return headers.
    
    This fixture:
    1. Registers a test user
    2. Gets email verification token from database
    3. Verifies email using the verification endpoint
    4. Logs in with the user
    5. Extracts the access token
    6. Returns Authorization header
    """
    import uuid
    from tests.fixtures.endpoint_test_helpers import EndpointTester
    from miniflow.database import RepositoryRegistry
    
    tester = EndpointTester(client)
    session = test_db_setup
    registry = RepositoryRegistry()
    user_repo = registry.user_repository()
    
    # Generate unique test user credentials
    test_id = str(uuid.uuid4())[:8]
    username = f"testuser_{test_id}"
    email = f"test_{test_id}@example.com"
    password = "TestPassword123!"
    
    # Register user
    register_data = {
        "username": username,
        "email": email,
        "password": password,
        "name": "Test",
        "surname": "User",
        "marketing_consent": False,
        "terms_accepted_version_id": test_agreements["terms_id"],
        "privacy_policy_accepted_version_id": test_agreements["privacy_id"]
    }
    
    register_response = tester.post("/frontend/auth/register", json=register_data)
    
    if register_response.status_code != 200:
        # If registration fails, return empty headers (fallback)
        return {}
    
    register_result = register_response.json()
    if not register_result.get("success"):
        return {}
    
    user_data = register_result.get("data", {})
    user_id = user_data.get("id")
    
    if not user_id:
        return {}
    
    # Get email verification token from database
    try:
        user = user_repo._get_by_id(session, record_id=user_id, raise_not_found=True)
        verification_token = user.email_verification_token
        
        if not verification_token:
            # If no token, return empty headers
            return {}
        
        # Verify email using the verification endpoint
        verify_data = {
            "verification_token": verification_token
        }
        
        verify_response = tester.post("/frontend/auth/verify-email", json=verify_data)
        
        if verify_response.status_code != 200:
            # If verification fails, return empty headers
            return {}
        
        verify_result = verify_response.json()
        if not verify_result.get("success"):
            return {}
        
    except Exception:
        session.rollback()
        return {}
    
    # Login
    login_data = {
        "email_or_username": email,
        "password": password,
        "device_type": "web"
    }
    
    login_response = tester.post("/frontend/auth/login", json=login_data)
    
    if login_response.status_code != 200:
        # If login fails, return empty headers
        return {}
    
    login_result = login_response.json()
    if not login_result.get("success"):
        return {}
    
    login_data_response = login_result.get("data", {})
    access_token = login_data_response.get("access_token")
    
    if not access_token:
        return {}
    
    # Return Authorization header
    return {
        "Authorization": f"Bearer {access_token}"
    }


@pytest.fixture(scope="function")
def admin_headers(client: TestClient, test_agreements: Dict[str, str], test_db_setup) -> Dict[str, str]:
    """Create admin user and return headers.
    
    This fixture creates an admin user and returns authentication headers.
    """
    import uuid
    from datetime import datetime, timezone
    from tests.fixtures.endpoint_test_helpers import EndpointTester
    from miniflow.database import RepositoryRegistry
    
    tester = EndpointTester(client)
    session = test_db_setup
    registry = RepositoryRegistry()
    user_repo = registry.user_repository()
    user_role_repo = registry.user_roles_repository()
    
    # Generate unique test admin credentials
    test_id = str(uuid.uuid4())[:8]
    username = f"admin_{test_id}"
    email = f"admin_{test_id}@example.com"
    password = "AdminPassword123!"
    
    # Register admin user
    register_data = {
        "username": username,
        "email": email,
        "password": password,
        "name": "Admin",
        "surname": "User",
        "marketing_consent": False,
        "terms_accepted_version_id": test_agreements["terms_id"],
        "privacy_policy_accepted_version_id": test_agreements["privacy_id"]
    }
    
    register_response = tester.post("/frontend/auth/register", json=register_data)
    
    if register_response.status_code != 200:
        return {}
    
    register_result = register_response.json()
    if not register_result.get("success"):
        return {}
    
    user_data = register_result.get("data", {})
    user_id = user_data.get("id")
    
    if not user_id:
        return {}
    
    # Verify email and set as super admin
    try:
        # Get email verification token from database
        user = user_repo._get_by_id(session, record_id=user_id, raise_not_found=True)
        verification_token = user.email_verification_token
        
        if verification_token:
            # Verify email using the verification endpoint
            verify_data = {
                "verification_token": verification_token
            }
            verify_response = tester.post("/frontend/auth/verify-email", json=verify_data)
            # Verification might fail due to response validation, but check database
        
        # Set user as super admin (is_superadmin=True)
        user_repo._update(
            session,
            record_id=user_id,
            is_verified=True,
            email_verified_at=datetime.now(timezone.utc),
            email_verification_token=None,
            email_verification_token_expires_at=None,
            is_superadmin=True  # Set as super admin
        )
        session.commit()
    except Exception:
        session.rollback()
        return {}
    
    # Login
    login_data = {
        "email_or_username": email,
        "password": password,
        "device_type": "web"
    }
    
    login_response = tester.post("/frontend/auth/login", json=login_data)
    
    if login_response.status_code != 200:
        return {}
    
    login_result = login_response.json()
    if not login_result.get("success"):
        return {}
    
    login_data_response = login_result.get("data", {})
    access_token = login_data_response.get("access_token")
    
    if not access_token:
        return {}
    
    return {
        "Authorization": f"Bearer {access_token}"
    }


@pytest.fixture(scope="function")
def test_workspace(client: TestClient, auth_headers: Dict[str, str]) -> Dict[str, Any]:
    """Create a test workspace and return workspace info."""
    import uuid
    from tests.fixtures.endpoint_test_helpers import EndpointTester
    
    tester = EndpointTester(client, auth_headers)
    
    workspace_data = {
        "name": "Test Workspace",
        "slug": f"test-workspace-{uuid.uuid4().hex[:8]}",
        "description": "Test workspace for integration tests"
    }
    
    response = tester.post("/frontend/workspaces", json=workspace_data)
    
    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            return result.get("data", {})
    
    return {}
