from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional, Dict, Any, List
from datetime import datetime

class StartProcessingRequest(BaseModel):
    """Request model for starting processing"""
    card_id: UUID = Field(..., description="ID of the card to process")
    config: Optional[Dict[str, Any]] = Field(None, description="Optional configuration overrides")

class StartProcessingResponse(BaseModel):
    """Response model for the start processing operation"""
    task_id: str = Field(..., description="Unique identifier for the task")
    status: str = Field(..., description="Status of the operation")
    message: str = Field(..., description="Description of the result")
    total_items_count: int = Field(0, description="Total number of items to process (clips, frames, faces)", alias="clips_count")

class StopProcessingRequest(BaseModel):
    """Request model for stopping processing"""
    task_id: UUID = Field(..., description="ID of the task to stop")

class StopProcessingResponse(BaseModel):
    """Response model for the stop processing operation"""
    status: str = Field(..., description="Status of the operation")
    message: str = Field(..., description="Description of the result")

class ProcessingTaskDB(BaseModel):
    """Model for representing the status of a processing task from the DB"""
    task_id: UUID = Field(..., description="ID of the task")
    card_id: UUID = Field(..., description="ID of the card being processed")
    status: str = Field(..., description="Current status of the task")
    stage: Optional[str] = Field(None, description="Current processing stage")
    progress: float = Field(0.0, description="Progress percentage (0.0 to 1.0)")
    message: Optional[str] = Field(None, description="Current status message or error")
    created_at: datetime = Field(..., description="Timestamp when the task was created")
    updated_at: datetime = Field(..., description="Timestamp when the task was last updated") 