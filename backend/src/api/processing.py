import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any, List, Optional
from uuid import UUID
import uuid
from datetime import datetime

# Import models from the schema file
from src.schemas.processing import (
    StartProcessingRequest,
    StartProcessingResponse,
    StopProcessingRequest,
    StopProcessingResponse,
    ProcessingTaskDB # Import the correct model name
)
from src.services.graphql_client import GraphQLClient
from src.services.processing_service import processing_service, ProcessingService

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api",
    tags=["processing"],
)

@router.post("/start-processing", response_model=StartProcessingResponse)
async def start_processing(
    request: StartProcessingRequest,
    background_tasks: BackgroundTasks # Keep BackgroundTasks for launching the process
):
    """
    Start processing a card (generating embeddings, processing clips, etc.)
    Uses the database for task management.

    Args:
        request: The request containing the card ID and optional config overrides
        background_tasks: FastAPI background tasks dependency

    Returns:
        Response with the task ID and initial status
    """
    graphql_client = GraphQLClient() # Get singleton instance
    card_id = str(request.card_id)
    logger.info(f"Received request to start processing for card: {card_id}")

    try:
        # 1. Check for existing *active* task in the DB for this card
        active_task = await graphql_client.get_active_db_task_for_card(card_id)
        if active_task:
            task_id = active_task['task_id']
            status = active_task['status']
            logger.info(f"Active processing task {task_id} (status: {status}) already exists for card {card_id}. Returning existing task.")
            # Get clip count for response consistency
            clips_count = await processing_service.get_queued_clips_count(card_id)
            return StartProcessingResponse(
                task_id=task_id,
                status=status,
                message=f"Active processing task {task_id} already exists for card {card_id}",
                clips_count=clips_count
            )

        # 2. Get card configuration
        # Note: ProcessingService also has get_card_config, could reuse or keep here
        db_config = await processing_service.get_card_config(card_id)
        if not db_config:
            logger.error(f"Failed to retrieve configuration for card {card_id}")
            raise HTTPException(status_code=404, detail=f"Configuration not found for card {card_id}")

        logger.debug(f"Retrieved configuration from database for card {card_id}")

        # Merge request config (overrides) with database config
        config = db_config.copy()
        if request.config:
            config.update(request.config)
            logger.info(f"Applied config overrides for card {card_id}")

        # Ensure default values if somehow missing (should be set by DB trigger)
        config.setdefault("scene_sensitivity", 0.2)
        config.setdefault("fallback_frame_rate", 6)
        config.setdefault("use_eq", True)

        # 3. Get count of clips to process
        clips_count = await processing_service.get_queued_clips_count(card_id)
        if clips_count == 0:
            logger.warning(f"No queued clips found for card {card_id}. Cannot start processing.")
            return StartProcessingResponse(
                task_id="none", # Or perhaps null/empty UUID?
                status="no_clips",
                message=f"No queued clips to process for card {card_id}",
                clips_count=0
            )

        # 4. Create task record in the database
        task_id = await graphql_client.create_db_task(card_id)
        if not task_id:
            logger.error(f"Failed to create task record in database for card {card_id}")
            raise HTTPException(status_code=500, detail="Failed to create processing task record")

        logger.info(f"Created database task record {task_id} for card {card_id}")

        # 5. Update card status to 'processing'
        await processing_service.update_card_status(card_id, "processing")

        # 6. Add the actual processing function to run in the background
        # Pass the NEWLY created DB task_id
        background_tasks.add_task(
            processing_service.process_card,
            task_id=task_id,
            card_id=card_id,
            config=config
        )

        logger.info(f"Scheduled background task {task_id} for card {card_id} using process_card")

        # 7. Return the new task ID
        return StartProcessingResponse(
            task_id=task_id,
            status="pending", # Initial status in DB is 'pending'
            message=f"Started processing for card {card_id}",
            clips_count=clips_count
        )

    except HTTPException as http_exc:
        # Re-raise HTTPExceptions directly
        raise http_exc
    except Exception as e:
        logger.exception(f"Error starting processing for card {card_id}: {e}")
        # Attempt to set the task to error if it was created
        if 'task_id' in locals() and task_id != "none":
            try:
                await graphql_client.update_db_task(task_id, status="error", message=f"Failed to start: {e}")
            except Exception as update_err:
                logger.error(f"Failed to update task {task_id} to error status: {update_err}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

@router.post("/stop-processing", response_model=StopProcessingResponse)
async def stop_processing(request: StopProcessingRequest):
    """
    Request cancellation of an active processing task by updating its status in the DB.

    Args:
        request: The request containing the task ID to stop

    Returns:
        Response indicating success or failure
    """
    graphql_client = GraphQLClient()
    # Task ID from request is UUID, convert to string if needed by downstream funcs
    task_id_str = str(request.task_id)
    logger.info(f"Received request to stop processing task: {task_id_str}")

    try:
        # Check current status (optional but good practice)
        current_status = await graphql_client.get_db_task_status(task_id_str)
        if not current_status:
            raise HTTPException(status_code=404, detail=f"Task not found: {task_id_str}")

        if current_status in ['complete', 'error', 'cancelled', 'cancelling']:
            logger.warning(f"Task {task_id_str} is already in status '{current_status}'. Cannot stop.")
            return StopProcessingResponse(
                status=current_status,
                message=f"Task {task_id_str} is already {current_status}."
            )

        # Update task status to 'cancelling'
        success = await graphql_client.update_db_task(task_id_str, status="cancelling", message="Cancellation requested by user.")

        if not success:
            logger.error(f"Failed to update task {task_id_str} status to 'cancelling' in database.")
            raise HTTPException(status_code=500, detail="Failed to request task cancellation in database.")

        logger.info(f"Successfully requested cancellation for task {task_id_str} by setting status to 'cancelling'.")
        # The background task will check this status and stop itself.
        return StopProcessingResponse(
            status="cancelling",
            message=f"Cancellation requested for task {task_id_str}. It will stop shortly."
        )

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.exception(f"Error stopping processing task {task_id_str}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

@router.get("/processing-tasks", response_model=List[ProcessingTaskDB])
async def get_processing_tasks():
    """
    Get a list of all processing tasks from the database.

    Returns:
        List of tasks with their status.
    """
    graphql_client = GraphQLClient()
    try:
        tasks = await graphql_client.get_all_db_tasks()
        # Convert timestamps from strings (if needed) to datetime objects for Pydantic
        # Assuming get_all_db_tasks returns ISO format strings
        result = []
        for task_data in tasks:
             # Ensure created_at and updated_at are datetime objects
             if isinstance(task_data.get('created_at'), str):
                 task_data['created_at'] = datetime.fromisoformat(task_data['created_at'].replace('Z', '+00:00'))
             if isinstance(task_data.get('updated_at'), str):
                 task_data['updated_at'] = datetime.fromisoformat(task_data['updated_at'].replace('Z', '+00:00'))
             # Convert task_id and card_id to UUID if they are strings
             if isinstance(task_data.get('task_id'), str):
                 task_data['task_id'] = UUID(task_data['task_id'])
             if isinstance(task_data.get('card_id'), str):
                 task_data['card_id'] = UUID(task_data['card_id'])
             result.append(ProcessingTaskDB(**task_data))
        return result
    except Exception as e:
        logger.exception(f"Error retrieving processing tasks: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve processing tasks")

@router.get("/processing-tasks/{task_id}", response_model=ProcessingTaskDB)
async def get_processing_task(task_id: UUID):
    """
    Get a specific processing task from the database.

    Args:
        task_id: The ID of the task to retrieve.

    Returns:
        The details of the specified task.
    """
    graphql_client = GraphQLClient()
    try:
        # We might need a specific get_db_task_by_id method in GraphQLClient
        # For now, let's filter the result of get_all_db_tasks (less efficient)
        # TODO: Implement get_db_task_by_id in GraphQLClient for efficiency
        tasks = await graphql_client.get_all_db_tasks() # Inefficient for single task
        task_id_str = str(task_id)
        task_data = next((task for task in tasks if task['task_id'] == task_id_str), None)

        if not task_data:
            raise HTTPException(status_code=404, detail=f"Task not found: {task_id_str}")

        # Convert timestamps and UUIDs
        if isinstance(task_data.get('created_at'), str):
             task_data['created_at'] = datetime.fromisoformat(task_data['created_at'].replace('Z', '+00:00'))
        if isinstance(task_data.get('updated_at'), str):
             task_data['updated_at'] = datetime.fromisoformat(task_data['updated_at'].replace('Z', '+00:00'))
        if isinstance(task_data.get('task_id'), str):
            task_data['task_id'] = UUID(task_data['task_id'])
        if isinstance(task_data.get('card_id'), str):
            task_data['card_id'] = UUID(task_data['card_id'])

        return ProcessingTaskDB(**task_data)
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.exception(f"Error retrieving task {task_id_str}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve task details") 