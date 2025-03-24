from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from typing import Dict, Any
from pydantic import BaseModel
import logging
import os
import datetime

from src.services.project_import_service import ProjectImportService
from src.utils.env_loader import get_required_env_var

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/consent",
    tags=["consent"],
    responses={404: {"description": "Not found"}},
)

class ImportResponse(BaseModel):
    """Response model for import operations."""
    success: bool
    message: str
    stats: Dict[str, Any] = {}

@router.post("/get-projects", response_model=ImportResponse)
async def get_projects():
    """
    Get projects by scanning the consent filesystem and importing to database.
    
    Returns:
        Import statistics and status
    """
    # Add basic print to ensure the function is called
    print("==== GET PROJECTS ENDPOINT CALLED ====")
    logger.info("GET PROJECTS ENDPOINT CALLED")
    
    try:
        # Explicitly check environment variables before creating service
        try:
            print("Checking environment variables...")
            hasura_url = get_required_env_var("HASURA_GRAPHQL_URL")
            hasura_secret = get_required_env_var("HASURA_ADMIN_SECRET")
            print(f"Environment vars found: URL={hasura_url[:10]}... SECRET={hasura_secret[:5]}...")
            logger.info("Environment variables are available for GraphQL client")
        except ValueError as e:
            print(f"Environment variable error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
            
        print("Creating ProjectImportService...")
        service = ProjectImportService()
        print("Calling import_all_project_data...")
        stats = await service.import_all_project_data()
        
        # Determine success based on if projects were imported
        success = stats["projects_imported"] > 0
        
        # Create appropriate message
        if success:
            message = f"Successfully imported {stats['projects_imported']} projects, {stats['profiles_imported']} profiles, and {stats['faces_imported']} faces"
        else:
            if stats["projects_found"] == 0:
                message = "No projects found in the consent folder"
            else:
                message = f"Failed to import any projects. {len(stats['errors'])} errors occurred."
        
        print(f"Returning response: success={success}")
        return ImportResponse(
            success=success,
            message=message,
            stats=stats
        )
    except Exception as e:
        print(f"ERROR in get_projects: {str(e)}")
        logger.exception(f"Error in get_projects endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error importing project data: {str(e)}"
        )

# Background version that runs asynchronously
@router.post("/get-projects-background", response_model=ImportResponse)
async def get_projects_background(background_tasks: BackgroundTasks):
    """
    Get projects in the background by scanning filesystem and importing to database.
    
    Returns:
        Success message (actual import runs in background)
    """
    async def run_import():
        service = ProjectImportService()
        await service.import_all_project_data()
    
    background_tasks.add_task(run_import)
    
    return ImportResponse(
        success=True,
        message="Project import process started in background",
        stats={"status": "running"}
    )

@router.get("/health", response_model=dict)
async def health_check():
    """Simple health check endpoint to verify API is functioning."""
    print("Health check endpoint called")
    logger.info("Health check endpoint called")
    
    # Check if environment variables are available without using them
    env_vars_available = (
        os.getenv("HASURA_GRAPHQL_URL") is not None and 
        os.getenv("HASURA_ADMIN_SECRET") is not None
    )
    
    return {
        "status": "ok",
        "env_vars_available": env_vars_available,
        "timestamp": datetime.datetime.now().isoformat()
    } 