import os
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

def load_environment_variables():
    """
    Load environment variables from .env file and validate required variables.
    
    Returns:
        bool: True if all required variables are loaded, False otherwise
    """
    # Display current working directory
    cwd = os.getcwd() # Get CWD
    logger.info(f"Current working directory when loading .env: {cwd}") # Log the CWD
    
    # Load variables from .env file if it exists
    dotenv_path = os.path.join(cwd, '.env') # Use CWD variable
    logger.info(f"Attempting to load .env file from: {dotenv_path}") # Log the path being checked
    if os.path.exists(dotenv_path):
        logger.info(f".env file found at {dotenv_path}")
        load_dotenv(dotenv_path)
    else:
        logger.warning(f".env file not found at {dotenv_path}")
        # Try looking in the parent directory
        parent_dotenv_path = os.path.join(os.path.dirname(cwd), '.env') # Use CWD variable
        logger.info(f"Attempting to load .env file from parent directory: {parent_dotenv_path}") # Log parent path check
        if os.path.exists(parent_dotenv_path):
            logger.info(f".env file found in parent directory: {parent_dotenv_path}")
            load_dotenv(parent_dotenv_path)
        else:
            logger.warning(f".env file not found in parent directory: {parent_dotenv_path}")
    
    # Define required environment variables
    required_vars = [
        "HASURA_GRAPHQL_URL",
        "HASURA_ADMIN_SECRET"
    ]
    
    # Log current environment variables (careful with secrets in production)
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Avoid logging the full secret
            log_value = value[:5] + '...' if var == "HASURA_ADMIN_SECRET" and len(value) > 5 else value
            logger.info(f"Found environment variable: {var}={log_value}")
        else:
            logger.warning(f"Missing environment variable: {var}")
    
    # Check for missing variables
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.info("Please create a .env file in the project root or set these environment variables")
        return False
    
    logger.info("Environment variables loaded successfully")
    return True 

def get_required_env_var(var_name):
    """
    Get a required environment variable and raise an error if it's not found.
    
    Args:
        var_name: Name of the environment variable
        
    Returns:
        The value of the environment variable
        
    Raises:
        ValueError: If the environment variable is not set
    """
    value = os.getenv(var_name)
    if not value:
        logger.error(f"Required environment variable {var_name} is not set")
        raise ValueError(f"Required environment variable {var_name} is not set")
    return value 