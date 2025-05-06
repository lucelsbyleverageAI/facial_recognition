import os
import sys
import json
import asyncio
import logging
from pathlib import Path
import re
from pprint import pprint

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add project root to path if needed
sys.path.append('/Users/lucelsby/Documents/repos/chwarel/facial_recognition')

# Import the service 
from src.services.frame_extraction_service import FrameExtractor

async def run_test():
    """Test frame extraction with detailed diagnostics"""
    
    # 1. Test clip and config data
    clip_id = "3a20781f-5e34-401d-a3b1-61b7f30fba14"
    clip_path = "/Users/lucelsby/Documents/repos/chwarel/facial_recognition/Test Inputs/Watch Folder/Card Test 1/XDROOT/Clip/WhatsApp Video 2025-04-22 at 08.17.03.mp4"
    
    config = {
        "align": False,
        "anti_spoofing": False,
        "detection_confidence_threshold": 0.5,
        "detector_backend": "retinaface",
        "distance_metric": "euclidean_l2",
        "enforce_detection": False,
        "expand_percentage": 0,
        "fallback_frame_rate": 6,
        "lut_file": None,
        "model_name": "Facenet512",
        "normalization": "base",
        "refresh_database": True,
        "scene_sensitivity": 0.2,
        "silent": True,
        "threshold": None,
        "use_eq": True
    }
    
    logger.info(f"===== STARTING DIAGNOSTIC TEST =====")
    logger.info(f"Clip ID: {clip_id}")
    logger.info(f"Clip Path: {clip_path}")
    logger.info(f"Config: {json.dumps(config, indent=2)}")
    
    # 2. Verify clip exists
    if not os.path.exists(clip_path):
        logger.error(f"Clip file not found at path: {clip_path}")
        return
    
    # 3. Initialize extractor with debug patches
    # Create a modified version of FrameExtractor just for this test
    class DiagnosticFrameExtractor(FrameExtractor):
        def _build_ffmpeg_command(self):
            """Add higher log level to command"""
            cmd = ["ffmpeg", "-v", "info", "-i", str(self.clip_path)]
            filter_complex = self._build_filter_complex()
            
            scene_pattern = str(self.output_dir / f"scene_%04d.png")
            fallback_pattern = str(self.output_dir / f"fallback_%04d.png")
    
            command = cmd + [
                "-filter_complex", filter_complex,
                "-map", "[vout1]", "-vsync", "vfr", "-q:v", "2", scene_pattern,
                "-map", "[vout2]", "-vsync", "vfr", "-q:v", "2", fallback_pattern
            ]
            return command
        
        async def extract_frames(self):
            """Enhanced extraction with diagnostic logging"""
            logger.info(f"=== Starting diagnostic frame extraction ===")
            
            try:
                # Build and log ffmpeg command
                ffmpeg_cmd = self._build_ffmpeg_command()
                logger.info(f"A. FFMPEG CMD: {' '.join(ffmpeg_cmd)}")
                log_file = self.output_dir / "ffmpeg_output.log"
                
                # Run ffmpeg process - capture both stdout and stderr
                import subprocess
                try:
                    process = subprocess.run(
                        ffmpeg_cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,  # Merge stderr into stdout
                        text=True,
                        check=True
                    )
                    self.ffmpeg_output = process.stdout
                    logger.info("FFmpeg process completed successfully")
                except subprocess.CalledProcessError as e:
                    logger.error("FFmpeg process failed!")
                    logger.error(f"Error: {str(e)}")
                    raise RuntimeError(f"FFmpeg failed: {e}")
                
                # Log ffmpeg output
                with open(log_file, 'w') as f:
                    f.write(self.ffmpeg_output)
                
                # Check for pts_time lines (quick diagnostic)
                pts_lines = [line for line in self.ffmpeg_output.splitlines() 
                           if 'pts_time:' in line]
                logger.info(f"B. PTS_TIME LINES FOUND: {len(pts_lines)}")
                if pts_lines:
                    logger.info("B. SAMPLE PTS LINES:")
                    for line in pts_lines[:5]:  # Show a few examples
                        logger.info(f"   {line}")
                
                # Get all output files
                frame_files = sorted(self.output_dir.glob('*.png'))
                logger.info(f"C. TOTAL PNG FILES: {len(frame_files)}")
                
                # Log some filenames
                if frame_files:
                    frame_names = [p.name for p in frame_files[:10]]
                    logger.info(f"D. SAMPLE FILENAMES: {frame_names}")
                
                if not frame_files:
                    logger.error("No frames were extracted!")
                    return []
                
                # Create Frame objects
                frames = []
                for frame_file in frame_files:
                    frame = {
                        "frame_id": "test-id",
                        "clip_id": self.clip_id,
                        "timestamp": "00:00:00:00",  # Default
                        "raw_frame_image_path": str(frame_file.absolute()),
                    }
                    frames.append(frame)
                
                # Try to parse timestamps - with original & enhanced regex
                try:
                    # Original regex
                    frame_data_orig = self._parse_ffmpeg_output_original(self.ffmpeg_output)
                    
                    # Enhanced regex
                    frame_data_enhanced = self._parse_ffmpeg_output_enhanced(self.ffmpeg_output)
                    
                    logger.info(f"E. TIMESTAMP PARSING:")
                    logger.info(f"   Original regex matches: {len(frame_data_orig)}")
                    logger.info(f"   Enhanced regex matches: {len(frame_data_enhanced)}")
                    
                    # Show timestamp comparison for diagnostic
                    if frame_data_orig and frame_data_enhanced:
                        logger.info("TIMESTAMP SAMPLE (Original vs Enhanced):")
                        for i in range(min(5, len(frame_data_orig), len(frame_data_enhanced))):
                            orig_ts = frame_data_orig[i]['timestamp'] if i < len(frame_data_orig) else None
                            enh_ts = frame_data_enhanced[i]['timestamp'] if i < len(frame_data_enhanced) else None
                            logger.info(f"   Frame {i}: Orig={orig_ts}, Enhanced={enh_ts}")
                    
                    # Test both mapping methods
                    if len(frame_data_enhanced) == len(frames):
                        logger.info("PERFECT MATCH: Same number of timestamps and frames!")
                        # Direct mapping should work
                        for i, data in enumerate(frame_data_enhanced):
                            frames[i]["timestamp"] = self._format_timecode(data['timestamp'])
                    else:
                        logger.warning(f"MISMATCH: {len(frame_data_enhanced)} timestamps vs {len(frames)} frames")
                        
                        # Test enhanced mapping by filename
                        logger.info("Attempting filename-based timestamp mapping...")
                        
                        # Create map of frame index to timestamp
                        ts_map = {}
                        for line in self.ffmpeg_output.splitlines():
                            if 'pts_time:' in line:
                                m = re.search(r"n:(\d+).*pts_time:(\d+(?:\.\d+)?)", line)
                                if m:
                                    frame_idx, ts = int(m.group(1)), float(m.group(2))
                                    ts_map[frame_idx] = ts
                        
                        # Map timestamps to frames by filename number
                        matched = 0
                        for frame in frames:
                            path = Path(frame["raw_frame_image_path"])
                            match = re.search(r'(\d+)\.png$', path.name)
                            if match:
                                idx = int(match.group(1))
                                if idx in ts_map:
                                    frame["timestamp"] = self._format_timecode(ts_map[idx])
                                    matched += 1
                        
                        logger.info(f"Filename mapping success rate: {matched}/{len(frames)}")
                                    
                except Exception as e:
                    logger.error(f"Failed to parse frame timestamps: {str(e)}")
                    import traceback
                    logger.error(traceback.format_exc())
                
                # Count frames with non-zero timestamps
                non_zero_count = sum(1 for f in frames if f["timestamp"] != "00:00:00:00")
                logger.info(f"FRAMES WITH NON-ZERO TIMESTAMPS: {non_zero_count}/{len(frames)}")
                
                return frames
            
            except Exception as e:
                logger.error(f"Frame extraction failed: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
                raise
        
        def _parse_ffmpeg_output_original(self, ffmpeg_output):
            """Original implementation for comparison"""
            frame_data = []
            
            timestamps = []
            for line in ffmpeg_output.splitlines():
                if 'pts_time:' in line:
                    match = re.search(r'pts_time:(\d+\.\d+)', line)
                    if match:
                        timestamps.append(float(match.group(1)))
            
            frame_files = sorted(self.output_dir.glob('*.png'))
            
            for i, frame_path in enumerate(frame_files):
                if i < len(timestamps):
                    timestamp = timestamps[i]
                    is_scene = 'scene_' in frame_path.name
                    
                    frame_data.append({
                        'timestamp': timestamp,
                        'path': frame_path,
                        'is_scene_change': is_scene
                    })
            
            frame_data.sort(key=lambda x: x['timestamp'])
            return frame_data
        
        def _parse_ffmpeg_output_enhanced(self, ffmpeg_output):
            """Enhanced implementation with fixes"""
            frame_data = []
            
            timestamps = []
            for line in ffmpeg_output.splitlines():
                if 'pts_time:' in line:
                    # Enhanced regex that works with integer timestamps too
                    match = re.search(r'pts_time:(\d+(?:\.\d+)?)', line)
                    if match:
                        timestamps.append(float(match.group(1)))
            
            frame_files = sorted(self.output_dir.glob('*.png'))
            
            for i, frame_path in enumerate(frame_files):
                if i < len(timestamps):
                    timestamp = timestamps[i]
                    is_scene = 'scene_' in frame_path.name
                    
                    frame_data.append({
                        'timestamp': timestamp,
                        'path': frame_path,
                        'is_scene_change': is_scene
                    })
            
            frame_data.sort(key=lambda x: x['timestamp'])
            return frame_data
    
    # Initialize extractor
    extractor = DiagnosticFrameExtractor(
        clip_path=clip_path,
        clip_id=clip_id,
        config=config
    )
    
    # 4. Check FFmpeg is installed
    if not extractor.check_ffmpeg():
        logger.error("FFmpeg not installed. Please install FFmpeg to run this test.")
        return
    
    # 5. Run the extraction
    try:
        frames = await extractor.extract_frames()
        
        # 6. Analyze results
        logger.info(f"===== TEST RESULTS =====")
        logger.info(f"Total frames extracted: {len(frames)}")
        
        # Check timestamps
        timestamps = [frame["timestamp"] for frame in frames]
        zero_timestamps = [ts for ts in timestamps if ts == "00:00:00:00"]
        
        logger.info(f"Frames with zero timestamp: {len(zero_timestamps)}/{len(frames)}")
        
        if len(zero_timestamps) == len(frames):
            logger.error("ALL timestamps are zero - bug still present!")
        elif len(zero_timestamps) > 0:
            logger.warning("SOME timestamps are zero - partial fix")
        else:
            logger.info("SUCCESS! All frames have valid timestamps")
        
        # Print a few examples
        if frames:
            logger.info("Sample frame data:")
            for i in range(min(5, len(frames))):
                logger.info(f"Frame {i+1}: {frames[i]['timestamp']} - {Path(frames[i]['raw_frame_image_path']).name}")
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    # Run the test
    asyncio.run(run_test())