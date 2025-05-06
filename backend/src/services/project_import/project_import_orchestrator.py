"""
Orchestrator for project import operations.
"""
import os
import logging
from typing import Dict, Any, Optional

from .project_service import ProjectService
from .profile_service import ProfileService
from .face_service import FaceService
from src.services.graphql_client import GraphQLClient, GraphQLClientError

# Configure logging
logger = logging.getLogger(__name__)

class ProjectImportOrchestrator:
    """
    Orchestrator for importing projects and their associated profiles and faces.
    Acts as the main entry point for project import operations.
    """
    
    def __init__(self, consent_folder_path: str = None):
        """
        Initialize the project import orchestrator.
        
        Args:
            consent_folder_path: Path to the consent folders. If None, uses the default.
        """
        self.consent_folder_path = consent_folder_path or r"/Users/lucelsby/Documents/repos/chwarel/facial_recognition/Test Inputs/Consent"
        
        # Initialize the GraphQL client
        self.graphql_client = self._initialize_graphql_client()
        
        # Initialize the services
        self.project_service = ProjectService(self.graphql_client)
        self.profile_service = ProfileService(self.graphql_client)
        self.face_service = FaceService(self.graphql_client)
    
    def _initialize_graphql_client(self) -> GraphQLClient:
        """Initialize and return a GraphQL client instance."""
        # Get environment variables directly
        hasura_url = os.getenv("HASURA_GRAPHQL_URL")
        hasura_admin_secret = os.getenv("HASURA_ADMIN_SECRET")
        
        if not hasura_url or not hasura_admin_secret:
            missing_vars = []
            if not hasura_url:
                missing_vars.append("HASURA_GRAPHQL_URL")
            if not hasura_admin_secret:
                missing_vars.append("HASURA_ADMIN_SECRET")
            
            error_msg = f"Missing required environment variables: {' or '.join(missing_vars)}"
            logger.error(error_msg)
            raise GraphQLClientError(error_msg)
        
        # Pass environment variables directly to the GraphQLClient
        try:
            client = GraphQLClient(url=hasura_url, admin_secret=hasura_admin_secret)
            logger.info("GraphQL client initialized successfully")
            return client
        except GraphQLClientError as e:
            logger.error(f"Failed to initialize GraphQL client: {str(e)}")
            raise
    
    async def import_all_project_data(self, consent_folder_path: str = None) -> Dict[str, Any]:
        """
        Import all project data from the filesystem structure.
        
        Args:
            consent_folder_path: Optional path to override the default consent folder path
            
        Returns:
            Dictionary with import statistics
        """
        # Override consent folder path if provided
        if consent_folder_path:
            self.consent_folder_path = consent_folder_path
            
        stats = {
            "projects_found": 0,
            "projects_created": 0,
            "projects_updated": 0,
            "consent_profiles_found": 0, 
            "consent_profiles_created": 0,
            "consent_profiles_updated": 0,
            "consent_images_found": 0,
            "consent_images_created": 0,
            "consent_images_updated": 0,
            "consent_images_with_embeddings_preserved": 0,  # Track preserved embeddings
            "errors": []
        }
        
        try:
            # Validate the consent folder exists
            if not os.path.isdir(self.consent_folder_path):
                error_msg = f"Consent folder not found at: {self.consent_folder_path}"
                logger.error(error_msg)
                stats["errors"].append(error_msg)
                return stats
                
            # Scan for project folders
            project_folders = self.project_service.get_project_folders(self.consent_folder_path)
            stats["projects_found"] = len(project_folders)
            
            # Process each project folder
            for project_id, project_name, project_path in project_folders:
                try:
                    # Create project in database
                    project_db_id, project_operation = await self.project_service.create_project(project_id, project_name)
                    
                    # Update stats based on operation
                    if project_operation == "created":
                        stats["projects_created"] += 1
                    elif project_operation == "unchanged":
                        stats["projects_updated"] += 1
                    
                    # Get consent profile folders
                    profile_folders = self.profile_service.get_consent_profile_folders(project_path)
                    stats["consent_profiles_found"] += len(profile_folders)
                    
                    # Process each consent profile
                    for profile_id, profile_name, profile_path in profile_folders:
                        try:
                            # Create consent profile in database
                            profile_db_id, profile_operation = await self.profile_service.create_consent_profile(
                                project_db_id, profile_id, profile_name
                            )
                            
                            # Update stats based on operation
                            if profile_operation == "created":
                                stats["consent_profiles_created"] += 1
                            elif profile_operation == "unchanged":
                                stats["consent_profiles_updated"] += 1
                            
                            # Get consent face images
                            face_images = self.face_service.get_consent_face_images(profile_path)
                            stats["consent_images_found"] += len(face_images)
                            
                            # Process each face image
                            for face_id, pose_type, image_path in face_images:
                                try:
                                    # Create or update consent face in database
                                    result_id, operation = await self.face_service.create_consent_face(
                                        profile_db_id, face_id, pose_type, image_path
                                    )
                                    
                                    # Check if face has an embedding (after processing)
                                    has_embedding = await self.face_service._check_face_has_embedding(result_id)
                                    
                                    # Update stats based on operation
                                    if operation == "created":
                                        stats["consent_images_created"] += 1
                                    elif operation == "updated":
                                        stats["consent_images_updated"] += 1
                                    elif operation == "unchanged" and has_embedding:
                                        # Count faces where we preserved embeddings
                                        stats["consent_images_with_embeddings_preserved"] += 1
                                        
                                except Exception as e:
                                    error_msg = f"Error importing face {face_id} in profile {profile_id}: {str(e)}"
                                    logger.error(error_msg)
                                    stats["errors"].append(error_msg)
                            
                        except Exception as e:
                            error_msg = f"Error importing profile {profile_id} in project {project_id}: {str(e)}"
                            logger.error(error_msg)
                            stats["errors"].append(error_msg)
                    
                except Exception as e:
                    error_msg = f"Error importing project {project_id}: {str(e)}"
                    logger.error(error_msg)
                    stats["errors"].append(error_msg)
            
            # Add summary logging for preserved embeddings
            logger.info(f"Import complete - Found: {stats['consent_images_found']}, Created: {stats['consent_images_created']}, Updated: {stats['consent_images_updated']}")
            
            return stats
            
        except Exception as e:
            error_msg = f"Unexpected error during import: {str(e)}"
            logger.exception(error_msg)
            stats["errors"].append(error_msg)
            return stats 