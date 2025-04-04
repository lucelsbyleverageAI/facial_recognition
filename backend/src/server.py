from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import logging
import time
from fastapi import Request
import asyncio

from src.api import scan_consent_folders  # Changed from get_projects to scan_consent_folders
from src.api import images  # Add the new images router
from src.api import scan_watch_folder  # Import the new scan_watch_folder router
from src.api import watch_folder_monitor  # Import the new watch folder monitoring API
from src.services.watch_folder_monitor import cleanup_monitors  # Import the cleanup function
from src.utils.env_loader import load_environment_variables

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Increase logging level to DEBUG
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # Ensure logs go to stdout
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
environment_loaded = load_environment_variables()
if not environment_loaded:
    logger.warning("Application starting with missing environment variables")

app = FastAPI(
    title="Facial Recognition API",
    description="API for facial recognition services",
    version="1.0.0"
)

# Register a startup event to initialize the background tasks system
@app.on_event("startup")
async def startup_event():
    logger.info("Application starting up")

# Register a shutdown event to cleanup resources, especially active monitors
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutting down, cleaning up resources")
    try:
        await cleanup_monitors()
    except Exception as e:
        logger.exception(f"Error during cleanup: {str(e)}")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development only, restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(scan_consent_folders.router)
app.include_router(images.router)  # Include the images router
app.include_router(scan_watch_folder.router)  # Include the new scan_watch_folder router
app.include_router(watch_folder_monitor.router)  # Include the new watch folder monitoring router

@app.get("/")
async def root():
    return {"message": "Welcome to Facial Recognition API"}

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware to log all requests."""
    start_time = time.time()
    path = request.url.path
    method = request.method
    
    print(f"=== Request: {method} {path} ===")
    logger.debug(f"Received request: {method} {path}")
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.debug(f"Request completed: {method} {path} - Status: {response.status_code} - Time: {process_time:.4f}s")
        return response
    except Exception as e:
        logger.exception(f"Error processing request: {method} {path} - {str(e)}")
        raise

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # Enable auto-reload during development
    ) 