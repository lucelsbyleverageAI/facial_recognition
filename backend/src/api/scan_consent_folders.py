from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from typing import Dict, Any, Optional
from pydantic import BaseModel
import logging
import os
import datetime

from src.services.project_import.project_import_orchestrator import ProjectImportOrchestrator
from src.utils.env_loader import get_required_env_var

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api",
    tags=["consent"],
    responses={404: {"description": "Not found"}},
)

class ScanConsentFoldersRequest(BaseModel):
    """Request model for the scan-consent-folders endpoint."""
    consent_folder_path: Optional[str] = None

class ScanConsentFoldersResponse(BaseModel):
    """Response model for the scan-consent-folders endpoint."""
    status: str
    projects_found: int = 0
    projects_created: int = 0
    projects_updated: int = 0
    consent_profiles_found: int = 0
    consent_profiles_created: int = 0
    consent_profiles_updated: int = 0
    consent_images_found: int = 0
    consent_images_created: int = 0
    consent_images_updated: int = 0

@router.post("/scan-consent-folders", response_model=ScanConsentFoldersResponse)
async def scan_consent_folders(request: ScanConsentFoldersRequest):
    """
    Scans the pre-defined local consent folder and synchronizes the database with 
    discovered projects, consent profiles, and images.
    
    Request Body:
        consent_folder_path: Optional path to the consent folders
    
    Returns:
        Import statistics and status
    """
    # Log endpoint call
    print("==== SCAN CONSENT FOLDERS ENDPOINT CALLED ====")
    logger.info("SCAN CONSENT FOLDERS ENDPOINT CALLED")
    
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
        
        # Get the consent folder path
        consent_folder_path = request.consent_folder_path
        
        print("Creating ProjectImportOrchestrator...")
        orchestrator = ProjectImportOrchestrator(consent_folder_path)
        print(f"Calling import_all_project_data with folder path: {consent_folder_path}")
        
        # Update the service call to include the consent folder path
        stats = await orchestrator.import_all_project_data(consent_folder_path)
        
        # Convert service stats to response format
        response = ScanConsentFoldersResponse(
            status="success",
            projects_found=stats.get("projects_found", 0),
            projects_created=stats.get("projects_created", 0),
            projects_updated=stats.get("projects_updated", 0),
            consent_profiles_found=stats.get("consent_profiles_found", 0),
            consent_profiles_created=stats.get("consent_profiles_created", 0),
            consent_profiles_updated=stats.get("consent_profiles_updated", 0),
            consent_images_found=stats.get("consent_images_found", 0),
            consent_images_created=stats.get("consent_images_created", 0),
            consent_images_updated=stats.get("consent_images_updated", 0)
        )
        
        print(f"Returning response: status={response.status}")
        return response
        
    except Exception as e:
        print(f"ERROR in scan_consent_folders: {str(e)}")
        logger.exception(f"Error in scan_consent_folders endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error scanning consent folders: {str(e)}"
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