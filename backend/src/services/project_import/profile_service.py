"""
Service for handling consent profile-related operations.
"""
import os
import re
import logging
from typing import List, Tuple, Optional

from src.services.graphql_client import GraphQLClient

# Configure logging
logger = logging.getLogger(__name__)

class ProfileService:
    """Service for handling consent profile-related operations."""
    
    def __init__(self, graphql_client: GraphQLClient):
        """
        Initialize the profile service.
        
        Args:
            graphql_client: The GraphQL client for database operations
        """
        self.graphql_client = graphql_client
    
    def get_consent_profile_folders(self, project_path: str) -> List[Tuple[str, str, str]]:
        """
        Get all consent profile folders from a project folder.
        
        Args:
            project_path: Path to the project folder
            
        Returns:
            List of tuples (profile_id, profile_name, profile_path)
        """
        profile_folders = []
        
        try:
            # List all subdirectories in the project folder
            for item in os.listdir(project_path):
                item_path = os.path.join(project_path, item)
                
                # Skip if not a directory
                if not os.path.isdir(item_path):
                    continue
                
                # Parse profile id and name from folder name
                match = re.match(r'^([^_]+)_(.+)$', item)
                if match:
                    profile_id = match.group(1)
                    profile_name = match.group(2)
                    profile_folders.append((profile_id, profile_name, item_path))
                else:
                    logger.warning(f"Skipping folder with invalid profile format: {item}")
            
            return profile_folders
        except Exception as e:
            logger.error(f"Error scanning profile folders: {str(e)}")
            return []
    
    async def create_consent_profile(self, project_id: str, profile_id: str, profile_name: str) -> Tuple[str, str]:
        """
        Create a consent profile in the database if it doesn't exist.
        
        Args:
            project_id: Project ID
            profile_id: Profile ID from folder name
            profile_name: Profile name from folder name
            
        Returns:
            Tuple of (profile_id, operation) where operation is 'created' or 'unchanged'
        """
        try:
            # Check if profile already exists
            check_query = """
            query GetProfile($profile_id: uuid!) {
                consent_profiles(where: {profile_id: {_eq: $profile_id}}) {
                    profile_id
                }
            }
            """
            
            result = await self.graphql_client.execute_async(check_query, {"profile_id": profile_id})
            
            if result.get("consent_profiles") and len(result["consent_profiles"]) > 0:
                logger.info(f"Profile {profile_id} already exists, skipping creation")
                return profile_id, "unchanged"
            
            # Create profile
            mutation = """
            mutation CreateConsentProfile($profile_id: uuid!, $project_id: uuid!, $person_name: String!) {
                insert_consent_profiles_one(object: {profile_id: $profile_id, project_id: $project_id, person_name: $person_name}) {
                    profile_id
                }
            }
            """
            
            variables = {
                "profile_id": profile_id,
                "project_id": project_id,
                "person_name": profile_name
            }
            
            result = await self.graphql_client.execute_async(mutation, variables)
            
            if result.get("insert_consent_profiles_one") and result["insert_consent_profiles_one"].get("profile_id"):
                logger.info(f"Created consent profile: {profile_name} with ID {profile_id}")
                return profile_id, "created"
            else:
                raise Exception("Failed to create consent profile, unexpected response format")
                
        except Exception as e:
            logger.error(f"Error creating consent profile {profile_id}: {str(e)}")
            raise 