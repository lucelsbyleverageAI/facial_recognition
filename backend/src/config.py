import os
from typing import Dict

ENV: Dict[str, str] = {
    # Database settings
    "POSTGRES_USER": os.getenv("POSTGRES_USER", "postgres"),
    "POSTGRES_PASSWORD": os.getenv("POSTGRES_PASSWORD", ""),
    "POSTGRES_DB": os.getenv("POSTGRES_DB", "db"),
    "DATABASE_URL": os.getenv("DATABASE_URL", ""),
    
    # Hasura settings
    "HASURA_ADMIN_SECRET": os.getenv("HASURA_ADMIN_SECRET", ""),
    "HASURA_GRAPHQL_URL": os.getenv("HASURA_GRAPHQL_URL", "http://localhost:8080/v1/graphql"),
}

# Validate required environment variables
def validate_env() -> None:
    """Validate that all required environment variables are set."""
    required_vars = [
        "HASURA_ADMIN_SECRET",
        "HASURA_GRAPHQL_URL",
    ]
    
    missing = [var for var in required_vars if not ENV.get(var)]
    if missing:
        raise EnvironmentError(f"Missing required environment variables: {', '.join(missing)}") 