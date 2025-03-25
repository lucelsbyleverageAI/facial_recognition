"""
Service for handling consent face-related operations.
"""
import os
import re
import uuid
import logging
import datetime
from typing import List, Tuple, Set, Optional

from src.services.graphql_client import GraphQLClient
from src.utils.datetime_utils import format_for_database, parse_datetime

# Configure logging
logger = logging.getLogger(__name__)

class FaceService:
    """Service for handling consent face-related operations."""
    
    # Valid image extensions
    VALID_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.gif'}
    
    # Valid pose types
    VALID_POSE_TYPES = {'F', 'S'}  # F = Front, S = Side
    
    def __init__(self, graphql_client: GraphQLClient):
        """
        Initialize the face service.
        
        Args:
            graphql_client: The GraphQL client for database operations
        """
        self.graphql_client = graphql_client
    
    def get_consent_face_images(self, profile_path: str) -> List[Tuple[str, str, str]]:
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
    
    async def create_consent_face(self, profile_id: str, face_id: str, pose_type: str, image_path: str) -> Tuple[str, str]:
        """
        Create or update a consent face in the database.
        
        Args:
            profile_id: Profile ID
            face_id: Face ID from filename
            pose_type: Pose type (F or S)
            image_path: Path to the image file
            
        Returns:
            Tuple of (face_id, operation) where operation is 'created', 'updated', or 'unchanged'
        """
        try:
            # Check if pose type is valid
            if pose_type not in self.VALID_POSE_TYPES:
                raise ValueError(f"Invalid pose type: {pose_type}")
            
            # Get file modification time
            mod_time = os.path.getmtime(image_path)
            last_updated = datetime.datetime.fromtimestamp(mod_time).astimezone()
            
            # 1. First check if face with the same image path already exists (regardless of ID)
            existing_face_id = await self._check_face_by_image_path(image_path)
            if existing_face_id:
                # Check if the image has been modified since last update
                db_last_updated = await self._get_face_last_updated(existing_face_id)
                
                # If file has been modified since last database update or no last_updated is stored
                if db_last_updated is None or last_updated > db_last_updated:
                    # Update the face with new timestamp and reset face_embedding
                    updated = await self._update_face(existing_face_id, last_updated)
                    if updated:
                        logger.info(f"Updated consent face with ID {existing_face_id} due to modified image")
                        return existing_face_id, "updated"
                    else:
                        raise Exception("Failed to update consent face")
                else:
                    logger.info(f"Face {existing_face_id} already exists with up-to-date image, skipping")
                    return existing_face_id, "unchanged"
            
            # 2. Otherwise, check if a face with this ID exists but with a different path
            if await self._check_face_by_id(face_id):
                logger.warning(f"Face ID {face_id} already exists but with a different image path. Using a new ID.")
                # Generate a new UUID for this face since the ID is already used
                face_id = str(uuid.uuid4())
            
            # 3. Create a new face
            new_face_id = await self._create_new_face(face_id, profile_id, image_path, pose_type, last_updated)
            if new_face_id:
                logger.info(f"Created consent face with ID {face_id} and pose type {pose_type}")
                return new_face_id, "created"
            else:
                raise Exception("Failed to create consent face")
                
        except Exception as e:
            logger.error(f"Error creating/updating consent face {face_id}: {str(e)}")
            raise
    
    async def _check_face_by_image_path(self, image_path: str) -> Optional[str]:
        """
        Check if a face with the given image path exists.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Face ID if exists, None otherwise
        """
        query = """
        query GetFaceByPath($image_path: String!) {
            consent_faces(where: {face_image_path: {_eq: $image_path}}) {
                consent_face_id
            }
        }
        """
        
        result = await self.graphql_client.execute_async(query, {"image_path": image_path})
        
        if result.get("consent_faces") and len(result["consent_faces"]) > 0:
            return result["consent_faces"][0]["consent_face_id"]
        
        return None
    
    async def _get_face_last_updated(self, face_id: str) -> Optional[datetime.datetime]:
        """
        Get the last_updated timestamp for a face.
        
        Args:
            face_id: Face ID
            
        Returns:
            Datetime of last update if exists, None otherwise
        """
        query = """
        query GetFaceLastUpdated($face_id: uuid!) {
            consent_faces_by_pk(consent_face_id: $face_id) {
                last_updated
            }
        }
        """
        
        result = await self.graphql_client.execute_async(query, {"face_id": face_id})
        
        if result.get("consent_faces_by_pk") and result["consent_faces_by_pk"].get("last_updated"):
            try:
                # Use the robust parse_datetime utility for parsing
                return parse_datetime(result["consent_faces_by_pk"]["last_updated"])
            except (ValueError, TypeError) as e:
                logger.warning(f"Failed to parse last_updated from database: {e}")
                return None
        
        return None
    
    async def _update_face(self, face_id: str, last_updated: datetime.datetime) -> bool:
        """
        Update a face with a new last_updated timestamp and reset face_embedding.
        
        Args:
            face_id: Face ID
            last_updated: New last_updated timestamp
            
        Returns:
            True if successful, False otherwise
        """
        mutation = """
        mutation UpdateConsentFace($face_id: uuid!, $last_updated: timestamptz!) {
            update_consent_faces_by_pk(
                pk_columns: {consent_face_id: $face_id}, 
                _set: {last_updated: $last_updated, face_embedding: null}
            ) {
                consent_face_id
            }
        }
        """
        
        variables = {
            "face_id": face_id,
            "last_updated": format_for_database(last_updated)
        }
        
        result = await self.graphql_client.execute_async(mutation, variables)
        
        return (result.get("update_consent_faces_by_pk") and 
                result["update_consent_faces_by_pk"].get("consent_face_id") is not None)
    
    async def _check_face_by_id(self, face_id: str) -> bool:
        """
        Check if a face with the given ID exists.
        
        Args:
            face_id: Face ID
            
        Returns:
            True if exists, False otherwise
        """
        query = """
        query GetFaceById($face_id: uuid!) {
            consent_faces(where: {consent_face_id: {_eq: $face_id}}) {
                consent_face_id
            }
        }
        """
        
        result = await self.graphql_client.execute_async(query, {"face_id": face_id})
        
        return result.get("consent_faces") and len(result["consent_faces"]) > 0
    
    async def _create_new_face(self, face_id: str, profile_id: str, image_path: str, 
                              pose_type: str, last_updated: datetime.datetime) -> Optional[str]:
        """
        Create a new consent face.
        
        Args:
            face_id: Face ID
            profile_id: Profile ID
            image_path: Path to the image file
            pose_type: Pose type
            last_updated: Last updated timestamp
            
        Returns:
            Face ID if created successfully, None otherwise
        """
        mutation = """
        mutation CreateConsentFace($face_id: uuid!, $profile_id: uuid!, $image_path: String!, $pose_type: String!, $last_updated: timestamptz!) {
            insert_consent_faces_one(object: {
                consent_face_id: $face_id, 
                profile_id: $profile_id, 
                face_image_path: $image_path, 
                pose_type: $pose_type,
                last_updated: $last_updated
            }) {
                consent_face_id
            }
        }
        """
        
        variables = {
            "face_id": face_id,
            "profile_id": profile_id,
            "image_path": image_path,
            "pose_type": pose_type,
            "last_updated": format_for_database(last_updated)
        }
        
        result = await self.graphql_client.execute_async(mutation, variables)
        
        if result.get("insert_consent_faces_one") and result["insert_consent_faces_one"].get("consent_face_id"):
            return result["insert_consent_faces_one"]["consent_face_id"]
        
        return None 