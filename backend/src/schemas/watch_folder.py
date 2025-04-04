from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional, List

class ScanWatchFolderResponse(BaseModel):
    """Response model for the scan watch folder operation"""
    task_id: UUID = Field(..., description="Unique identifier for the task")
    status: str = Field(..., description="Status of the operation")
    clips_found: int = Field(..., description="Number of clips found in the folder")
    clips_created: int = Field(..., description="Number of new clips created in the database")
    clips_updated: int = Field(..., description="Number of existing clips updated in the database")
    watch_folder_path: str = Field(..., description="Path of the watched folder")
    duplicate_filenames: List[str] = Field(default_factory=list, description="List of filenames that were skipped because they already exist for this card")

class ClipModel(BaseModel):
    """Model representing a video clip"""
    clip_id: Optional[UUID] = Field(None, description="Unique identifier for the clip")
    card_id: UUID = Field(..., description="ID of the card this clip belongs to")
    watch_folder_id: UUID = Field(..., description="ID of the watch folder this clip was found in")
    filename: str = Field(..., description="Name of the video file")
    path: str = Field(..., description="Full path to the video file")
    status: str = Field("pending", description="Current status of the clip")
    error_message: Optional[str] = Field(None, description="Error message if processing failed") 