"""
Orchestrator for S3-based project import operations.
"""
import logging
import os
from typing import Dict, Any, Optional

from src.services.aws_s3_service import AWSS3Service
from .project_service import ProjectService
from .profile_service import ProfileService
from .face_service import FaceService
from src.services.graphql_client import GraphQLClient, GraphQLClientError

logger = logging.getLogger(__name__)

def download_s3_image_to_local(s3_service, s3_key, local_base_dir):
    """
    Download an image from S3 to the local consent directory, preserving folder structure.
    Returns the local file path.
    """
    # Remove any leading slashes from s3_key
    s3_key = s3_key.lstrip('/')
    local_path = os.path.join(local_base_dir, s3_key)
    local_dir = os.path.dirname(local_path)
    os.makedirs(local_dir, exist_ok=True)
    image_bytes = s3_service.get_file_content(s3_key)
    with open(local_path, 'wb') as f:
        f.write(image_bytes)
    return local_path

class S3ProjectImportOrchestrator:
    """
    Orchestrator for importing projects and their associated profiles and faces from S3.
    """
    def __init__(self, s3_service: Optional[AWSS3Service] = None, s3_prefix: str = ""):
        """
        Initialize the S3 project import orchestrator.
        Args:
            s3_service: Optional AWSS3Service instance. If None, a default will be created.
            s3_prefix: Optional prefix within the S3 bucket to scan.
        """
        self.s3_service = s3_service or AWSS3Service()
        self.s3_prefix = s3_prefix
        self.graphql_client = self._initialize_graphql_client()
        self.project_service = ProjectService(self.graphql_client)
        self.profile_service = ProfileService(self.graphql_client)
        self.face_service = FaceService(self.graphql_client)

    def _initialize_graphql_client(self) -> GraphQLClient:
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
        try:
            client = GraphQLClient(url=hasura_url, admin_secret=hasura_admin_secret)
            logger.info("GraphQL client initialized successfully (S3)")
            return client
        except GraphQLClientError as e:
            logger.error(f"Failed to initialize GraphQL client: {str(e)}")
            raise

    async def import_all_project_data(self, s3_prefix: Optional[str] = None) -> Dict[str, Any]:
        """
        Import all project data from the S3 bucket structure.
        Args:
            s3_prefix: Optional prefix to override the default S3 prefix
        Returns:
            Dictionary with import statistics
        """
        prefix = s3_prefix if s3_prefix is not None else self.s3_prefix
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
        import re
        LOCAL_IMAGE_BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../consent'))
        try:
            # List top-level folders (projects) in the S3 bucket
            project_folders = self.s3_service.list_folders(prefix=prefix)
            # Check if any folders match the project pattern
            valid_project_folders = [f for f in project_folders if re.match(r'^([^_]+)_(.+)$', f["name"])]
            if not valid_project_folders and len(project_folders) == 1:
                # Descend into the single folder (e.g., 'Consent/')
                base_folder = project_folders[0]["path"]
                logger.info(f"Descending into base folder: {base_folder}")
                project_folders = self.s3_service.list_folders(prefix=base_folder)
            stats["projects_found"] = len(project_folders)
            for project_folder in project_folders:
                try:
                    project_name_full = project_folder["name"]
                    project_path = project_folder["path"]
                    match = re.match(r'^([^_]+)_(.+)$', project_name_full)
                    if not match:
                        logger.warning(f"Skipping folder with invalid project format: {project_name_full}")
                        continue
                    project_id = match.group(1)
                    project_name = match.group(2)
                    # Create project in database
                    project_db_id, project_operation = await self.project_service.create_project(project_id, project_name)
                    if project_operation == "created":
                        stats["projects_created"] += 1
                    elif project_operation == "unchanged":
                        stats["projects_updated"] += 1
                    # List profile folders within the project
                    profile_folders = self.s3_service.list_folders(prefix=project_path)
                    stats["consent_profiles_found"] += len(profile_folders)
                    for profile_folder in profile_folders:
                        try:
                            profile_name_full = profile_folder["name"]
                            profile_path = profile_folder["path"]
                            match = re.match(r'^([^_]+)_(.+)$', profile_name_full)
                            if not match:
                                logger.warning(f"Skipping folder with invalid profile format: {profile_name_full}")
                                continue
                            profile_id = match.group(1)
                            profile_name = match.group(2)
                            # Create consent profile in database
                            profile_db_id, profile_operation = await self.profile_service.create_consent_profile(
                                project_db_id, profile_id, profile_name
                            )
                            if profile_operation == "created":
                                stats["consent_profiles_created"] += 1
                            elif profile_operation == "unchanged":
                                stats["consent_profiles_updated"] += 1
                            # List files (images) within the profile folder
                            face_images = self.s3_service.list_files(prefix=profile_path)
                            stats["consent_images_found"] += len(face_images)
                            for face_file in face_images:
                                try:
                                    file_name = face_file["name"]
                                    file_path = face_file["path"]  # S3 key
                                    match = re.match(r'^([^_]+)_([FS]).*$', file_name)
                                    if match:
                                        face_id = match.group(1)
                                        pose_type = match.group(2)
                                    else:
                                        if file_name.startswith('F') or file_name.startswith('S'):
                                            pose_type = file_name[0]
                                            import uuid
                                            face_id = str(uuid.uuid4())
                                        else:
                                            logger.warning(f"Skipping file with invalid face format: {file_name}")
                                            continue
                                    # Download S3 image to local consent directory
                                    local_path = download_s3_image_to_local(
                                        self.s3_service, file_path, LOCAL_IMAGE_BASE_DIR
                                    )
                                    result_id, operation = await self.face_service.create_consent_face(
                                        profile_db_id, face_id, pose_type, local_path
                                    )
                                    has_embedding = await self.face_service._check_face_has_embedding(result_id)
                                    if operation == "created":
                                        stats["consent_images_created"] += 1
                                    elif operation == "updated":
                                        stats["consent_images_updated"] += 1
                                    elif operation == "unchanged" and has_embedding:
                                        stats["consent_images_with_embeddings_preserved"] += 1
                                except Exception as e:
                                    error_msg = f"Error importing face {file_name} in profile {profile_name_full}: {str(e)}"
                                    logger.error(error_msg)
                                    stats["errors"].append(error_msg)
                        except Exception as e:
                            error_msg = f"Error importing profile {profile_name_full} in project {project_name_full}: {str(e)}"
                            logger.error(error_msg)
                            stats["errors"].append(error_msg)
                except Exception as e:
                    error_msg = f"Error importing project {project_name_full}: {str(e)}"
                    logger.error(error_msg)
                    stats["errors"].append(error_msg)
            logger.info(f"S3 import complete - Found: {stats['consent_images_found']}, Created: {stats['consent_images_created']}, Updated: {stats['consent_images_updated']}")
            return stats
        except Exception as e:
            error_msg = f"Unexpected error during S3 import: {str(e)}"
            logger.exception(error_msg)
            stats["errors"].append(error_msg)
            return stats 