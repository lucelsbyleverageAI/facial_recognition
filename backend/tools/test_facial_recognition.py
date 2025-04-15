#!/usr/bin/env python3
"""
Test script for the facial recognition processing pipeline.
This script demonstrates how to use the continuous processing workflow.
"""

import asyncio
import logging
import os
import sys
import uuid
from pathlib import Path
import time

# Add parent directory to path to resolve imports
sys.path.append(str(Path(__file__).parent.parent))

from src.services.graphql_client import GraphQLClient
from src.services.frame_analysis_service import FrameAnalysisService
from src.services.processing_service import ProcessingService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

async def print_processing_status(card_id: str, processing_service: ProcessingService):
    """Print a detailed status report for a card"""
    try:
        status = await processing_service.get_processing_status(card_id)
        
        print("\n=== Processing Status ===")
        print(f"Queued Clips: {status['queued_clips']}")
        print(f"Unprocessed Frames: {status['unprocessed_frames']}")
        print(f"Unmatched Faces: {status['unmatched_faces']}")
        print(f"Total Items: {status['total_items']}")
        print("========================\n")
        
        return status['total_items'] > 0
    except Exception as e:
        logger.error(f"Error getting processing status: {e}")
        return False

async def test_continuous_processing(card_id: str, task_id: str = None):
    """
    Test the continuous processing workflow for a specific card.
    
    Args:
        card_id: The ID of the card to process
        task_id: Optional task ID (creates a new one if not provided)
    """
    graphql_client = GraphQLClient()
    processing_service = ProcessingService()
    
    # Print initial status
    logger.info(f"Checking initial status for card {card_id}")
    has_work = await print_processing_status(card_id, processing_service)
    
    if not has_work:
        logger.warning("No work found for the card. Do you need to add clips or set their status to 'queued'?")
        return False
    
    # Create task ID if not provided
    if task_id is None:
        task_id = str(uuid.uuid4())
        logger.info(f"Created new task ID: {task_id}")
        # Register task in database
        await graphql_client.create_db_task(card_id)
    
    # Get card configuration
    config = await processing_service.get_card_config(card_id)
    if not config:
        logger.error(f"Failed to retrieve configuration for card {card_id}")
        return False
    
    logger.info(f"Retrieved configuration for card {card_id}")
    
    # Start continuous processing
    logger.info("Starting continuous processing...")
    
    try:
        # Start processing in background
        processing_task = asyncio.create_task(
            processing_service.process_card(task_id, card_id, config)
        )
        
        # Monitor status while processing
        while not processing_task.done():
            # Get task status from database
            db_task = await graphql_client.get_db_task_status(task_id)
            logger.info(f"Task status: {db_task}")
            
            # Print detailed status
            await print_processing_status(card_id, processing_service)
            
            # Wait before checking again
            await asyncio.sleep(3)
        
        # Get the result
        result = processing_task.result()
        logger.info(f"Processing completed with result: {result}")
        
        # Final status check
        await print_processing_status(card_id, processing_service)
        
        return result
    except Exception as e:
        logger.exception(f"Error during continuous processing: {e}")
        return False

async def main():
    """
    Main function to run the test.
    """
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='Test facial recognition processing')
    parser.add_argument('--card-id', type=str, required=True, help='ID of the card to process')
    parser.add_argument('--task-id', type=str, help='Optional task ID')
    args = parser.parse_args()
    
    # Run the test
    await test_continuous_processing(args.card_id, args.task_id)

if __name__ == '__main__':
    asyncio.run(main()) 