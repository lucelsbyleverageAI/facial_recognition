import os
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api",
    tags=["images"],
)

@router.get("/images")
async def get_image(path: str = Query(..., description="Local file path to the image")):
    """
    Serve an image file from the local filesystem.
    
    Args:
        path: The full local path to the image file.
    
    Returns:
        The image file.
    
    Raises:
        HTTPException: If the file doesn't exist or can't be accessed.
    """
    try:
        # Security check: ensure path exists and is a file
        image_path = Path(path)
        if not image_path.exists() or not image_path.is_file():
            logger.error(f"Image not found: {path}")
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Check if it's an image file by extension
        valid_extensions = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"]
        if image_path.suffix.lower() not in valid_extensions:
            logger.error(f"Not an image file: {path}")
            raise HTTPException(status_code=400, detail="Not an image file")
        
        logger.info(f"Serving image: {path}")
        return FileResponse(
            path=str(image_path),
            media_type=f"image/{image_path.suffix[1:].lower()}", 
            filename=image_path.name
        )
        
    except Exception as e:
        logger.exception(f"Error serving image: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error serving image: {str(e)}") 