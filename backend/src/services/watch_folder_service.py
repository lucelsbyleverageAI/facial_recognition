import os
import logging
import uuid
from pathlib import Path
from typing import List, Dict, Any, Set

from src.services.graphql_client import GraphQLClient
from src.schemas.watch_folder import ScanWatchFolderResponse

# Configure logging
logger = logging.getLogger(__name__)

# Define supported video file extensions
SUPPORTED_VIDEO_EXTENSIONS = {
    '.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', 
    '.webm', '.m4v', '.mpg', '.mpeg', '.3gp', '.3g2',
    '.mxf'  # Material Exchange Format - commonly used in professional broadcast and post-production
}

async def scan_watch_folder(watch_folder_id: str, folder_path: str) -> ScanWatchFolderResponse:
    """
    Scan a watch folder for video clips and add them to the database
    
    Args:
        watch_folder_id: The ID of the watch folder to scan
        folder_path: The path to the folder to scan
        
    Returns:
        A response object with scan results
    """
    logger.info(f"Starting scan of watch folder: {folder_path}")
    
    # Generate a task ID for tracking
    task_id = str(uuid.uuid4())
    
    # Initialize GraphQL client
    graphql_client = GraphQLClient()
    
    # Validate folder path exists
    if not os.path.isdir(folder_path):
        logger.error(f"Folder path does not exist: {folder_path}")
        raise ValueError(f"Folder path does not exist: {folder_path}")
    
    # Get card ID from watch folder ID
    card_id = await get_card_id_by_watch_folder_id(graphql_client, watch_folder_id)
    if not card_id:
        logger.error(f"Could not find card ID for watch folder ID: {watch_folder_id}")
        raise ValueError(f"Could not find card ID for watch folder ID: {watch_folder_id}")
    
    # Find video files in the folder and subfolders
    video_files = find_video_files(folder_path)
    logger.info(f"Found {len(video_files)} video files in {folder_path}")
    
    # Get existing filenames for this card to avoid constraint violations
    existing_filenames = await get_existing_filenames_for_card(graphql_client, card_id)
    logger.info(f"Card already has {len(existing_filenames)} clips")
    
    # Check which files already exist in database for this watch folder
    file_paths = [str(file) for file in video_files]
    existing_clips = await get_existing_clips(graphql_client, watch_folder_id, file_paths)
    
    # Prepare new clips for insertion
    new_clips = []
    duplicate_filenames = []
    
    for file_path in video_files:
        path_str = str(file_path)
        filename = file_path.name
        
        # Skip if the file is already in this watch folder
        if path_str in existing_clips:
            continue
            
        # Check if the filename already exists for this card
        if filename in existing_filenames:
            duplicate_filenames.append(filename)
            logger.warning(f"Skipping file {filename} - already exists for this card")
            continue
            
        new_clips.append({
            'card_id': card_id,
            'watch_folder_id': watch_folder_id,
            'filename': filename,
            'path': path_str,
            'status': 'pending'
        })
    
    # Insert new clips into database
    clips_created = 0
    if new_clips:
        try:
            result = await insert_clips(graphql_client, new_clips)
            clips_created = result.get('affected_rows', 0)
        except Exception as e:
            # Check if it's a unique constraint violation
            if "unique_card_filename" in str(e):
                logger.warning("Some clips were not inserted due to duplicate filenames")
            else:
                raise
    
    # Update watch folder status to 'scanned'
    await update_watch_folder_status(graphql_client, watch_folder_id, 'scanned')
    
    # Create response
    response = ScanWatchFolderResponse(
        task_id=uuid.UUID(task_id),
        status="success",
        clips_found=len(video_files),
        clips_created=clips_created,
        clips_updated=0,  # We're not updating existing clips in this implementation
        watch_folder_path=folder_path,
        duplicate_filenames=duplicate_filenames  # Add this to the response
    )
    
    return response

