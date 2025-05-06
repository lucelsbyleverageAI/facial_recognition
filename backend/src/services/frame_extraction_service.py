import os
import re
import uuid
import logging
import asyncio
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timedelta

from src.services.graphql_client import GraphQLClient
from src.utils.datetime_utils import format_for_database

# Configure logging
logger = logging.getLogger(__name__)

class FrameExtractionService:
    """Service for extracting frames from video clips."""
    
    def __init__(self, graphql_client: GraphQLClient):
        """
        Initialize the frame extraction service.
        
        Args:
            graphql_client: The GraphQL client for database operations
        """
        self.graphql_client = graphql_client
        
    async def process_clip(self, clip_id: str, config: Dict[str, Any]) -> bool:
        """
        Process a clip by extracting frames and updating database.
        
        Args:
            clip_id: The ID of the clip to process
            config: The card configuration for processing
            
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info(f"Starting frame extraction for clip {clip_id}")
        
        # 1. Update clip status to extracting_frames
        await self.update_clip_status(clip_id, "extracting_frames")
        
        try:
            # 2. Get clip details from database
            clip_data = await self._get_clip_data(clip_id)
            
            if not clip_data:
                logger.error(f"Clip {clip_id} not found in database")
                await self.update_clip_status(clip_id, "error", error_message="Clip not found in database")
                return False
                
            # 3. Extract frames
            extractor = FrameExtractor(
                clip_path=clip_data["path"],
                clip_id=clip_id,
                config=config
            )
            
            # Check if FFmpeg is installed
            if not extractor.check_ffmpeg():
                logger.error("FFmpeg not found. Please install FFmpeg to extract frames.")
                await self.update_clip_status(clip_id, "error", error_message="FFmpeg not installed")
                return False
            
            frames = await extractor.extract_frames()
            
            # 4. Create frame records in database
            logger.info(f"Extracted {len(frames)} frames from clip {clip_id}")
            for frame in frames:
                await self._create_frame_record(frame)
            
            # 5. Update clip status to extraction_complete
            await self.update_clip_status(clip_id, "extraction_complete")
            logger.info(f"Successfully completed frame extraction for clip {clip_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing clip {clip_id}: {str(e)}", exc_info=True)
            # Set clip status to error
            await self.update_clip_status(clip_id, "error", error_message=str(e))
            return False
    
    async def update_clip_status(self, clip_id: str, status: str, error_message: Optional[str] = None) -> bool:
        """
        Update clip status in database.
        
        Args:
            clip_id: The ID of the clip
            status: New status
            error_message: Optional error message
            
        Returns:
            bool: True if successful, False otherwise
        """
        mutation = """
        mutation UpdateClipStatus($clip_id: uuid!, $status: String!, $error_message: String) {
            update_clips_by_pk(
                pk_columns: {clip_id: $clip_id}, 
                _set: {status: $status, error_message: $error_message}
            ) {
                clip_id
            }
        }
        """
        
        variables = {
            "clip_id": clip_id,
            "status": status,
            "error_message": error_message
        }
        
        try:
            result = await self.graphql_client.execute_async(mutation, variables)
            return result.get("update_clips_by_pk") is not None
        except Exception as e:
            logger.error(f"Failed to update clip status: {str(e)}")
            return False
    
    async def _get_clip_data(self, clip_id: str) -> Optional[Dict[str, Any]]:
        """
        Get clip data from database.
        
        Args:
            clip_id: The ID of the clip
            
        Returns:
            Dict with clip data if found, None otherwise
        """
        query = """
        query GetClipData($clip_id: uuid!) {
            clips_by_pk(clip_id: $clip_id) {
                clip_id
                card_id
                path
                filename
                watch_folder {
                    watch_folder_id
                    folder_path
                }
            }
        }
        """
        
        try:
            result = await self.graphql_client.execute_async(query, {"clip_id": clip_id})
            return result.get("clips_by_pk")
        except Exception as e:
            logger.error(f"Failed to get clip data: {str(e)}")
            return None
    
    async def _create_frame_record(self, frame: Dict[str, Any]) -> Optional[str]:
        """
        Create a frame record in the database.
        
        Args:
            frame: Frame data dictionary
            
        Returns:
            frame_id if successful, None otherwise
        """
        mutation = """
        mutation CreateFrame($frame_id: uuid!, $clip_id: uuid!, $timestamp: String!, $raw_frame_image_path: String!, $status: String!) {
            insert_frames_one(object: {
                frame_id: $frame_id,
                clip_id: $clip_id,
                timestamp: $timestamp,
                raw_frame_image_path: $raw_frame_image_path,
                status: $status
            }) {
                frame_id
            }
        }
        """
        
        variables = {
            "frame_id": frame["frame_id"],
            "clip_id": frame["clip_id"],
            "timestamp": frame["timestamp"],
            "raw_frame_image_path": frame["raw_frame_image_path"],
            "status": "queued"  # Initial status for new frames
        }
        
        try:
            result = await self.graphql_client.execute_async(mutation, variables)
            if result.get("insert_frames_one"):
                return result["insert_frames_one"]["frame_id"]
            return None
        except Exception as e:
            logger.error(f"Failed to create frame record: {str(e)}")
            return None


class FrameExtractor:
    """
    Extracts frames from a video file using FFmpeg.
    """
    
    def __init__(self, clip_path: str, clip_id: str, config: Dict[str, Any]):
        """
        Initialize the frame extractor.
        
        Args:
            clip_path: Path to the video clip
            clip_id: The ID of the clip
            config: Configuration for frame extraction
        """
        self.clip_path = clip_path
        self.clip_id = clip_id
        self.config = config
        
        # Set defaults if not specified in config
        self.scene_sensitivity = config.get("scene_sensitivity", 0.3)
        self.fallback_frame_rate = config.get("fallback_frame_rate", 5)
        self.use_eq = config.get("use_eq", True)
        
        # Setup output directory with clip_id for uniqueness
        self.output_dir = Path("outputs/extracted_frames") / self.clip_id
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize LUT file path
        self.lut_file = None
        if not self.use_eq and config.get("lut_file"):
            self._initialize_lut(config.get("lut_file"))

    def check_ffmpeg(self) -> bool:
        """
        Check if FFmpeg is installed.
        
        Returns:
            bool: True if FFmpeg is installed, False otherwise
        """
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                text=True,
                check=False
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def _initialize_lut(self, lut_filename: str) -> None:
        """
        Initialize LUT file path.
        
        Args:
            lut_filename: Name of the LUT file
        """
        # Check if LUT file exists in the backend/luts folder
        lut_dir = Path("backend/luts")
        lut_path = lut_dir / lut_filename
        
        if not lut_path.exists():
            logger.warning(f"LUT file not found: {lut_path}. Falling back to equalization.")
            self.use_eq = True
            return
            
        self.lut_file = str(lut_path.absolute())
        logger.info(f"Using LUT file: {self.lut_file}")
    
    async def extract_frames(self) -> List[Dict[str, Any]]:
        """
        Extract frames from the video using ffmpeg.
        
        Returns:
            List of dictionaries containing frame data
        """
        logger.info(f"=== Starting frame extraction for clip: {self.clip_id} ===")
        logger.info(f"Clip path: {self.clip_path}")
        logger.info(f"Output directory: {self.output_dir}")
        logger.info(f"Configuration: scene_sensitivity={self.scene_sensitivity}, "
                    f"fallback_frame_rate={self.fallback_frame_rate}, "
                    f"use_eq={self.use_eq}")
        
        try:
            # Build ffmpeg command
            ffmpeg_cmd = self._build_ffmpeg_command()
            logger.info(f"FFmpeg command: {' '.join(ffmpeg_cmd)}")
            log_file = self.output_dir / "ffmpeg_output.log"
            
            # Run ffmpeg process
            try:
                process = subprocess.run(
                    ffmpeg_cmd,
                    capture_output=True,
                    text=True,
                    check=True
                )
                self.ffmpeg_output = process.stderr
                logger.info("FFmpeg process completed successfully")
            except subprocess.CalledProcessError as e:
                logger.error("FFmpeg process failed!")
                logger.error("FFmpeg stderr output:")
                for line in e.stderr.splitlines():
                    logger.error(f"FFmpeg: {line}")
                raise RuntimeError(f"FFmpeg failed with error: {e.stderr}")
            
            # Log ffmpeg output
            with open(log_file, 'w') as f:
                f.write(self.ffmpeg_output)
            
            # Get all output files
            logger.info("Checking for extracted frames...")
            frame_files = sorted(self.output_dir.glob('*.png'))
            logger.info(f"Found {len(frame_files)} extracted frames")
            
            if not frame_files:
                logger.error("No frames were extracted!")
                logger.error("FFmpeg output directory contents:")
                for item in self.output_dir.iterdir():
                    logger.error(f"  {item.name} ({item.stat().st_size} bytes)")
                raise RuntimeError("No frames were extracted from the video")
            
            # Create Frame objects from the files
            frames = []
            for frame_file in frame_files:
                frame_id = str(uuid.uuid4())
                
                frame = {
                    "frame_id": frame_id,
                    "clip_id": self.clip_id,
                    "timestamp": "00:00:00:00",  # Default timestamp
                    "raw_frame_image_path": str(frame_file.absolute()),
                }
                frames.append(frame)
            
            # Try to parse timestamps if possible
            try:
                frame_data = self._parse_ffmpeg_output(self.ffmpeg_output)
                if frame_data and len(frame_data) == len(frames):
                    for i, data in enumerate(frame_data):
                        frames[i]["timestamp"] = self._format_timecode(data['timestamp'])
                else:
                    logger.warning(f"Timestamp count mismatch: {len(frame_data)} timestamps for {len(frames)} frames")
            except Exception as e:
                logger.warning(f"Failed to parse frame timestamps: {str(e)}")
                logger.warning("Using default timestamps for frames")
            
            logger.info(f"Successfully processed {len(frames)} frames")
            logger.info("=== Frame extraction completed successfully ===")
            return frames
            
        except Exception as e:
            logger.error(f"Frame extraction failed: {str(e)}")
            raise

    def _build_ffmpeg_command(self) -> List[str]:
        """
        Build ffmpeg command with appropriate filters.
        
        Returns:
            List of command components
        """
        # Base command with input
        cmd = ["ffmpeg", "-i", str(self.clip_path)]
        
        # Build filter complex based on settings
        filter_complex = self._build_filter_complex()
        
        # Add filter and output options
        scene_pattern = str(self.output_dir / f"scene_%04d.png")
        fallback_pattern = str(self.output_dir / f"fallback_%04d.png")

        command = cmd + [
            "-filter_complex", filter_complex,
            "-map", "[vout1]", "-vsync", "vfr", "-q:v", "2", scene_pattern,
            "-map", "[vout2]", "-vsync", "vfr", "-q:v", "2", fallback_pattern
        ]

        return command

    def _build_filter_complex(self) -> str:
        """
        Build filter complex string based on the video config.
        
        Returns:
            Filter complex string for FFmpeg
        """
        if self.lut_file:
            return self._build_lut_filter()
        elif self.use_eq:
            return self._build_eq_filter()
        else:
            return self._build_basic_filter()

    def _build_basic_filter(self) -> str:
        """
        Build basic filter string without color correction.
        
        Returns:
            Filter string
        """
        return (
            f"[0:v]split[v1][v2];"
            f"[v1]select='gt(scene,{self.scene_sensitivity})',showinfo[vout1];"
            f"[v2]fps=1/{self.fallback_frame_rate},showinfo[vout2]"
        )
        
    def _build_eq_filter(self) -> str:
        """
        Build filter string for histogram equalization.
        
        Returns:
            Filter string
        """
        return (
            f"[0:v]split[v1][v2];"
            f"[v1]eq=contrast=1.5:saturation=1.5,select='gt(scene,{self.scene_sensitivity})',showinfo[vout1];"
            f"[v2]eq=contrast=1.5:saturation=1.5,fps=1/{self.fallback_frame_rate},showinfo[vout2]"
        )
        
    def _build_lut_filter(self) -> str:
        """
        Build filter string for LUT application.
        
        Returns:
            Filter string
        """
        return (
            f"[0:v]split[v1][v2];"
            f"[v1]lut3d='{self.lut_file}',select='gt(scene,{self.scene_sensitivity})',showinfo[vout1];"
            f"[v2]lut3d='{self.lut_file}',fps=1/{self.fallback_frame_rate},showinfo[vout2]"
        )

    def _parse_ffmpeg_output(self, ffmpeg_output: str) -> List[Dict[str, Any]]:
        """
        Parse ffmpeg output to extract frame information.
        
        Args:
            ffmpeg_output: Output from FFmpeg
            
        Returns:
            List of dictionaries containing frame data
        """
        frame_data = []
        
        # Extract timestamps from showinfo filter output
        timestamps = []
        for line in ffmpeg_output.splitlines():
            if 'pts_time:' in line:
                # Updated regex to handle both integer and decimal timestamps
                match = re.search(r'pts_time:(\d+(?:\.\d+)?)', line)
                if match:
                    timestamps.append(float(match.group(1)))
        
        # Get all output files
        frame_files = sorted(self.output_dir.glob('*.png'))
        
        # If we have timestamps, create frame data with them
        for i, frame_path in enumerate(frame_files):
            if i < len(timestamps):
                timestamp = timestamps[i]
                is_scene = 'scene_' in frame_path.name
                
                frame_data.append({
                    'timestamp': timestamp,
                    'path': frame_path,
                    'is_scene_change': is_scene
                })
        
        # Sort all frames by timestamp
        frame_data.sort(key=lambda x: x['timestamp'])
        
        return frame_data

    def _format_timecode(self, timestamp: float) -> str:
        """
        Convert timestamp to HH:MM:SS:FF format.
        
        Args:
            timestamp: Timestamp in seconds
            
        Returns:
            Formatted timecode string
        """
        FPS = 25  # Standard PAL framerate
        
        total_frames = int(timestamp * FPS)
        frames = total_frames % FPS
        total_seconds = int(timestamp)
        
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}:{frames:02d}" 