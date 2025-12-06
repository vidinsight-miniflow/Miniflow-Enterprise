import os
from pathlib import Path
from dotenv import load_dotenv
from miniflow.core.exceptions import ResourceNotFoundError, InternalError

class EnvironmentHandler:
    """Environment handler for loading and managing environment variables from .env files."""
    _initialized = False
    _env_path = None

    @classmethod
    def load_env(cls, env_file_name=".env"):
        """Load environment variables from the specified .env file."""
        if cls._initialized:
            return

        project_root = Path(__file__).resolve().parents[4]
        cls._env_path = project_root / env_file_name

        if not cls._env_path.exists():
            raise ResourceNotFoundError(
                resource_name="Environment file", 
                resource_id=str(cls._env_path)
            )

        load_dotenv(cls._env_path)

        success, test_value = cls.test()
        if not success:
            raise InternalError(
                component_name="environment_handler",
                message="Environment validation test failed. Environment file may be corrupted or missing required variables.",
                error_details={
                    "test_key": "TEST_KEY",
                    "expected_value": "ThisKeyIsForConfigTest",
                    "actual_value": test_value,
                    "env_file_path": str(cls._env_path)
                }
            )
        
        cls._initialized = True

    @staticmethod
    def test(test_key="TEST_KEY"):
        """Test environment file validity by checking test key."""
        value = os.getenv(test_key)
        return (value == "ThisKeyIsForConfigTest", value if value else None)

    @staticmethod
    def get(key: str, default=None):
        """Get an environment variable value by key."""
        return os.getenv(key, default)
