import logging
import asyncio
from typing import Dict, Any, List, Set, Optional
import uuid
import numpy as np

from src.services.graphql_client import GraphQLClient
from src.services.frame_extraction_service import FrameExtractionService
from src.utils.recognition_utils import find_bulk_embeddings

logger = logging.getLogger(__name__)

class ProcessingService:
    """Service for processing cards, generating embeddings, and analyzing clips"""
    
    def __init__(self):
        """Initialize the service with a GraphQL client instance"""
        self.graphql_client = GraphQLClient() # Get the singleton instance

    async def _check_for_cancellation(self, task_id: str) -> bool:
        """Helper to check DB task status for cancellation."""
        try:
            status = await self.graphql_client.get_db_task_status(task_id)
            if status == 'cancelling':
                logger.info(f"Cancellation requested for task {task_id}, stopping processing.")
                await self.graphql_client.update_db_task(task_id, status="cancelled", message="Processing cancelled by user request.")
                
                # Also update the card status to paused so it can be restarted
                try:
                    # First get the card_id from the task
                    card_id = await self._get_card_id_for_task(task_id)
                    if card_id:
                        await self.update_card_status(card_id, "paused")
                        logger.info(f"Updated card {card_id} status to paused after cancellation.")
                    else:
                        logger.error(f"Could not find card_id for task {task_id} during cancellation.")
                except Exception as card_error:
                    logger.error(f"Error updating card status to paused during cancellation: {card_error}")
                
                return True
        except Exception as e:
            logger.error(f"Error checking cancellation status for task {task_id}: {e}")
            # Decide if we should stop on error or continue
            # For now, let's continue but log the error
        return False

    async def update_card_status(self, card_id: str, status: str) -> bool:
        """
        Update the status of a card in the database
        
        Args:
            card_id: ID of the card to update
            status: New status for the card
            
        Returns:
            bool: True if update was successful
        """
        mutation = """
        mutation UpdateCardStatus($card_id: uuid!, $status: String!) {
            update_cards_by_pk(
                pk_columns: {card_id: $card_id},
                _set: {status: $status}
            ) {
                card_id
            }
        }
        """
        
        variables = {
            "card_id": card_id,
            "status": status
        }
        
        try:
            result = await self.graphql_client.execute_async(mutation, variables)
            if not result.get("update_cards_by_pk"):
                logger.error(f"Failed to update card status for card {card_id}")
                return False
                
            logger.info(f"Updated card {card_id} status to {status}")
            return True
        except Exception as e:
            logger.error(f"Error updating card status: {str(e)}")
            return False
    
    async def get_card_config(self, card_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the configuration for a card from the database
        
        Args:
            card_id: ID of the card
            
        Returns:
            Card configuration or None if not found
        """
        query = """
        query GetCardConfigWithProject($card_id: uuid!) {
            card_configs(where: {card_id: {_eq: $card_id}}) {
                config_id
                scene_sensitivity
                fallback_frame_rate
                use_eq
                lut_file
                model_name
                detector_backend
                align
                enforce_detection
                distance_metric
                expand_percentage
                threshold
                normalization
                silent
                refresh_database
                anti_spoofing
                detection_confidence_threshold
            }
            cards_by_pk(card_id: $card_id) {
                project_id
            }
        }
        """
        
        variables = {
            "card_id": card_id
        }
        
        try:
            result = await self.graphql_client.execute_async(query, variables)
            
            config_data = result.get("card_configs")
            card_data = result.get("cards_by_pk")

            if config_data and card_data:
                # Merge config and project_id
                config = config_data[0]
                config['project_id'] = card_data.get('project_id')
                config['card_id'] = card_id # Add card_id for convenience
                return config
            else:
                logger.warning(f"No configuration or card data found for card {card_id}")
                if not config_data:
                    logger.warning("No entry in card_configs table.")
                if not card_data:
                    logger.warning("No entry in cards table.")
                return None
            
        except Exception as e:
            logger.error(f"Error getting card config: {str(e)}")
            return None
    
    async def get_consent_faces_without_embeddings(self, project_id: str) -> List[Dict[str, Any]]:
        """
        Get all consent faces for a project that don't have embeddings
        
        Args:
            project_id: ID of the project
            
        Returns:
            List of consent faces without embeddings
        """
        query = """
        query GetConsentFacesWithoutEmbeddings($project_id: uuid!) {
            consent_profiles(where: {project_id: {_eq: $project_id}}) {
                consent_faces(where: {face_embedding: {_is_null: true}}) {
                    consent_face_id
                    face_image_path
                }
            }
        }
        """
        
        variables = {
            "project_id": project_id
        }
        
        try:
            result = await self.graphql_client.execute_async(query, variables)
            
            if not result or "consent_profiles" not in result:
                logger.warning(f"No consent profiles found for project: {project_id}")
                return []
                
            # Flatten the structure to get a list of faces
            faces_without_embeddings = []
            for profile in result["consent_profiles"]:
                for face in profile.get("consent_faces", []):
                    faces_without_embeddings.append({
                        "consent_face_id": face["consent_face_id"],
                        "face_image_path": face["face_image_path"],
                    })
                    
            logger.info(f"Found {len(faces_without_embeddings)} consent faces without embeddings for project {project_id}")
            return faces_without_embeddings
            
        except Exception as e:
            logger.error(f"Error getting consent faces without embeddings: {str(e)}")
            return []
            
    async def update_face_embedding(self, face_id: str, embedding: List[float]) -> bool:
        """
        Update the embedding for a consent face
        
        Args:
            face_id: ID of the consent face
            embedding: Face embedding as a list of floats
            
        Returns:
            True if successful, False otherwise
        """
        mutation = """
        mutation UpdateFaceEmbedding($face_id: uuid!, $embedding: jsonb!) {
            update_consent_faces_by_pk(
                pk_columns: {consent_face_id: $face_id},
                _set: {face_embedding: $embedding}
            ) {
                consent_face_id
            }
        }
        """
        # Hasura expects JSONB, so no need to explicitly json.dumps here if passing list
        variables = {"face_id": face_id, "embedding": embedding}
        try:
            result = await self.graphql_client.execute_async(mutation, variables)
            if result.get("update_consent_faces_by_pk"):
                logger.debug(f"Successfully updated embedding for face {face_id}")
                return True
            else:
                logger.warning(f"Failed to update embedding for face {face_id}")
                return False
        except Exception as e:
            logger.error(f"Error updating embedding for face {face_id}: {e}")
            return False
            
    async def generate_consent_embeddings(
        self,
        task_id: str, # Accept task_id
        card_id: str,
        config: Dict[str, Any]
        # Remove cancellation_token
    ) -> bool:
        """
        Generate embeddings for all consent faces without embeddings for a project
        
        Args:
            task_id: The ID of the task record in the database.
            card_id: ID of the card being processed
            config: Processing configuration
            
        Returns:
            True if successful, False otherwise
        """
        project_id = await self._get_project_id_for_card(card_id)
        if not project_id:
            logger.error(f"Could not find project ID for card {card_id}")
            await self.graphql_client.update_db_task(task_id, status="error", message="Could not find project ID")
            return False

        # Update task status in DB
        await self.graphql_client.update_db_task(task_id, status="generating_embeddings", stage="Generating Consent Embeddings")
        await self.update_card_status(card_id, "generating_embeddings")

        logger.info(f"Checking for consent faces that need embeddings for project {project_id}")
        faces_to_process = await self.get_consent_faces_without_embeddings(project_id)

        if not faces_to_process:
            logger.info(f"No consent faces without embeddings found for project {project_id}")
            return True # Not an error, just nothing to do

        face_paths = [face['face_image_path'] for face in faces_to_process]
        face_ids = [face['consent_face_id'] for face in faces_to_process]

        model_name = config.get('model_name', 'Facenet512')
        detector_backend = config.get('detector_backend', 'retinaface')
        normalization = config.get('normalization', 'base')
        align = config.get('align', True)
        enforce_detection = config.get('enforce_detection', False)

        try:
            logger.info(f"Generating embeddings for {len(face_paths)} faces using model={model_name}, detector={detector_backend}")

            # Check for cancellation before starting bulk embedding
            if await self._check_for_cancellation(task_id): return False

            results = find_bulk_embeddings(
                image_paths=face_paths,
                model_name=model_name,
                detector_backend=detector_backend,
                enforce_detection=enforce_detection,
                align=align,
                normalization=normalization
            )

            updated_count = 0
            failed_count = 0
            total_faces = len(face_ids)

            for i, result in enumerate(results):
                # Check for cancellation periodically during update loop
                if i % 10 == 0: # Check every 10 faces
                   if await self._check_for_cancellation(task_id): return False

                face_id = face_ids[i]
                if result and 'embedding' in result and isinstance(result['embedding'], list):
                    if await self.update_face_embedding(face_id, result['embedding']):
                        updated_count += 1
                else:
                    logger.warning(f"Failed to generate embedding for face {face_id} (Path: {face_paths[i]})")
                    failed_count += 1

                # Update progress in DB
                progress = (i + 1) / total_faces
                await self.graphql_client.update_db_task(task_id, progress=progress)


            logger.info(f"Finished generating consent embeddings: {updated_count} updated, {failed_count} failed.")
            if failed_count > 0:
                 await self.graphql_client.update_db_task(task_id, message=f"Completed embedding generation with {failed_count} failures.")
            return True

        except Exception as e:
            logger.exception(f"Error during consent embedding generation for project {project_id}: {e}")
            await self.graphql_client.update_db_task(task_id, status="error", message=f"Embedding generation failed: {e}")
            return False
            
    async def get_queued_clips(self, card_id: str) -> List[Dict[str, Any]]:
        """
        Get all clips for a card that are in 'queued' or 'extracting_frames' status
        
        Args:
            card_id: ID of the card
            
        Returns:
            List of clip objects
        """
        query = """
        query GetQueuedClips($card_id: uuid!) {
            clips(
                where: {
                    card_id: {_eq: $card_id},
                    status: {_in: ["queued", "extracting_frames"]}
                }
            ) {
                clip_id
                path
                filename
                status
            }
        }
        """
        
        variables = {
            "card_id": card_id
        }
        
        try:
            result = await self.graphql_client.execute_async(query, variables)
            return result.get("clips", [])
        except Exception as e:
            logger.error(f"Error fetching queued clips: {str(e)}")
            return []

    async def get_queued_clips_count(self, card_id: str) -> int:
        """
        Get count of clips for a card that are in 'queued' or 'extracting_frames' status
        
        Args:
            card_id: ID of the card
            
        Returns:
            Count of queued clips
        """
        query = """
        query GetQueuedClipsCount($card_id: uuid!) {
            clips_aggregate(
                where: {
                    card_id: {_eq: $card_id},
                    status: {_in: ["queued", "extracting_frames"]}
                }
            ) {
                aggregate {
                    count
                }
            }
        }
        """
        
        variables = {
            "card_id": card_id
        }
        
        try:
            result = await self.graphql_client.execute_async(query, variables)
            return result.get("clips_aggregate", {}).get("aggregate", {}).get("count", 0)
        except Exception as e:
            logger.error(f"Error fetching queued clips count: {str(e)}")
            return 0

    async def process_card(self, task_id: str, card_id: str, config: Dict[str, Any]) -> bool:
        """
        Process a card, including:
        1. Generate embeddings for consent faces if needed
        2. Extract frames from clips if needed
        3. Process frames to detect and match faces
        
        Args:
            task_id: The ID of the task record in the database.
            card_id: ID of the card to process
            config: Configuration for processing
            
        Returns:
            bool: True if processing was successful
        """
        logger.info(f"Starting main processing for card {card_id}, task {task_id}")
        overall_success = True

        try:
            # 1. Generate Consent Embeddings (if needed)
            logger.info(f"Step 1: Generating consent embeddings for card {card_id}, task {task_id}")
            embeddings_success = await self.generate_consent_embeddings(task_id, card_id, config)
            if not embeddings_success:
                # Error status already set within generate_consent_embeddings
                logger.error(f"Failed to generate consent embeddings for card {card_id}, task {task_id}")
                await self.update_card_status(card_id, "error")
                return False # Treat this as a critical failure

            # Check for cancellation after embedding generation
            if await self._check_for_cancellation(task_id): return False

            # 2. Process Clips
            logger.info(f"Step 2: Processing clips for card {card_id}, task {task_id}")
            await self.graphql_client.update_db_task(task_id, status="processing_clips", stage="Processing Clips", progress=0.0) # Reset progress for clip stage
            await self.update_card_status(card_id, "processing") # General processing status

            clips_to_process = await self.get_queued_clips(card_id)
            total_clips = len(clips_to_process)
            processed_clips = 0
            failed_clips = 0

            if not clips_to_process:
                logger.warning(f"No queued clips found for card {card_id}. Skipping clip processing.")
            else:
                frame_extraction_service = FrameExtractionService(self.graphql_client)
                for i, clip in enumerate(clips_to_process):
                    clip_id = clip['clip_id']
                    clip_filename = clip['filename']
                    logger.info(f"Processing clip {i+1}/{total_clips}: {clip_id} ({clip_filename}) for task {task_id}")

                    # Check for cancellation before processing each clip
                    if await self._check_for_cancellation(task_id): return False

                    try:
                        # TODO: Add actual clip processing logic here (frame extraction, detection, recognition)
                        clip_success = await frame_extraction_service.process_clip(clip_id, config)

                        if clip_success:
                            logger.info(f"Successfully processed clip {clip_id}")
                            processed_clips += 1
                            # TODO: Update clip status to 'processing_complete' or similar via service call
                            await frame_extraction_service.update_clip_status(clip_id, "extraction_complete") # Example
                        else:
                            logger.warning(f"Failed to process clip {clip_id}")
                            failed_clips += 1
                            # Status updated to 'error' within frame_extraction_service.process_clip

                    except Exception as clip_error:
                        logger.exception(f"Unexpected error processing clip {clip_id}: {clip_error}")
                        failed_clips += 1
                        await frame_extraction_service.update_clip_status(clip_id, "error", str(clip_error))

                    # Update overall progress in DB
                    progress = (i + 1) / total_clips
                    await self.graphql_client.update_db_task(task_id, progress=progress)

            # 3. Finalize
            final_message = f"Processing complete. {processed_clips}/{total_clips} clips processed successfully."
            if failed_clips > 0:
                final_message += f" {failed_clips} clips failed."
                overall_success = False # Indicate partial failure if clips failed

            logger.info(f"Finalizing processing for card {card_id}, task {task_id}. {final_message}")
            await self.graphql_client.update_db_task(task_id, status="complete", stage="Complete", progress=1.0, message=final_message)
            await self.update_card_status(card_id, "complete")
            return True # Return True even if some clips failed, as the card processing itself finished

        except Exception as e:
            logger.exception(f"Critical error during card processing for card {card_id}, task {task_id}: {e}")
            await self.graphql_client.update_db_task(task_id, status="error", stage="Error", message=f"Critical processing error: {e}")
            await self.update_card_status(card_id, "error")
            return False

    async def _get_project_id_for_card(self, card_id: str) -> Optional[str]:
        """
        Get the project ID for a card
        
        Args:
            card_id: ID of the card
            
        Returns:
            Project ID or None if not found
        """
        query = """
        query GetProjectForCard($card_id: uuid!) {
            cards_by_pk(card_id: $card_id) {
                project_id
            }
        }
        """
        
        variables = {
            "card_id": card_id
        }
        
        try:
            result = await self.graphql_client.execute_async(query, variables)
            card_data = result.get("cards_by_pk")
            if card_data:
                return card_data.get("project_id")
            else:
                return None
        except Exception as e:
            logger.error(f"Error fetching project ID for card: {str(e)}")
            return None

    async def _get_card_id_for_task(self, task_id: str) -> Optional[str]:
        """
        Get the card ID associated with a processing task
        
        Args:
            task_id: ID of the task
            
        Returns:
            Card ID or None if not found
        """
        query = """
        query GetCardIdForTask($task_id: uuid!) {
            processing_tasks_by_pk(task_id: $task_id) {
                card_id
            }
        }
        """
        
        variables = {
            "task_id": task_id
        }
        
        try:
            result = await self.graphql_client.execute_async(query, variables)
            task_data = result.get("processing_tasks_by_pk")
            if task_data:
                return task_data.get("card_id")
            else:
                return None
        except Exception as e:
            logger.error(f"Error fetching card ID for task: {str(e)}")
            return None

# Global instance
processing_service = ProcessingService() 