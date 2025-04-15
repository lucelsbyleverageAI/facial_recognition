import logging
import os
import uuid
import cv2
import numpy as np
from typing import Dict, Any, List, Optional
from pathlib import Path

from deepface import DeepFace
from deepface.modules import representation, detection, verification

from src.services.graphql_client import GraphQLClient

# Configure logging
logger = logging.getLogger(__name__)

class FrameAnalysisService:
    """
    Service for analyzing frames, detecting faces, and matching against consent profiles.
    This service processes frames that have already been extracted from clips.
    """
    
    def __init__(self, graphql_client: GraphQLClient):
        """Initialize with a GraphQL client for database operations"""
        self.graphql_client = graphql_client
        self.logger = logging.getLogger(__name__)
    
    async def process_frames(self, card_id: str, task_id: str, config: Dict[str, Any]) -> bool:
        """
        Process all queued or partially processed frames for a card.
        Detects faces in frames and stores them in the database.
        
        Args:
            card_id: The ID of the card being processed
            task_id: The ID of the processing task
            config: Configuration parameters for face detection
            
        Returns:
            bool: True if processing was successful (even with some errors), False if critical failure
        """
        try:
            # Get frames with status 'queued' or 'detecting_faces'
            frames = await self.get_frames_to_process(card_id)
            total_frames = len(frames)
            
            if not frames:
                self.logger.info(f"No frames to process for card {card_id}")
                return True
            
            self.logger.info(f"Processing {total_frames} frames for card {card_id}")
            
            # Track progress
            processed_frames = 0
            failed_frames = 0
            
            # Process each frame
            for i, frame in enumerate(frames):
                frame_id = frame["frame_id"]
                raw_image_path = frame["raw_frame_image_path"]
                
                # Check for cancellation every 5 frames
                if i % 5 == 0:
                    cancelled = await self._check_cancellation(task_id)
                    if cancelled:
                        return False
                
                try:
                    self.logger.debug(f"Processing frame {i+1}/{total_frames}: {frame_id}")
                    
                    # Update frame status to 'detecting_faces'
                    await self.update_frame_status(frame_id, "detecting_faces")
                    
                    # Detect faces in the frame
                    detection_success = await self.process_frame(frame_id, raw_image_path, config)
                    
                    if detection_success:
                        # Update frame status to 'detection_complete'
                        await self.update_frame_status(frame_id, "detection_complete")
                        processed_frames += 1
                    else:
                        # Set to error if detection failed
                        await self.update_frame_status(frame_id, "error")
                        failed_frames += 1
                
                except Exception as e:
                    self.logger.error(f"Error processing frame {frame_id}: {str(e)}")
                    await self.update_frame_status(frame_id, "error")
                    failed_frames += 1
                
                # Update task progress
                progress = (i + 1) / total_frames
                await self.graphql_client.update_db_task(
                    task_id, 
                    progress=progress, 
                    message=f"Processed {i+1}/{total_frames} frames. {failed_frames} failures."
                )
            
            self.logger.info(f"Completed frame processing: {processed_frames} successful, {failed_frames} failed")
            return True
        
        except Exception as e:
            self.logger.exception(f"Critical error during frame processing for card {card_id}: {str(e)}")
            return False
    
    async def process_frame(self, frame_id: str, raw_image_path: str, config: Dict[str, Any]) -> bool:
        """
        Process a single frame to detect faces.
        
        Args:
            frame_id: ID of the frame to process
            raw_image_path: Path to the raw frame image
            config: Configuration parameters for face detection
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Extract faces from the frame
            face_objs = DeepFace.extract_faces(
                img_path=raw_image_path,
                detector_backend=config.get('detector_backend', 'retinaface'),
                enforce_detection=config.get('enforce_detection', False),
                align=config.get('align', True),
                expand_percentage=config.get('expand_percentage', 0),
                grayscale=False
            )
            
            self.logger.debug(f"Found {len(face_objs)} faces in frame {frame_id}")
            
            # Process and store faces that meet confidence threshold
            for face_obj in face_objs:
                confidence = face_obj['confidence']
                if confidence >= config.get('detection_confidence_threshold', 0.5):
                    # Generate embedding for the detected face
                    embedding_obj = representation.represent(
                        img_path=face_obj['face'],  # Pass the extracted face array
                        model_name=config.get('model_name', 'Facenet512'),
                        enforce_detection=False,  # Already detected
                        detector_backend="skip",  # Skip detection since we have the face
                        align=config.get('align', True),
                        normalization=config.get('normalization', 'base')
                    )
                    
                    # Create facial area object
                    facial_area = {
                        'x': int(face_obj['facial_area']['x']),
                        'y': int(face_obj['facial_area']['y']),
                        'w': int(face_obj['facial_area']['w']),
                        'h': int(face_obj['facial_area']['h'])
                    }
                    
                    # Add eye coordinates if available
                    if 'left_eye' in face_obj['facial_area']:
                        facial_area['left_eye'] = face_obj['facial_area']['left_eye']
                    if 'right_eye' in face_obj['facial_area']:
                        facial_area['right_eye'] = face_obj['facial_area']['right_eye']
                    
                    # Get embeddings as a list
                    embeddings = embedding_obj[0]['embedding']
                    if hasattr(embeddings, 'tolist'):
                        embeddings = embeddings.tolist()
                    
                    # Store the detected face in the database
                    detection_id = await self.store_detected_face(
                        frame_id,
                        facial_area,
                        float(confidence),
                        embeddings
                    )
                    
                    if not detection_id:
                        self.logger.warning(f"Failed to store detected face for frame {frame_id}")
            
            return True
        
        except Exception as e:
            self.logger.error(f"Error processing frame {frame_id}: {str(e)}")
            return False
    
    async def match_faces(self, card_id: str, task_id: str, config: Dict[str, Any], embeddings_cache: Dict[str, Any]) -> bool:
        """
        Match all detected faces against consent profiles.
        
        Args:
            card_id: ID of the card being processed
            task_id: ID of the processing task
            config: Configuration parameters for face matching
            embeddings_cache: Dictionary of consent profile embeddings
            
        Returns:
            bool: True if matching was successful (even with some errors), False if critical failure
        """
        try:
            # Get faces with status 'queued' or 'matching_faces'
            faces = await self.get_faces_to_match(card_id)
            total_faces = len(faces)
            
            if not faces:
                self.logger.info(f"No faces to match for card {card_id}")
                return True
            
            self.logger.info(f"Matching {total_faces} faces for card {card_id}")
            
            # Track progress
            matched_faces = 0
            failed_faces = 0
            
            # Process each face
            for i, face in enumerate(faces):
                detection_id = face["detection_id"]
                frame_id = face["frame_id"]
                embeddings = face["face_embeddings"]
                
                # Check for cancellation every 10 faces
                if i % 10 == 0:
                    cancelled = await self._check_cancellation(task_id)
                    if cancelled:
                        return False
                
                try:
                    self.logger.debug(f"Matching face {i+1}/{total_faces}: {detection_id}")
                    
                    # Update face status to 'matching_faces'
                    await self.update_detected_face_status(detection_id, "matching_faces")
                    
                    # Match face against consent profiles
                    match_success = await self.match_face(
                        detection_id, 
                        embeddings, 
                        face["facial_area"],
                        embeddings_cache, 
                        config
                    )
                    
                    # Update face status to 'matching_complete'
                    await self.update_detected_face_status(detection_id, "matching_complete")
                    matched_faces += 1
                
                except Exception as e:
                    self.logger.error(f"Error matching face {detection_id}: {str(e)}")
                    await self.update_detected_face_status(detection_id, "error")
                    failed_faces += 1
                
                # Update task progress
                progress = (i + 1) / total_faces
                await self.graphql_client.update_db_task(
                    task_id, 
                    progress=progress, 
                    message=f"Matched {i+1}/{total_faces} faces. {failed_faces} failures."
                )
            
            # Visualize all frames after matching
            await self.visualize_all_frames(card_id, task_id)
            
            self.logger.info(f"Completed face matching: {matched_faces} successful, {failed_faces} failed")
            return True
        
        except Exception as e:
            self.logger.exception(f"Critical error during face matching for card {card_id}: {str(e)}")
            return False
    
    async def match_face(
        self, 
        detection_id: str, 
        embeddings: List[float], 
        facial_area: Dict[str, Any],
        embeddings_cache: Dict[str, Any], 
        config: Dict[str, Any]
    ) -> bool:
        """
        Match a detected face against consent profiles.
        
        Args:
            detection_id: ID of the detected face
            embeddings: Face embeddings to match
            facial_area: Facial area coordinates
            embeddings_cache: Dictionary of consent profile embeddings
            config: Configuration parameters for face matching
            
        Returns:
            bool: True if matching was successful (even if no match found), False if error
        """
        try:
            if not embeddings_cache or 'profiles' not in embeddings_cache:
                self.logger.warning("Empty embeddings cache - no matches possible")
                return True  # Not an error, just no matches possible
            
            best_match = None
            best_distance = float('inf')
            
            # Get distance metric from config
            distance_metric = config.get('distance_metric', 'euclidean_l2')
            
            # Iterate through all profiles and their faces
            for profile in embeddings_cache['profiles']:
                for face in profile['faces']:
                    if face['embedding'] is None:
                        continue
                    
                    # Calculate distance between embeddings
                    source_embedding = face['embedding']
                    distance = verification.find_distance(
                        source_embedding,
                        embeddings,
                        distance_metric
                    )
                    
                    # Get threshold (from config or use default based on model)
                    threshold = config.get('threshold')
                    if threshold is None:
                        threshold = verification.find_threshold(
                            config.get('model_name', 'Facenet512'),
                            distance_metric
                        )
                    
                    # Check if this is the best match so far
                    if distance <= threshold and distance < best_distance:
                        best_distance = distance
                        best_match = {
                            'consent_face_id': face['consent_face_id'],
                            'distance': distance,
                            'threshold': threshold
                        }
            
            # If we found a match, create and store a FaceMatch object
            if best_match:
                match_id = await self.store_face_match(
                    detection_id, 
                    best_match['consent_face_id'],
                    best_match['distance'],
                    best_match['threshold'],
                    facial_area,  # Source coordinates
                    facial_area   # Target coordinates (using same for now)
                )
                
                if not match_id:
                    self.logger.warning(f"Failed to store face match for detection {detection_id}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error matching face {detection_id}: {str(e)}")
            return False
    
    async def visualize_all_frames(self, card_id: str, task_id: str) -> bool:
        """
        Create visualizations for all frames with detected faces.
        
        Args:
            card_id: ID of the card being processed
            task_id: ID of the processing task
            
        Returns:
            bool: True if visualization was successful
        """
        try:
            # Get all frames for the card that have completed detection
            query = """
            query GetFramesForVisualization($card_id: uuid!) {
                frames(
                    where: {
                        clip: {card_id: {_eq: $card_id}},
                        status: {_in: ["detection_complete"]}
                    }
                ) {
                    frame_id
                    raw_frame_image_path
                }
            }
            """
            
            variables = {
                "card_id": card_id
            }
            
            result = await self.graphql_client.execute_async(query, variables)
            frames = result.get("frames", [])
            
            self.logger.info(f"Visualizing {len(frames)} frames for card {card_id}")
            
            for i, frame in enumerate(frames):
                frame_id = frame["frame_id"]
                raw_image_path = frame["raw_frame_image_path"]
                
                # Check for cancellation periodically
                if i % 10 == 0:
                    cancelled = await self._check_cancellation(task_id)
                    if cancelled:
                        return False
                
                # Create visualization
                processed_path = await self.visualize_frame(frame_id, raw_image_path)
                
                if processed_path:
                    # Update frame with processed image path and set to recognition_complete
                    await self.update_frame_with_processed_image(frame_id, processed_path, "recognition_complete")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error visualizing frames for card {card_id}: {str(e)}")
            return False
    
    async def visualize_frame(self, frame_id: str, raw_image_path: str) -> Optional[str]:
        """
        Create visualization of frame with detected faces.
        Draw bounding boxes (green for matched, red for unmatched).
        
        Args:
            frame_id: ID of the frame to visualize
            raw_image_path: Path to the raw frame image
            
        Returns:
            Optional[str]: Path to the processed image if successful, None otherwise
        """
        try:
            # Get all detected faces for the frame
            query = """
            query GetDetectedFacesForVisualization($frame_id: uuid!) {
                detected_faces(where: {frame_id: {_eq: $frame_id}}) {
                    detection_id
                    facial_area
                    confidence
                    face_matches {
                        match_id
                    }
                }
            }
            """
            
            variables = {
                "frame_id": frame_id
            }
            
            result = await self.graphql_client.execute_async(query, variables)
            detected_faces = result.get("detected_faces", [])
            
            if not detected_faces:
                self.logger.debug(f"No detected faces for frame {frame_id}, skipping visualization")
                # Still mark as complete but don't create visualization
                return raw_image_path
            
            # Load the raw frame image
            frame_image = cv2.imread(raw_image_path)
            if frame_image is None:
                raise ValueError(f"Failed to load image at path: {raw_image_path}")
            
            # Draw bounding boxes and annotations
            for face in detected_faces:
                facial_area = face["facial_area"]
                face_matches = face.get("face_matches", [])
                
                # Green if matched, Red if unmatched
                color = (0, 255, 0) if face_matches else (0, 0, 255)  # BGR format in OpenCV
                thickness = 2
                
                # Draw bounding box
                start_point = (int(facial_area['x']), int(facial_area['y']))
                end_point = (
                    int(facial_area['x'] + facial_area['w']), 
                    int(facial_area['y'] + facial_area['h'])
                )
                cv2.rectangle(frame_image, start_point, end_point, color, thickness)
                
                # Add confidence score
                cv2.putText(
                    frame_image,
                    f"{face['confidence']:.2f}",
                    (int(facial_area['x']), int(facial_area['y'] - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    color,
                    1,
                )
                
                # Add match/no match indicator
                label = "Matched" if face_matches else "Unmatched"
                cv2.putText(
                    frame_image,
                    label,
                    (int(facial_area['x']), int(facial_area['y'] + facial_area['h'] + 15)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    color,
                    1,
                )
            
            # Save the processed image
            # Extract directory from raw path
            base_dir = os.path.dirname(raw_image_path)
            processed_dir = os.path.join(base_dir, "processed")
            os.makedirs(processed_dir, exist_ok=True)
            
            # Use the same filename with "_processed" suffix
            filename = os.path.basename(raw_image_path)
            name, ext = os.path.splitext(filename)
            processed_filename = f"{name}_processed{ext}"
            processed_path = os.path.join(processed_dir, processed_filename)
            
            cv2.imwrite(processed_path, frame_image)
            
            return processed_path
            
        except Exception as e:
            self.logger.error(f"Error visualizing frame {frame_id}: {str(e)}")
            return None
    
    # Database operations
    
    async def get_frames_to_process(self, card_id: str) -> List[Dict[str, Any]]:
        """Get frames with status 'queued' or 'detecting_faces'"""
        query = """
        query GetFramesToProcess($card_id: uuid!) {
            frames(
                where: {
                    clip: {card_id: {_eq: $card_id}},
                    status: {_in: ["queued", "detecting_faces"]}
                },
                order_by: {timestamp: asc}
            ) {
                frame_id
                clip_id
                timestamp
                raw_frame_image_path
                status
            }
        }
        """
        
        variables = {
            "card_id": card_id
        }
        
        try:
            result = await self.graphql_client.execute_async(query, variables)
            return result.get("frames", [])
        except Exception as e:
            self.logger.error(f"Error getting frames to process: {str(e)}")
            return []

    async def get_faces_to_match(self, card_id: str) -> List[Dict[str, Any]]:
        """Get detected faces with status 'queued' or 'matching_faces'"""
        query = """
        query GetFacesToMatch($card_id: uuid!) {
            detected_faces(
                where: {
                    frame: {clip: {card_id: {_eq: $card_id}}},
                    status: {_in: ["queued", "matching_faces"]}
                }
            ) {
                detection_id
                frame_id
                face_embeddings
                facial_area
                confidence
                status
            }
        }
        """
        
        variables = {
            "card_id": card_id
        }
        
        try:
            result = await self.graphql_client.execute_async(query, variables)
            return result.get("detected_faces", [])
        except Exception as e:
            self.logger.error(f"Error getting faces to match: {str(e)}")
            return []

    async def update_frame_status(self, frame_id: str, status: str) -> bool:
        """Update frame status in the database"""
        mutation = """
        mutation UpdateFrameStatus($frame_id: uuid!, $status: String!) {
            update_frames_by_pk(
                pk_columns: {frame_id: $frame_id},
                _set: {status: $status}
            ) {
                frame_id
            }
        }
        """
        
        variables = {
            "frame_id": frame_id,
            "status": status
        }
        
        try:
            result = await self.graphql_client.execute_async(mutation, variables)
            return bool(result.get("update_frames_by_pk"))
        except Exception as e:
            self.logger.error(f"Error updating frame status: {str(e)}")
            return False

    async def update_frame_with_processed_image(self, frame_id: str, processed_image_path: str, status: str) -> bool:
        """Update frame with processed image path and status"""
        mutation = """
        mutation UpdateFrameWithProcessedImage($frame_id: uuid!, $processed_frame_image_path: String!, $status: String!) {
            update_frames_by_pk(
                pk_columns: {frame_id: $frame_id},
                _set: {
                    processed_frame_image_path: $processed_frame_image_path,
                    status: $status
                }
            ) {
                frame_id
            }
        }
        """
        
        variables = {
            "frame_id": frame_id,
            "processed_frame_image_path": processed_image_path,
            "status": status
        }
        
        try:
            result = await self.graphql_client.execute_async(mutation, variables)
            return bool(result.get("update_frames_by_pk"))
        except Exception as e:
            self.logger.error(f"Error updating frame with processed image: {str(e)}")
            return False

    async def update_detected_face_status(self, detection_id: str, status: str) -> bool:
        """Update detected face status in the database"""
        mutation = """
        mutation UpdateDetectedFaceStatus($detection_id: uuid!, $status: String!) {
            update_detected_faces_by_pk(
                pk_columns: {detection_id: $detection_id},
                _set: {status: $status}
            ) {
                detection_id
            }
        }
        """
        
        variables = {
            "detection_id": detection_id,
            "status": status
        }
        
        try:
            result = await self.graphql_client.execute_async(mutation, variables)
            return bool(result.get("update_detected_faces_by_pk"))
        except Exception as e:
            self.logger.error(f"Error updating detected face status: {str(e)}")
            return False

    async def store_detected_face(self, frame_id: str, facial_area: Dict[str, Any], confidence: float, embeddings: List[float]) -> Optional[str]:
        """Store detected face and return detection_id"""
        mutation = """
        mutation InsertDetectedFace($frame_id: uuid!, $facial_area: jsonb!, $confidence: float8!, $embeddings: jsonb!) {
            insert_detected_faces_one(
                object: {
                    frame_id: $frame_id,
                    facial_area: $facial_area,
                    confidence: $confidence,
                    face_embeddings: $embeddings,
                    status: "queued"
                }
            ) {
                detection_id
            }
        }
        """
        
        variables = {
            "frame_id": frame_id,
            "facial_area": facial_area,
            "confidence": confidence,
            "embeddings": embeddings
        }
        
        try:
            result = await self.graphql_client.execute_async(mutation, variables)
            detection = result.get("insert_detected_faces_one")
            if detection:
                return detection.get("detection_id")
            return None
        except Exception as e:
            self.logger.error(f"Error storing detected face: {str(e)}")
            return None

    async def store_face_match(
        self, 
        detection_id: str, 
        consent_face_id: str, 
        distance: float, 
        threshold: float,
        source_coords: Dict[str, Any],
        target_coords: Dict[str, Any]
    ) -> Optional[str]:
        """Store face match and return match_id"""
        mutation = """
        mutation InsertFaceMatch(
            $detection_id: uuid!, 
            $consent_face_id: uuid!, 
            $distance: numeric!,
            $threshold: numeric!,
            $source_x: Int!,
            $source_y: Int!,
            $source_w: Int!,
            $source_h: Int!,
            $target_x: Int!,
            $target_y: Int!,
            $target_w: Int!,
            $target_h: Int!
        ) {
            insert_face_matches_one(
                object: {
                    detection_id: $detection_id,
                    consent_face_id: $consent_face_id,
                    distance: $distance,
                    threshold: $threshold,
                    source_x: $source_x,
                    source_y: $source_y,
                    source_w: $source_w,
                    source_h: $source_h,
                    target_x: $target_x,
                    target_y: $target_y,
                    target_w: $target_w,
                    target_h: $target_h
                }
            ) {
                match_id
            }
        }
        """
        
        variables = {
            "detection_id": detection_id,
            "consent_face_id": consent_face_id,
            "distance": distance,
            "threshold": threshold,
            "source_x": source_coords["x"],
            "source_y": source_coords["y"],
            "source_w": source_coords["w"],
            "source_h": source_coords["h"],
            "target_x": target_coords["x"],
            "target_y": target_coords["y"],
            "target_w": target_coords["w"],
            "target_h": target_coords["h"]
        }
        
        try:
            result = await self.graphql_client.execute_async(mutation, variables)
            match = result.get("insert_face_matches_one")
            if match:
                return match.get("match_id")
            return None
        except Exception as e:
            self.logger.error(f"Error storing face match: {str(e)}")
            return None
    
    async def _check_cancellation(self, task_id: str) -> bool:
        """Helper method to check if task has been cancelled"""
        try:
            status = await self.graphql_client.get_db_task_status(task_id)
            return status == 'cancelling' or status == 'cancelled'
        except Exception as e:
            self.logger.error(f"Error checking cancellation status: {str(e)}")
            return False 