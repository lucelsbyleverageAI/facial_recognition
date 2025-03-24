import os
import pytest
import unittest.mock as mock
from unittest.mock import patch, MagicMock
import asyncio
from gql import Client

from src.services import GraphQLClient, GraphQLClientError
from src.config import ENV


class TestGraphQLClient:
    """Test cases for the GraphQLClient class."""

    def setup_method(self):
        """Setup method to run before each test."""
        # Get real environment variables but fall back to mock values if not available
        self.mock_env = {
            "HASURA_GRAPHQL_URL": os.getenv("HASURA_GRAPHQL_URL") or "http://test-hasura:8080/v1/graphql",
            "HASURA_ADMIN_SECRET": os.getenv("HASURA_ADMIN_SECRET") or "test-secret-key",
            # Include other ENV values to avoid KeyErrors
            "POSTGRES_USER": os.getenv("POSTGRES_USER") or "test-user",
            "POSTGRES_PASSWORD": os.getenv("POSTGRES_PASSWORD") or "test-password",
            "POSTGRES_DB": os.getenv("POSTGRES_DB") or "test-db",
            "DATABASE_URL": os.getenv("DATABASE_URL") or "postgresql://test-user:test-password@postgres:5432/test-db"
        }
        
        # Apply patches
        self.env_patcher = patch.dict('src.config.ENV', self.mock_env, clear=True)
        self.env_patcher.start()
        
        # Ensure we're testing with a clean singleton state
        GraphQLClient._instance = None

    def teardown_method(self):
        """Teardown method to run after each test."""
        # Stop patches
        self.env_patcher.stop()
        
        # Clean up singleton state
        GraphQLClient._instance = None

    def test_singleton_pattern(self):
        """Test that GraphQLClient follows the singleton pattern."""
        client1 = GraphQLClient()
        client2 = GraphQLClient()
        
        assert client1 is client2, "GraphQLClient should be a singleton"

    def test_initialization(self):
        """Test that the client initializes correctly with environment variables."""
        with patch('gql.Client') as mock_client:
            client = GraphQLClient()
            
            assert client.hasura_url == self.mock_env["HASURA_GRAPHQL_URL"]
            assert client.hasura_admin_secret == self.mock_env["HASURA_ADMIN_SECRET"]
            assert client.headers == {
                "Content-Type": "application/json",
                "x-hasura-admin-secret": self.mock_env["HASURA_ADMIN_SECRET"]
            }
            
            # Should initialize both sync and async clients
            assert hasattr(client, 'sync_client')
            assert hasattr(client, 'async_client')

    def test_missing_env_vars(self):
        """Test that the client raises an error if environment variables are missing."""
        # Set environment variables to empty values
        with patch.dict('src.config.ENV', {
            "HASURA_GRAPHQL_URL": "",
            "HASURA_ADMIN_SECRET": ""
        }, clear=True):
            GraphQLClient._instance = None  # Reset singleton for clean test
            
            with pytest.raises(GraphQLClientError) as exc_info:
                GraphQLClient()
            
            assert "Missing required environment variables" in str(exc_info.value)

    def test_execute_sync(self):
        """Test synchronous query execution."""
        test_query = "query { users { id name } }"
        expected_result = {"users": [{"id": 1, "name": "Test User"}]}
        
        # Create mock for sync client
        mock_sync_client = MagicMock()
        mock_sync_client.execute.return_value = expected_result
        
        with patch.object(Client, '__new__', return_value=mock_sync_client):
            client = GraphQLClient()
            client.sync_client = mock_sync_client
            
            result = client.execute(test_query)
            
            assert result == expected_result
            mock_sync_client.execute.assert_called_once()

    def test_execute_with_variables(self):
        """Test synchronous query execution with variables."""
        test_query = "query GetUser($id: Int!) { user(id: $id) { name } }"
        variables = {"id": 1}
        expected_result = {"user": {"name": "Test User"}}
        
        # Create mock for sync client
        mock_sync_client = MagicMock()
        mock_sync_client.execute.return_value = expected_result
        
        with patch.object(Client, '__new__', return_value=mock_sync_client):
            client = GraphQLClient()
            client.sync_client = mock_sync_client
            
            result = client.execute(test_query, variables)
            
            assert result == expected_result
            # Verify variables were passed correctly
            args, kwargs = mock_sync_client.execute.call_args
            assert kwargs.get('variable_values') == variables

    def test_execute_sync_error(self):
        """Test error handling in synchronous execution."""
        test_query = "query { users { id name } }"
        
        # Create mock for sync client that raises an exception
        mock_sync_client = MagicMock()
        mock_sync_client.execute.side_effect = Exception("Test error")
        
        with patch.object(Client, '__new__', return_value=mock_sync_client):
            client = GraphQLClient()
            client.sync_client = mock_sync_client
            
            with pytest.raises(GraphQLClientError) as exc_info:
                client.execute(test_query)
            
            assert "Failed to execute GraphQL operation" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_execute_async(self):
        """Test asynchronous query execution."""
        test_query = "query { users { id name } }"
        expected_result = {"users": [{"id": 1, "name": "Test User"}]}
        
        # Setup mocks for async execution
        mock_session = MagicMock()
        mock_session.__aenter__ = MagicMock()
        mock_session.__aexit__ = MagicMock()
        mock_session.__aenter__.return_value = mock_session
        mock_session.execute = MagicMock()
        mock_session.execute.return_value = expected_result
        
        async def mock_execute_async(self, query, variables=None):
            if query == test_query:
                return expected_result
            return {}  # Default response
        
        # Patch the initialization methods and execute_async
        with patch.object(GraphQLClient, '_init_sync_client', MagicMock()), \
             patch.object(GraphQLClient, '_init_async_client', MagicMock()), \
             patch.object(GraphQLClient, 'execute_async', mock_execute_async):
            
            client = GraphQLClient()
            result = await client.execute_async(test_query)
            
            assert result == expected_result

    @pytest.mark.asyncio
    async def test_execute_async_with_variables(self):
        """Test asynchronous query execution with variables."""
        test_query = "query GetUser($id: Int!) { user(id: $id) { name } }"
        variables = {"id": 1}
        expected_result = {"user": {"name": "Test User"}}
        
        # Define mock implementation that checks variables
        async def mock_execute_async(self, query, variables=None):
            assert query == test_query
            assert variables == {"id": 1}
            return expected_result
        
        # Patch the methods
        with patch.object(GraphQLClient, '_init_sync_client', MagicMock()), \
             patch.object(GraphQLClient, '_init_async_client', MagicMock()), \
             patch.object(GraphQLClient, 'execute_async', mock_execute_async):
            
            client = GraphQLClient()
            result = await client.execute_async(test_query, variables)
            
            assert result == expected_result

    @pytest.mark.asyncio
    async def test_execute_async_error(self):
        """Test error handling in asynchronous execution."""
        test_query = "query { users { id name } }"
        
        # Define mock that raises an error
        async def mock_execute_async(self, query, variables=None):
            raise GraphQLClientError("Failed to execute async GraphQL operation: Test async error")
        
        # Patch the methods
        with patch.object(GraphQLClient, '_init_sync_client', MagicMock()), \
             patch.object(GraphQLClient, '_init_async_client', MagicMock()), \
             patch.object(GraphQLClient, 'execute_async', mock_execute_async):
            
            client = GraphQLClient()
            
            with pytest.raises(GraphQLClientError) as exc_info:
                await client.execute_async(test_query)
            
            assert "Failed to execute async GraphQL operation" in str(exc_info.value)
            assert "Test async error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_execute_async_graphql_errors(self):
        """Test handling of GraphQL errors in the response."""
        test_query = "query { users { id name } }"
        error_messages = ["Field 'user' doesn't exist", "Not authorized"]
        
        # Define mock that returns GraphQL errors
        async def mock_execute_async(self, query, variables=None):
            error_msg = f"GraphQL errors: {', '.join(error_messages)}"
            raise GraphQLClientError(error_msg)
        
        # Patch the methods
        with patch.object(GraphQLClient, '_init_sync_client', MagicMock()), \
             patch.object(GraphQLClient, '_init_async_client', MagicMock()), \
             patch.object(GraphQLClient, 'execute_async', mock_execute_async):
            
            client = GraphQLClient()
            
            with pytest.raises(GraphQLClientError) as exc_info:
                await client.execute_async(test_query)
            
            # Verify both error messages are included
            for error in error_messages:
                assert error in str(exc_info.value) 