"""
Service for handling project-related operations.
"""
import os
import re
import logging
from typing import List, Tuple, Optional

from src.services.graphql_client import GraphQLClient
from src.utils.datetime_utils import format_for_database
import datetime

# Configure logging
logger = logging.getLogger(__name__)

class ProjectService:
    """Service for handling project-related operations."""
    
    def __init__(self, graphql_client: GraphQLClient):
        """
        Initialize the project service.
        
        Args:
            graphql_client: The GraphQL client for database operations
        """
        self.graphql_client = graphql_client
    
    def get_project_folders(self, base_path: str) -> List[Tuple[str, str, str]]:
        """
        Get all project folders from the consent folder.
        
        Args:
            base_path: Base path to scan for project folders
            
        Returns:
            List of tuples (project_id, project_name, project_path)
        """
        project_folders = []
        
        try:
            # List all subdirectories in the consent folder
            for item in os.listdir(base_path):
                item_path = os.path.join(base_path, item)
                
                # Skip if not a directory
                if not os.path.isdir(item_path):
                    continue
                
                # Parse project id and name from folder name
                match = re.match(r'^([^_]+)_(.+)$', item)
                if match:
                    project_id = match.group(1)
                    project_name = match.group(2)
                    project_folders.append((project_id, project_name, item_path))
                else:
                    logger.warning(f"Skipping folder with invalid project format: {item}")
            
            return project_folders
        except Exception as e:
            logger.error(f"Error scanning project folders: {str(e)}")
            return []
    
    async def create_project(self, project_id: str, project_name: str) -> Tuple[str, str]:
        """
        Create a project in the database if it doesn't exist.
        
        Args:
            project_id: Project ID from folder name
            project_name: Project name from folder name
            
        Returns:
            Tuple of (project_id, operation) where operation is 'created' or 'unchanged'
        """
        try:
            # Check if project already exists
            check_query = """
            query GetProject($project_id: uuid!) {
                projects(where: {project_id: {_eq: $project_id}}) {
                    project_id
                }
            }
            """
            
            result = await self.graphql_client.execute_async(check_query, {"project_id": project_id})
            
            if result.get("projects") and len(result["projects"]) > 0:
                logger.info(f"Project {project_id} already exists, skipping creation")
                return project_id, "unchanged"
            
            # Create project
            mutation = """
            mutation CreateProject($project_id: uuid!, $project_name: String!, $created_at: timestamptz!) {
                insert_projects_one(object: {project_id: $project_id, project_name: $project_name, created_at: $created_at}) {
                    project_id
                }
            }
            """
            
            variables = {
                "project_id": project_id,
                "project_name": project_name,
                "created_at": format_for_database(datetime.datetime.now())
            }
            
            result = await self.graphql_client.execute_async(mutation, variables)
            
            if result.get("insert_projects_one") and result["insert_projects_one"].get("project_id"):
                logger.info(f"Created project: {project_name} with ID {project_id}")
                return project_id, "created"
            else:
                raise Exception("Failed to create project, unexpected response format")
                
        except Exception as e:
            logger.error(f"Error creating project {project_id}: {str(e)}")
            raise 