def find_video_files(folder_path: str) -> List[Path]:
    """
    Find all video files in the given folder and its subfolders
    
    Args:
        folder_path: The path to search for video files
        
    Returns:
        A list of Path objects for the video files found
    """
    video_files = []
    
    # Walk through the directory tree
    for root, _, files in os.walk(folder_path):
        for file in files:
            file_path = Path(os.path.join(root, file))
            if file_path.suffix.lower() in SUPPORTED_VIDEO_EXTENSIONS:
                video_files.append(file_path)
    
    return video_files

async def get_card_id_by_watch_folder_id(graphql_client: GraphQLClient, watch_folder_id: str) -> str:
    """
    Get the card_id associated with a watch_folder_id using GraphQL
    
    Args:
        graphql_client: GraphQL client instance
        watch_folder_id: The ID of the watch folder
        
    Returns:
        The associated card_id or None if not found
    """
    query = """
    query GetCardIdByWatchFolderId($watchFolderId: uuid!) {
        watch_folders_by_pk(watch_folder_id: $watchFolderId) {
            config_id
            card_config {
                card_id
            }
        }
    }
    """
    
    try:
        result = await graphql_client.execute_async(query, {"watchFolderId": watch_folder_id})
        watch_folder = result.get("watch_folders_by_pk")
        
        if watch_folder and watch_folder.get("card_config"):
            return watch_folder["card_config"]["card_id"]
        
        # If the card_config relationship isn't defined, try a second approach
        if watch_folder and watch_folder.get("config_id"):
            # Get the card_id from the card_configs table directly
            config_id = watch_folder["config_id"]
            card_query = """
            query GetCardIdByConfigId($configId: uuid!) {
                card_configs_by_pk(config_id: $configId) {
                    card_id
                }
            }
            """
            card_result = await graphql_client.execute_async(card_query, {"configId": config_id})
            if card_result.get("card_configs_by_pk"):
                return card_result["card_configs_by_pk"]["card_id"]
        
        return None
    except Exception as e:
        logger.error(f"Error getting card_id for watch_folder_id {watch_folder_id}: {str(e)}")
        raise

