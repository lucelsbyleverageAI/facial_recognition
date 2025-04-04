import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional

from src.services.watch_folder_monitor import start_watch_folder_monitoring, stop_watch_folder_monitoring
from src.services.graphql_client import GraphQLClient
from src.services.watch_folder_service import get_watch_folder_path

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api",
    tags=["watch_folders"],
)

class StartMonitoringRequest(BaseModel):
    """Request model for starting watch folder monitoring"""
    watch_folder_id: UUID = Field(..., description="ID of the watch folder to monitor")
    inactivity_timeout_minutes: int = Field(30, description="Number of minutes of inactivity before stopping monitoring")

class StartMonitoringResponse(BaseModel):
    """Response model for starting watch folder monitoring"""
    status: str = Field(..., description="Status of the operation")
    watch_folder_id: UUID = Field(..., description="ID of the watch folder being monitored")
    monitoring_status: str = Field(..., description="Current monitoring status")
    message: str = Field(..., description="Description of the result")
    inactivity_timeout_minutes: int = Field(..., description="Number of minutes of inactivity before stopping")

class StopMonitoringRequest(BaseModel):
    """Request model for stopping watch folder monitoring"""
    watch_folder_id: UUID = Field(..., description="ID of the watch folder to stop monitoring")

class StopMonitoringResponse(BaseModel):
    """Response model for stopping watch folder monitoring"""
    status: str = Field(..., description="Status of the operation")
    watch_folder_id: UUID = Field(..., description="ID of the watch folder")
    monitoring_status: str = Field(..., description="Current monitoring status")
    message: str = Field(..., description="Description of the result")

@router.post("/start-watch-folder-monitoring", response_model=StartMonitoringResponse)
async def start_monitoring(request: StartMonitoringRequest):
    """
    Start monitoring a watch folder for new video clips.
    
    Args:
        request: The request containing the watch folder ID and timeout
        
    Returns:
        A response with the monitoring status
    """
    try:
        watch_folder_id = str(request.watch_folder_id)
        logger.info(f"Starting monitoring for watch folder: {watch_folder_id}")
        
        # Get the folder path from the database
        graphql_client = GraphQLClient()
        logger.info(f"Fetching path for watch folder ID: {watch_folder_id}")
        folder_path = await get_watch_folder_path(graphql_client, watch_folder_id)
        
        logger.info(f"Result from get_watch_folder_path: {folder_path}")
        
        if not folder_path:
            logger.error(f"Watch folder not found: {watch_folder_id}")
            raise HTTPException(status_code=404, detail=f"Watch folder not found: {watch_folder_id}")
            
        # Start the monitoring process
        result = await start_watch_folder_monitoring(
            watch_folder_id, 
            folder_path, 
            request.inactivity_timeout_minutes
        )
        
        # Return response
        return StartMonitoringResponse(
            status="success",
            watch_folder_id=request.watch_folder_id,
            monitoring_status="active",
            message="Watch folder monitoring started",
            inactivity_timeout_minutes=request.inactivity_timeout_minutes
        )
        
    except Exception as e:
        logger.exception(f"Error starting watch folder monitoring: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error starting watch folder monitoring: {str(e)}")

@router.post("/stop-watch-folder-monitoring", response_model=StopMonitoringResponse)
async def stop_monitoring(request: StopMonitoringRequest):
    """
    Stop monitoring a watch folder.
    
    Args:
        request: The request containing the watch folder ID
        
    Returns:
        A response with the monitoring status
    """
    try:
        watch_folder_id = str(request.watch_folder_id)
        logger.info(f"Stopping monitoring for watch folder: {watch_folder_id}")
        
        # Stop the monitoring process
        result = await stop_watch_folder_monitoring(watch_folder_id)
        
        # Return response
        return StopMonitoringResponse(
            status="success",
            watch_folder_id=request.watch_folder_id,
            monitoring_status="idle",
            message="Watch folder monitoring stopped"
        )
        
    except Exception as e:
        logger.exception(f"Error stopping watch folder monitoring: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error stopping watch folder monitoring: {str(e)}") 