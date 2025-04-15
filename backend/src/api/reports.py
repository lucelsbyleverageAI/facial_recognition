import os
import httpx
import base64
import logging
from io import BytesIO
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, Depends, Path as FastApiPath, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from PIL import Image, UnidentifiedImageError

# Assuming environment variables are loaded by server.py using dotenv
# If not, you might need load_dotenv() here too.

# Setup logger
logger = logging.getLogger(__name__)

# --- Configuration ---
# Get config from environment variables (set defaults if necessary)
HASURA_URL = os.getenv("HASURA_GRAPHQL_URL", "http://localhost:8080/v1/graphql")
HASURA_ADMIN_SECRET = os.getenv("HASURA_ADMIN_SECRET")

# --- FastAPI Router Setup ---
router = APIRouter(prefix="/api", tags=["reports"])

# Adjust template path relative to this file's location (src/api/reports.py)
# Goes up three levels (api -> src -> backend) then into templates
templates_path = Path(__file__).parent.parent.parent / "templates"
if not templates_path.is_dir():
    logger.warning(f"Templates directory not found at: {templates_path}")
    # Handle error appropriately - maybe raise an exception or provide a default path
    # For now, we'll let Jinja2 potentially fail later if the path is wrong.
templates = Jinja2Templates(directory=str(templates_path))

# --- GraphQL Query --- 
GET_REPORT_DATA_QUERY = """
query GetReportData($cardId: uuid!) {
  cards_by_pk(card_id: $cardId) {
    card_id
    card_name
    project {
      project_name
    }
    clips(order_by: {filename: asc}) {
      clip_id
      filename
      frames(order_by: {timestamp: asc}) {
        frame_id
        timestamp
        raw_frame_image_path
        processed_frame_image_path
        detected_faces {
          detection_id
          facial_area # {x, y, w, h}
          face_matches {
            match_id # Presence indicates a match
          }
        }
      }
    }
  }
}
"""

# --- Helper Functions ---

async def execute_graphql(query: str, variables: dict) -> dict:
    """Executes a GraphQL query against the Hasura endpoint."""
    headers = {"Content-Type": "application/json"}
    if HASURA_ADMIN_SECRET:
        headers["x-hasura-admin-secret"] = HASURA_ADMIN_SECRET
    else:
        logger.warning("Executing GraphQL query without HASURA_ADMIN_SECRET.")

    logger.debug(f"Executing GraphQL query to {HASURA_URL}")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                HASURA_URL,
                json={"query": query, "variables": variables},
                headers=headers,
                timeout=60.0, # Increase timeout for potentially large queries
            )
            response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
            result = response.json()
            if "errors" in result:
                logger.error(f"GraphQL Errors: {result['errors']}")
                raise HTTPException(
                    status_code=400,
                    detail=f"GraphQL Errors: {result['errors']}"
                )
            logger.debug("GraphQL query executed successfully.")
            return result["data"]
        except httpx.RequestError as exc:
            logger.error(f"HTTPX Request Error connecting to Hasura: {exc}")
            raise HTTPException(
                status_code=503, # Service Unavailable
                detail=f"Error connecting to GraphQL endpoint: {exc}"
            )
        except httpx.HTTPStatusError as exc:
            logger.error(f"Hasura returned error status: {exc.response.status_code} - {exc.response.text}")
            raise HTTPException(
                status_code=exc.response.status_code,
                detail=f"Error from GraphQL endpoint: {exc.response.text}"
            )
        except Exception as exc:
            logger.exception(f"Unexpected error during GraphQL execution: {exc}") # Log full traceback
            raise HTTPException(
                status_code=500,
                detail=f"An unexpected error occurred during GraphQL execution."
            )

