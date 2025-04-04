import os
import asyncio
import logging
import time
from pathlib import Path
from typing import Dict, Set, Optional, List
from datetime import datetime

from src.services.graphql_client import GraphQLClient
from src.services.watch_folder_service import (
    get_card_id_by_watch_folder_id, 
    update_watch_folder_status,
    SUPPORTED_VIDEO_EXTENSIONS
)

# Configure logging
logger = logging.getLogger(__name__)

# Global registry for active monitoring tasks
active_monitors: Dict[str, 'WatchFolderMonitor'] = {}

class WatchFolderMonitor:
    """
    Service for monitoring a watch folder for new video files.
    Automatically adds new clips to the database when detected.
    """
    
    def __init__(self, watch_folder_id: str, folder_path: str, inactivity_timeout_minutes: int = 30):
        """
        Initialize a new watch folder monitor.
        
        Args:
            watch_folder_id: The ID of the watch folder to monitor
            folder_path: The path to the folder to monitor
            inactivity_timeout_minutes: Number of minutes of inactivity before stopping monitoring
        """
        self.watch_folder_id = watch_folder_id
        self.folder_path = folder_path
        self.inactivity_timeout_minutes = inactivity_timeout_minutes
        self.graphql_client = GraphQLClient()
        self.running = False
        self.task: Optional[asyncio.Task] = None
        self.known_files: Set[str] = set()
        self.last_activity_time = time.time()
        self.card_id: Optional[str] = None
    
    async def start(self):
        """Start monitoring the folder for new video files."""
        if self.running:
            logger.warning(f"Monitor for watch folder {self.watch_folder_id} is already running")
            return
        
        try:
            # Get the card ID for this watch folder
            self.card_id = await get_card_id_by_watch_folder_id(self.graphql_client, self.watch_folder_id)
            if not self.card_id:
                raise ValueError(f"Could not find card ID for watch folder {self.watch_folder_id}")
            
            # Update watch folder status to active
            await update_watch_folder_status(self.graphql_client, self.watch_folder_id, "active")
            
            # Initial scan to populate known files
            self.known_files = await self._get_existing_files()
            
            # Start the monitoring task
            self.running = True
            self.task = asyncio.create_task(self._monitor_loop())
            
            # Register this monitor in the global registry
            active_monitors[self.watch_folder_id] = self
            
            logger.info(f"Started monitoring watch folder {self.watch_folder_id} at {self.folder_path}")
            return {"status": "success", "message": "Watch folder monitoring started"}
        
        except Exception as e:
            logger.exception(f"Error starting watch folder monitor: {str(e)}")
            await self._set_error_status(f"Failed to start monitoring: {str(e)}")
            raise
    
    async def stop(self):
        """Stop monitoring the folder."""
        if not self.running:
            logger.warning(f"Monitor for watch folder {self.watch_folder_id} is not running")
            return
        
        try:
            self.running = False
            
            # Cancel the task
            if self.task and not self.task.done():
                self.task.cancel()
                try:
                    await self.task
                except asyncio.CancelledError:
                    logger.info(f"Monitor task for {self.watch_folder_id} was cancelled")
            
            # Update watch folder status to idle
            await update_watch_folder_status(self.graphql_client, self.watch_folder_id, "idle")
            
            # Remove from active monitors
            if self.watch_folder_id in active_monitors:
                del active_monitors[self.watch_folder_id]
            
            logger.info(f"Stopped monitoring watch folder {self.watch_folder_id}")
            return {"status": "success", "message": "Watch folder monitoring stopped"}
        
        except Exception as e:
            logger.exception(f"Error stopping watch folder monitor: {str(e)}")
            await self._set_error_status(f"Error stopping monitoring: {str(e)}")
            raise
    
    async def _monitor_loop(self):
        """Main monitoring loop that periodically checks for new files."""
        try:
            while self.running:
                try:
                    await self._check_for_new_files()
                    
                    # Check for inactivity timeout
                    minutes_since_activity = (time.time() - self.last_activity_time) / 60
                    if minutes_since_activity >= self.inactivity_timeout_minutes:
                        logger.info(f"Stopping monitor for {self.watch_folder_id} due to inactivity timeout: {minutes_since_activity:.1f} minutes")
                        await self.stop()
                        break
                    
                    # Wait a bit before next check (5 seconds)
                    await asyncio.sleep(5)
                
                except asyncio.CancelledError:
                    # This is expected when stopping, so just propagate
                    raise
                except Exception as e:
                    logger.exception(f"Error in monitor loop for {self.watch_folder_id}: {str(e)}")
                    await self._set_error_status(f"Error during monitoring: {str(e)}")
                    # Don't break the loop for non-fatal errors
                    await asyncio.sleep(15)  # Wait longer after error
            
        except asyncio.CancelledError:
            logger.info(f"Monitor loop for {self.watch_folder_id} was cancelled")
            # Let the cancellation propagate
            raise
    
    async def _check_for_new_files(self):
        """Check for new video files in the watch folder."""
        try:
            current_files = self._scan_directory()
            new_files = current_files - self.known_files
            
            if new_files:
                # Update last activity time
                self.last_activity_time = time.time()
                
                # Add new files to the database
                await self._add_new_clips(new_files)
                
                # Update known files
                self.known_files.update(new_files)
                
                logger.info(f"Found {len(new_files)} new video files in {self.folder_path}")
        
        except Exception as e:
            logger.exception(f"Error checking for new files: {str(e)}")
            raise
    
    def _scan_directory(self) -> Set[str]:
        """
        Scan the directory for video files.
        
        Returns:
            A set of absolute paths to video files in the directory
        """
        try:
            folder_path = Path(self.folder_path)
            if not folder_path.exists() or not folder_path.is_dir():
                logger.error(f"Watch folder path does not exist or is not a directory: {self.folder_path}")
                return set()
            
            video_files = set()
            for path in folder_path.glob('**/*'):
                if path.is_file() and path.suffix.lower() in SUPPORTED_VIDEO_EXTENSIONS:
                    video_files.add(str(path.absolute()))
            
            return video_files
        
        except Exception as e:
            logger.exception(f"Error scanning directory {self.folder_path}: {str(e)}")
            return set()
    
    async def _add_new_clips(self, file_paths: Set[str]):
        """
        Add new clips to the database.
        
        Args:
            file_paths: Set of absolute paths to the new video files
        """
        if not self.card_id:
            logger.error(f"Cannot add clips without card_id for watch folder {self.watch_folder_id}")
            return
        
        try:
            clips = []
            for path in file_paths:
                file_path = Path(path)
                clips.append({
                    "card_id": self.card_id,
                    "watch_folder_id": self.watch_folder_id,
                    "filename": file_path.name,
                    "path": str(file_path),
                    "status": "queued"  # Set to queued directly
                })
            
            if clips:
                # Reuse the insert_clips function but create a specific version for monitoring
                await self._insert_clips(clips)
        
        except Exception as e:
            logger.exception(f"Error adding new clips: {str(e)}")
            raise
    
    async def _insert_clips(self, clips: List[dict]):
        """
        Insert new clips into the database.
        
        Args:
            clips: List of clip data dictionaries
        """
        if not clips:
            return
        
        # Prepare the mutation
        mutation = """
        mutation InsertClips($clips: [clips_insert_input!]!) {
            insert_clips(objects: $clips, on_conflict: {constraint: unique_card_filename, update_columns: []}) {
                affected_rows
                returning {
                    clip_id
                    filename
                }
            }
        }
        """
        
        try:
            result = await self.graphql_client.execute_async(mutation, {"clips": clips})
            affected_rows = result.get("data", {}).get("insert_clips", {}).get("affected_rows", 0)
            logger.info(f"Inserted {affected_rows} new clips from monitoring {self.watch_folder_id}")
        
        except Exception as e:
            logger.exception(f"Error inserting clips during monitoring: {str(e)}")
            raise
    
    async def _get_existing_files(self) -> Set[str]:
        """
        Get the set of existing video files in the folder.
        
        Returns:
            A set of absolute paths to existing video files
        """
        return self._scan_directory()
    
    async def _set_error_status(self, error_message: str):
        """
        Set the watch folder status to error.
        
        Args:
            error_message: The error message
        """
        try:
            await update_watch_folder_status(self.graphql_client, self.watch_folder_id, "error")
            logger.error(f"Watch folder {self.watch_folder_id} status set to error: {error_message}")
        except Exception as e:
            logger.exception(f"Error setting watch folder status to error: {str(e)}")

