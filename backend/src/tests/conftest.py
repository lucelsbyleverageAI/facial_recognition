import os
import pytest
from dotenv import load_dotenv

# Load environment variables at the beginning of test session
def pytest_configure(config):
    """Load environment variables from .env file."""
    # Path to .env file relative to the backend directory
    env_path = os.path.join(os.path.dirname(__file__), '../..', '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
    else:
        pytest.fail(f".env file not found at {env_path}") 