def crop_face(image_path: str, facial_area: dict) -> str | None:
    """Loads an image, crops the face based on facial_area, returns base64 encoded JPEG."""
    # Base path assumption - adjust if your image paths from Hasura are relative
    # or need prefixing based on where the backend runs / volume mounts.
    # Example: BASE_IMAGE_PATH = Path("/path/to/shared/images")
    # full_image_path = BASE_IMAGE_PATH / image_path
    full_image_path = Path(image_path)
    logger.debug(f"Attempting to crop face from image: {full_image_path}")

    if not facial_area or not all(k in facial_area for k in ('x', 'y', 'w', 'h')):
        logger.warning(f"Invalid or missing facial_area data for cropping: {facial_area} in path {image_path}")
        return None

    try:
        if not full_image_path.is_file():
            logger.error(f"Image file not found at {full_image_path}")
            return None

        img = Image.open(full_image_path)

        x = int(facial_area['x'])
        y = int(facial_area['y'])
        w = int(facial_area['w'])
        h = int(facial_area['h'])

        box = (x, y, x + w, y + h)

        # Ensure crop box is within image bounds
        img_w, img_h = img.size
        clamped_box = (
            max(0, box[0]),
            max(0, box[1]),
            min(img_w, box[2]),
            min(img_h, box[3])
        )

        if box != clamped_box:
             logger.warning(f"Crop box {box} was clamped to {clamped_box} for image {full_image_path}")

        # Check if the box is valid after clamping
        if clamped_box[0] >= clamped_box[2] or clamped_box[1] >= clamped_box[3]:
             logger.error(f"Invalid crop dimensions after clamping for {full_image_path}: {clamped_box}")
             return None

        cropped_img = img.crop(clamped_box)

        # Convert to base64
        buffered = BytesIO()
        cropped_img.save(buffered, format="JPEG") # Save as JPEG for web compatibility
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        logger.debug(f"Successfully cropped face from {full_image_path}")
        return img_str

    except FileNotFoundError:
        logger.error(f"Image file not found at {full_image_path} during PIL open")
        return None
    except UnidentifiedImageError:
        logger.error(f"Cannot identify image file (corrupted/wrong format?) at {full_image_path}")
        return None
    except ValueError as e:
         logger.error(f"Invalid coordinate data for cropping {full_image_path}: {facial_area} - Error: {e}")
         return None
    except Exception as e:
        logger.exception(f"Error cropping image {full_image_path}: {e}")
        return None