# Helper functions for working with the monitor registry

async def start_watch_folder_monitoring(watch_folder_id: str, folder_path: str, inactivity_timeout_minutes: int = 30):
    """
    Start monitoring a watch folder for new video files.
    
    Args:
        watch_folder_id: The ID of the watch folder to monitor
        folder_path: The path to the folder to monitor
        inactivity_timeout_minutes: Number of minutes of inactivity before stopping monitoring
        
    Returns:
        A dictionary with the status of the operation
    """
    # Check if already monitoring this folder
    if watch_folder_id in active_monitors:
        logger.info(f"Watch folder {watch_folder_id} is already being monitored")
        return {"status": "success", "message": "Watch folder is already being monitored"}
    
    # Create and start a new monitor
    monitor = WatchFolderMonitor(watch_folder_id, folder_path, inactivity_timeout_minutes)
    return await monitor.start()

async def stop_watch_folder_monitoring(watch_folder_id: str):
    """
    Stop monitoring a watch folder.
    
    Args:
        watch_folder_id: The ID of the watch folder to stop monitoring
        
    Returns:
        A dictionary with the status of the operation
    """
    if watch_folder_id not in active_monitors:
        logger.info(f"Watch folder {watch_folder_id} is not being monitored")
        # Still update the status to be safe
        graphql_client = GraphQLClient()
        await update_watch_folder_status(graphql_client, watch_folder_id, "idle")
        return {"status": "success", "message": "Watch folder is not being monitored"}
    
    # Stop the monitor
    monitor = active_monitors[watch_folder_id]
    return await monitor.stop()

# Handle cleanup on application shutdown
async def cleanup_monitors():
    """Stop all active monitors on application shutdown."""
    logger.info(f"Cleaning up {len(active_monitors)} active monitors on shutdown")
    for watch_folder_id, monitor in list(active_monitors.items()):
        try:
            await monitor.stop()
        except Exception as e:
            logger.exception(f"Error stopping monitor {watch_folder_id} during cleanup: {str(e)}") 