async def get_existing_clips(graphql_client: GraphQLClient, watch_folder_id: str, file_paths: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Get existing clips in the database for the given watch folder and file paths
    
    Args:
        graphql_client: GraphQL client instance
        watch_folder_id: The ID of the watch folder
        file_paths: List of file paths to check
        
    Returns:
        Dictionary mapping file paths to existing clip records
    """
    query = """
    query GetExistingClips($watchFolderId: uuid!, $paths: [String!]) {
        clips(where: {watch_folder_id: {_eq: $watchFolderId}, path: {_in: $paths}}) {
            clip_id
            card_id
            watch_folder_id
            filename
            path
            status
        }
    }
    """
    
    try:
        result = await graphql_client.execute_async(query, {
            "watchFolderId": watch_folder_id,
            "paths": file_paths
        })
        
        existing_clips = {}
        for clip in result.get("clips", []):
            existing_clips[clip["path"]] = clip
        
        return existing_clips
    except Exception as e:
        logger.error(f"Error getting existing clips for watch_folder_id {watch_folder_id}: {str(e)}")
        raise

async def insert_clips(graphql_client: GraphQLClient, clips: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Insert new clips into the database using GraphQL
    
    Args:
        graphql_client: GraphQL client instance
        clips: List of clip objects to insert
        
    Returns:
        GraphQL mutation result
    """
    mutation = """
    mutation InsertClips($objects: [clips_insert_input!]!) {
        insert_clips(objects: $objects) {
            affected_rows
            returning {
                clip_id
                filename
            }
        }
    }
    """
    
    try:
        result = await graphql_client.execute_async(mutation, {"objects": clips})
        return result.get("insert_clips", {})
    except Exception as e:
        logger.error(f"Error inserting clips: {str(e)}")
        raise

async def update_watch_folder_status(graphql_client: GraphQLClient, watch_folder_id: str, status: str) -> bool:
    """
    Update the status of a watch folder using GraphQL
    
    Args:
        graphql_client: GraphQL client instance
        watch_folder_id: The ID of the watch folder
        status: The new status
        
    Returns:
        True if successful, False otherwise
    """
    mutation = """
    mutation UpdateWatchFolderStatus($watchFolderId: uuid!, $status: String!) {
        update_watch_folders_by_pk(
            pk_columns: {watch_folder_id: $watchFolderId}, 
            _set: {status: $status}
        ) {
            watch_folder_id
        }
    }
    """
    
    try:
        result = await graphql_client.execute_async(mutation, {
            "watchFolderId": watch_folder_id,
            "status": status
        })
        
        return result.get("update_watch_folders_by_pk") is not None
    except Exception as e:
        logger.error(f"Error updating watch folder status: {str(e)}")
        return False

async def get_existing_filenames_for_card(graphql_client: GraphQLClient, card_id: str) -> set:
    """
    Get all existing filenames for a card to avoid unique constraint violations
    
    Args:
        graphql_client: GraphQL client instance
        card_id: The ID of the card
        
    Returns:
        Set of existing filenames
    """
    query = """
    query GetExistingFilenames($cardId: uuid!) {
        clips(where: {card_id: {_eq: $cardId}}) {
            filename
        }
    }
    """
    
    try:
        result = await graphql_client.execute_async(query, {"cardId": card_id})
        filenames = set()
        for clip in result.get("clips", []):
            filenames.add(clip["filename"])
        return filenames
    except Exception as e:
        logger.error(f"Error getting existing filenames for card {card_id}: {str(e)}")
        raise

async def get_watch_folder_path(graphql_client: GraphQLClient, watch_folder_id: str) -> str:
    """
    Get the path of a watch folder from the database.
    
    Args:
        graphql_client: GraphQL client instance
        watch_folder_id: ID of the watch folder
        
    Returns:
        The folder path or None if not found
    """
    try:
        logger.info(f"Getting folder path for watch folder with ID: {watch_folder_id}")
        
        # Query to get the folder path by watch folder ID - notice the variable name is watch_folder_id not watchFolderId
        query = """
        query GetWatchFolderPath($watch_folder_id: uuid!) {
            watch_folders_by_pk(watch_folder_id: $watch_folder_id) {
                folder_path
            }
        }
        """
        
        # Debug the query and variables
        logger.debug(f"Query: {query}")
        logger.debug(f"Variables: {{'watch_folder_id': {watch_folder_id}}}")
        
        # Try a direct database query with a more verbose debug output
        try:
            # Execute the query - Make sure the variable name matches the query parameter exactly
            result = await graphql_client.execute_async(query, {"watch_folder_id": watch_folder_id})
            
            # Debug the raw response
            logger.info(f"GraphQL raw response: {result}")
            
            # Handle both possible response structures (with or without 'data' key)
            if isinstance(result, dict):
                # Check if the result has a 'data' key (some GraphQL clients wrap the response)
                if "data" in result and result["data"] and "watch_folders_by_pk" in result["data"]:
                    folder = result["data"]["watch_folders_by_pk"]
                    logger.info(f"Found folder in data.watch_folders_by_pk: {folder}")
                    if folder:
                        return folder["folder_path"]
                
                # Check if the result has the response directly (no data wrapper)
                elif "watch_folders_by_pk" in result:
                    folder = result["watch_folders_by_pk"]
                    logger.info(f"Found folder in watch_folders_by_pk: {folder}")
                    if folder:
                        return folder["folder_path"]
                
                # Log keys to help diagnose structure issues
                logger.warning(f"Response has unexpected structure. Keys: {result.keys()}")
                
                # Fall back to a direct SQL query if GraphQL fails
                logger.info("Attempting direct query to list all watch folder IDs for debugging")
                list_query = """
                query ListWatchFolders {
                    watch_folders {
                        watch_folder_id
                        folder_path
                    }
                }
                """
                list_result = await graphql_client.execute_async(list_query, {})
                logger.info(f"Available watch folders: {list_result}")
            else:
                logger.warning(f"Unexpected response type: {type(result)}")
            
            logger.warning(f"Watch folder not found for ID: {watch_folder_id}")
            return None
            
        except Exception as inner_e:
            logger.exception(f"Inner exception in GraphQL query: {str(inner_e)}")
            return None
            
    except Exception as e:
        logger.exception(f"Error getting watch folder path: {str(e)}")
        return None 