def process_report_data(data: dict) -> tuple:
    """Processes the raw GraphQL data to structure it for the report template."""
    card_data = data.get("cards_by_pk")
    if not card_data:
        logger.error("Card data not found in GraphQL response.")
        raise HTTPException(status_code=404, detail="Card data not found.")

    logger.info(f"Processing report data for card: {card_data.get('card_name')}")
    clip_summaries = []
    unmatched_details = []
    any_unmatched_found = False

    for clip in card_data.get("clips", []):
        total_frames_in_clip = len(clip.get("frames", []))
        unmatched_frames_count = 0
        clip_unmatched_faces = []
        logger.debug(f"Processing clip: {clip.get('filename')}, Frames: {total_frames_in_clip}")

        for frame in clip.get("frames", []):
            frame_has_unmatched = False
            detected_faces = frame.get("detected_faces", [])
            if not detected_faces:
                continue # Skip frames with no detected faces

            for face in detected_faces:
                # Check if face_matches array exists and has length > 0
                is_matched = isinstance(face.get("face_matches"), list) and len(face["face_matches"]) > 0
                if not is_matched:
                    frame_has_unmatched = True
                    any_unmatched_found = True
                    # Prioritize processed path if available
                    image_path = frame.get("processed_frame_image_path") or frame.get("raw_frame_image_path")
                    facial_area = face.get("facial_area")

                    if image_path and facial_area:
                        cropped_base64 = crop_face(image_path, facial_area)
                        if cropped_base64:
                            clip_unmatched_faces.append({
                                "frame_id": frame.get("frame_id"),
                                "frame_id_short": str(frame.get("frame_id"))[:8],
                                "timestamp": frame.get("timestamp"),
                                "cropped_image_base64": cropped_base64
                            })
                        else:
                             logger.warning(f"Failed to crop face for detection {face.get('detection_id')} in frame {frame.get('frame_id')}")
                    elif not image_path:
                        logger.warning(f"No image path found for frame {frame.get('frame_id')}")
                    elif not facial_area:
                        logger.warning(f"No facial_area found for detection {face.get('detection_id')} in frame {frame.get('frame_id')}")

            if frame_has_unmatched:
                unmatched_frames_count += 1

        safe_frames_count = total_frames_in_clip - unmatched_frames_count
        clip_summaries.append({
            "filename": clip.get("filename", "N/A"),
            "total_frames": total_frames_in_clip,
            "unmatched_frames_count": unmatched_frames_count,
            "safe_frames_count": safe_frames_count,
        })

        if clip_unmatched_faces:
            unmatched_details.append({
                "filename": clip.get("filename", "N/A"),
                "unmatched_faces": clip_unmatched_faces
            })
            logger.debug(f"Added {len(clip_unmatched_faces)} unmatched faces for clip {clip.get('filename')}")

    overall_status = "Review Required" if any_unmatched_found else "Complete"
    logger.info(f"Report processing complete. Overall Status: {overall_status}")

    template_context = {
        # request is automatically added by FastAPI when using Jinja2Templates dependency
        # "request": None,
        "project_name": card_data.get("project", {}).get("project_name", "N/A"),
        "card_name": card_data.get("card_name", "N/A"),
        "card_id": card_data.get("card_id"),
        "generation_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "overall_status": overall_status,
        "clip_summaries": clip_summaries,
        "unmatched_details": unmatched_details,
    }

    return template_context, overall_status

# --- API Endpoint ---

@router.get("/cards/{card_id}/report", response_class=HTMLResponse)
async def generate_card_report(
    request: Request, # Inject request for Jinja2Templates
    card_id: str = FastApiPath(..., title="Card ID", description="The UUID of the card for the report")
):
    """Generates an HTML report for the specified card."""
    logger.info(f"Received request to generate report for card_id: {card_id}")

    # 1. Fetch data from Hasura
    try:
        report_data = await execute_graphql(GET_REPORT_DATA_QUERY, {"cardId": card_id})
    except HTTPException as e:
         logger.error(f"HTTPException while fetching report data: {e.detail}")
         raise e
    except Exception as e:
        logger.exception(f"Unexpected Error fetching report data for card {card_id}")
        raise HTTPException(status_code=500, detail="Failed to fetch report data.")

    if not report_data or not report_data.get("cards_by_pk"):
        logger.warning(f"Card not found in Hasura for ID: {card_id}")
        raise HTTPException(status_code=404, detail=f"Card with ID {card_id} not found.")

    # 2. Process data and crop images
    try:
        template_context, status = process_report_data(report_data)
    except HTTPException as e: # Catch potential exceptions from process_report_data
        logger.error(f"HTTPException while processing report data: {e.detail}")
        raise e
    except Exception as e:
        logger.exception(f"Error processing report data for card {card_id}")
        raise HTTPException(status_code=500, detail="Failed to process report data.")

    # 3. Render HTML template
    try:
        # Add request to context for Jinja2
        template_context["request"] = request
        html_content = templates.get_template("report_template.html").render(template_context)
        logger.info(f"Successfully rendered report template for card {card_id}")
    except Exception as e:
        logger.exception(f"Error rendering report template for card {card_id}")
        raise HTTPException(status_code=500, detail="Failed to render report template.")

    # 4. Return HTML as a downloadable file
    safe_card_name = template_context.get('card_name', 'UnknownCard').replace(" ", "_").replace("/", "_")
    filename = f"{safe_card_name}_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    headers = {
        "Content-Disposition": f"attachment; filename=\"{filename}\""
    }

    return HTMLResponse(content=html_content, status_code=200, headers=headers) 