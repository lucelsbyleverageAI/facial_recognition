import os
import logging
import aiohttp
import json
from typing import Dict, Any, Optional
from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport
from gql.transport.aiohttp import AIOHTTPTransport
from src.config import ENV

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set GQL transport logger to WARNING to reduce verbosity
logging.getLogger('gql.transport.aiohttp').setLevel(logging.WARNING)

class GraphQLClientError(Exception):
    """Exception raised for GraphQL client errors."""
    pass

class GraphQLClient:
    """
    A GraphQL client that handles both synchronous and asynchronous operations.
    This client manages connections to the Hasura GraphQL endpoint and provides
    methods for executing queries and mutations.
    """
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        """Ensure only one instance of GraphQLClient exists. Accept any args but ignore them here."""
        if cls._instance is None:
            cls._instance = super(GraphQLClient, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, url: Optional[str] = None, admin_secret: Optional[str] = None):
        """
        Initialize the GraphQL client.
        
        Args:
            url: The Hasura GraphQL URL. If None, uses HASURA_GRAPHQL_URL environment variable.
            admin_secret: The Hasura admin secret. If None, uses HASURA_ADMIN_SECRET environment variable.
        """
        # Only initialize once even if constructor is called multiple times (singleton pattern)
        if getattr(self, "_initialized", False):
            print("GraphQLClient already initialized, skipping")
            return
            
        # First try parameters, then environment variables
        self.url = url
        if not self.url:
            self.url = os.getenv("HASURA_GRAPHQL_URL")
            if self.url:
                logger.info("Using HASURA_GRAPHQL_URL from environment")
            else:
                logger.error("HASURA_GRAPHQL_URL not found in parameters or environment")
        
        self.admin_secret = admin_secret
        if not self.admin_secret:
            self.admin_secret = os.getenv("HASURA_ADMIN_SECRET")
            if self.admin_secret:
                logger.info("Using HASURA_ADMIN_SECRET from environment")
            else:
                logger.error("HASURA_ADMIN_SECRET not found in parameters or environment")
        
        if not self.url or not self.admin_secret:
            missing_vars = []
            if not self.url:
                missing_vars.append("HASURA_GRAPHQL_URL")
            if not self.admin_secret:
                missing_vars.append("HASURA_ADMIN_SECRET")
            
            error_msg = f"Missing required environment variables: {' or '.join(missing_vars)}"
            logger.error(error_msg)
            raise GraphQLClientError(error_msg)
        
        self.logger = logging.getLogger(__name__)
        
        # Common headers for authentication
        self.headers = {
            "Content-Type": "application/json",
            "x-hasura-admin-secret": self.admin_secret
        }
        
        # Initialize both sync and async clients
        self._init_sync_client()
        self._init_async_client()
        
        self._initialized = True

    def _init_sync_client(self) -> None:
        """
        Initialize the synchronous GraphQL client using RequestsHTTPTransport.
        This client is used for regular synchronous operations.
        """
        try:
            transport = RequestsHTTPTransport(
                url=self.url,
                headers=self.headers,
                verify=True,  # SSL verification
                retries=3,    # Retry failed requests
            )
            
            self.sync_client = Client(
                transport=transport,
                fetch_schema_from_transport=False
            )
            
            self.logger.info("Synchronous GraphQL client initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize sync client: {str(e)}")
            raise GraphQLClientError("Sync client initialization failed") from e

    def _init_async_client(self) -> None:
        """
        Initialize the asynchronous GraphQL client using AIOHTTPTransport.
        This client is used for asynchronous operations.
        """
        try:
            transport = AIOHTTPTransport(
                url=self.url,
                headers=self.headers
            )
            
            self.async_client = Client(
                transport=transport,
                fetch_schema_from_transport=False
            )
            
            self.logger.info("Asynchronous GraphQL client initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize async client: {str(e)}")
            raise GraphQLClientError("Async client initialization failed") from e

    def execute(
        self, 
        query: str, 
        variables: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a synchronous GraphQL operation.
        
        Args:
            query: The GraphQL query or mutation string
            variables: Optional variables for the operation
            
        Returns:
            Dictionary containing the operation results
            
        Raises:
            GraphQLClientError: If the operation fails
        """
        try:
            # Convert string to gql object
            parsed_query = gql(query)
            
            # Execute the query
            result = self.sync_client.execute(
                parsed_query,
                variable_values=variables if variables is not None else {}
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"GraphQL operation failed: {str(e)}")
            raise GraphQLClientError("Failed to execute GraphQL operation") from e

    async def execute_async(self, query: str, variables: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute a GraphQL query or mutation asynchronously.
        
        Args:
            query: The GraphQL query or mutation string
            variables: Variables for the query
            
        Returns:
            The data response from the query
            
        Raises:
            GraphQLClientError: If the request fails or returns errors
        """
        headers = {
            "Content-Type": "application/json",
            "x-hasura-admin-secret": self.admin_secret
        }
        
        payload = {
            "query": query,
            "variables": variables or {}
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                # Log the request
                logger.debug(f"Sending GraphQL request to {self.url}")
                
                async with session.post(self.url, json=payload, headers=headers) as response:
                    # Log the response status
                    logger.debug(f"GraphQL response status: {response.status}")
                    
                    if response.status != 200:
                        # Try to get text content for better error messages
                        content_type = response.headers.get("Content-Type", "")
                        response_text = await response.text()
                        
                        error_msg = f"GraphQL server returned status {response.status}"
                        logger.error(f"{error_msg}\nResponse: {response_text[:500]}")
                        
                        # If we got a 404, give more helpful suggestions
                        if response.status == 404:
                            logger.error(f"GraphQL endpoint not found at: {self.url}")
                            logger.error("Check if Hasura is running and if the URL is correct")
                            logger.error("Common URLs: http://localhost:8080/v1/graphql, http://hasura:8080/v1/graphql")
                        
                        raise GraphQLClientError(error_msg)
                    
                    result = await response.json()
                    
                    if "errors" in result:
                        error_msg = f"GraphQL error: {json.dumps(result['errors'])}"
                        logger.error(error_msg)
                        raise GraphQLClientError(error_msg)
                    
                    return result.get("data", {})
        except aiohttp.ClientError as e:
            error_msg = f"Network error during GraphQL request: {str(e)}"
            logger.error(error_msg)
            raise GraphQLClientError(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error during GraphQL request: {str(e)}"
            logger.error(error_msg)
            raise GraphQLClientError(error_msg) from e 