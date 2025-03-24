import os
import re
import logging
import uuid
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
import imghdr  # For image type detection
import datetime

from src.services.graphql_client import GraphQLClient, GraphQLClientError
from src.utils.datetime_utils import format_for_database

# Configure logging
logger = logging.getLogger(__name__)

class ProjectImportService:
    """Service for importing projects from a filesystem structure."""
    
    # Valid image extensions
    VALID_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.gif'}
    
    # Valid pose types
    VALID_POSE_TYPES = {'F', 'S'}  # F = Front, S = Side
    
    def __init__(self, consent_folder_path: str = None):
        """
        Initialize the project import service.
        
        Args:
            consent_folder_path: Path to the consent folders. If None, uses the default.
        """
        self.consent_folder_path = consent_folder_path or r"C:\Users\LucElsby\Documents\code_repos\chwarel\facial_recognition\Test Inputs\Consent"
        
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
            self.graphql_client = GraphQLClient(url=hasura_url, admin_secret=hasura_admin_secret)
            logger.info("GraphQL client initialized successfully")
        except GraphQLClientError as e:
            logger.error(f"Failed to initialize GraphQL client: {str(e)}")
            raise
        
    async def import_all_project_data(self) -> Dict[str, Any]:
        """
        Import all project data from the filesystem structure.
        
        Returns:
            Dictionary with import statistics
        """
        stats = {
            "projects_found": 0,
            "projects_imported": 0,
            "profiles_found": 0, 
            "profiles_imported": 0,
            "faces_found": 0,
            "faces_imported": 0,
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
            project_folders = self._get_project_folders()
            stats["projects_found"] = len(project_folders)
            
            # Process each project folder
            for project_id, project_name, project_path in project_folders:
                try:
                    # Create project in database
                    project_db_id = await self._create_project(project_id, project_name)
                    
                    # Get consent profile folders
                    profile_folders = self._get_consent_profile_folders(project_path)
                    stats["profiles_found"] += len(profile_folders)
                    
                    # Process each consent profile
                    for profile_id, profile_name, profile_path in profile_folders:
                        try:
                            # Create consent profile in database
                            profile_db_id = await self._create_consent_profile(project_db_id, profile_id, profile_name)
                            
                            # Get consent face images
                            face_images = self._get_consent_face_images(profile_path)
                            stats["faces_found"] += len(face_images)
                            
                            # Process each face image
                            for face_id, pose_type, image_path in face_images:
                                try:
                                    # Create consent face in database
                                    await self._create_consent_face(profile_db_id, face_id, pose_type, image_path)
                                    stats["faces_imported"] += 1
                                except Exception as e:
                                    error_msg = f"Error importing face {face_id} in profile {profile_id}: {str(e)}"
                                    logger.error(error_msg)
                                    stats["errors"].append(error_msg)
                            
                            stats["profiles_imported"] += 1
                        except Exception as e:
                            error_msg = f"Error importing profile {profile_id} in project {project_id}: {str(e)}"
                            logger.error(error_msg)
                            stats["errors"].append(error_msg)
                    
                    stats["projects_imported"] += 1
                except Exception as e:
                    error_msg = f"Error importing project {project_id}: {str(e)}"
                    logger.error(error_msg)
                    stats["errors"].append(error_msg)
            
            return stats
            
        except Exception as e:
            error_msg = f"Unexpected error during import: {str(e)}"
            logger.exception(error_msg)
            stats["errors"].append(error_msg)
            return stats
    
    def _get_project_folders(self) -> List[Tuple[str, str, str]]:
        """
        Get all project folders from the consent folder.
        
        Returns:
            List of tuples (project_id, project_name, project_path)
        """
        project_folders = []
        
        try:
            # List all subdirectories in the consent folder
            for item in os.listdir(self.consent_folder_path):
                item_path = os.path.join(self.consent_folder_path, item)
                
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
    
    def _get_consent_profile_folders(self, project_path: str) -> List[Tuple[str, str, str]]:
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
    
    def _get_consent_face_images(self, profile_path: str) -> List[Tuple[str, str, str]]:
        """
        Get all consent face images from a profile folder.
        
        Args:
            profile_path: Path to the profile folder
            
        Returns:
            List of tuples (face_id, pose_type, image_path)
        """
        face_images = []
        
        try:
            # List all files in the profile folder
            for item in os.listdir(profile_path):
                item_path = os.path.join(profile_path, item)
                
                # Skip if not a file
                if not os.path.isfile(item_path):
                    continue
                
                # Check if it's an image file
                file_ext = os.path.splitext(item)[1].lower()
                if file_ext not in self.VALID_IMAGE_EXTENSIONS:
                    continue
                
                # Try to parse face id and pose type from filename
                match = re.match(r'^([^_]+)_([FS]).*$', item)
                if match:
                    face_id = match.group(1)
                    pose_type = match.group(2)
                    face_images.append((face_id, pose_type, item_path))
                else:
                    # Check if the filename is just a pose type
                    if item.startswith('F') or item.startswith('S'):
                        pose_type = item[0]
                        face_id = str(uuid.uuid4())  # Generate a UUID for the face
                        face_images.append((face_id, pose_type, item_path))
                    else:
                        logger.warning(f"Skipping file with invalid face format: {item}")
            
            return face_images
        except Exception as e:
            logger.error(f"Error scanning face images: {str(e)}")
            return []
    
    async def _create_project(self, project_id: str, project_name: str) -> str:
        """
        Create a project in the database.
        
        Args:
            project_id: Project ID from folder name
            project_name: Project name from folder name
            
        Returns:
            Database ID of the created project
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
                return project_id
            
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
                return project_id
            else:
                raise Exception("Failed to create project, unexpected response format")
                
        except Exception as e:
            logger.error(f"Error creating project {project_id}: {str(e)}")
            raise
    
    async def _create_consent_profile(self, project_id: str, profile_id: str, profile_name: str) -> str:
        """
        Create a consent profile in the database.
        
        Args:
            project_id: Project ID 
            profile_id: Profile ID from folder name
            profile_name: Profile name from folder name
            
        Returns:
            Database ID of the created consent profile
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
                return profile_id
            
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
                return profile_id
            else:
                raise Exception("Failed to create consent profile, unexpected response format")
                
        except Exception as e:
            logger.error(f"Error creating consent profile {profile_id}: {str(e)}")
            raise
    
    async def _create_consent_face(self, profile_id: str, face_id: str, pose_type: str, image_path: str) -> str:
        """
        Create a consent face in the database.
        
        Args:
            profile_id: Profile ID
            face_id: Face ID from filename
            pose_type: Pose type (F or S)
            image_path: Path to the image file
            
        Returns:
            Database ID of the created consent face
        """
        try:
            # Check if pose type is valid
            if pose_type not in self.VALID_POSE_TYPES:
                raise ValueError(f"Invalid pose type: {pose_type}")
            
            # Check if face already exists
            check_query = """
            query GetFace($face_id: uuid!) {
                consent_faces(where: {consent_face_id: {_eq: $face_id}}) {
                    consent_face_id
                }
            }
            """
            
            result = await self.graphql_client.execute_async(check_query, {"face_id": face_id})
            
            if result.get("consent_faces") and len(result["consent_faces"]) > 0:
                logger.info(f"Face {face_id} already exists, skipping creation")
                return face_id
            
            # Create face
            mutation = """
            mutation CreateConsentFace($face_id: uuid!, $profile_id: uuid!, $image_path: String!, $pose_type: String!) {
                insert_consent_faces_one(object: {
                    consent_face_id: $face_id, 
                    profile_id: $profile_id, 
                    face_image_path: $image_path, 
                    pose_type: $pose_type
                }) {
                    consent_face_id
                }
            }
            """
            
            variables = {
                "face_id": face_id,
                "profile_id": profile_id,
                "image_path": image_path,
                "pose_type": pose_type
            }
            
            result = await self.graphql_client.execute_async(mutation, variables)
            
            if result.get("insert_consent_faces_one") and result["insert_consent_faces_one"].get("consent_face_id"):
                logger.info(f"Created consent face with ID {face_id} and pose type {pose_type}")
                return face_id
            else:
                raise Exception("Failed to create consent face, unexpected response format")
                
        except Exception as e:
            logger.error(f"Error creating consent face {face_id}: {str(e)}")
            raise 