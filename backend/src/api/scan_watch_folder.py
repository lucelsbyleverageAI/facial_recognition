import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from uuid import UUID

from src.services.watch_folder_service import scan_watch_folder
from src.schemas.watch_folder import ScanWatchFolderResponse

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api",
    tags=["watch_folders"],
)

class ScanWatchFolderRequest(BaseModel):
    watch_folder_id: UUID
    folder_path: str

@router.post("/scan-watch-folder", response_model=ScanWatchFolderResponse)
async def scan_folder(request: ScanWatchFolderRequest):
    """
    Scans a watch folder for video clips and adds them to the database.
    
    Args:
        request: The request containing watch_folder_id and folder_path
        
    Returns:
        A response with statistics about the scan results
    """
    try:
        logger.info(f"Scanning watch folder: {request.folder_path}")
        result = await scan_watch_folder(str(request.watch_folder_id), request.folder_path)
        logger.info(f"Completed scan of {request.folder_path}: {result.clips_found} found, {result.clips_created} created, {result.clips_updated} updated")
        return result
    except Exception as e:
        logger.exception(f"Error scanning watch folder: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error scanning watch folder: {str(e)}") 