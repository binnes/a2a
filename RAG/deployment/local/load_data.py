#!/usr/bin/env python3
"""
Data loader script for automatically loading Shakespeare text into Milvus.
Runs as a one-time job during deployment.
"""

import os
import sys
import time
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.settings import Settings
from services.milvus_client import MilvusClient
from services.document_processor import DocumentProcessor
from services.watsonx_client import WatsonxClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def wait_for_milvus(settings: Settings, max_retries: int = 30, delay: int = 5):
    """Wait for Milvus to be ready."""
    logger.info("Waiting for Milvus to be ready...")
    
    for attempt in range(max_retries):
        try:
            # Try to initialize MilvusClient (which connects automatically)
            test_client = MilvusClient(settings)
            logger.info("✓ Milvus is ready")
            return True
        except Exception as e:
            logger.warning(f"Milvus not ready (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(delay)
    
    logger.error("Milvus failed to become ready")
    return False


def load_shakespeare_data():
    """Load Shakespeare text into Milvus."""
    try:
        logger.info("=== Starting Data Loader ===")
        
        # Initialize settings
        settings = Settings()
        logger.info(f"Milvus host: {settings.milvus_host}:{settings.milvus_port}")
        logger.info(f"Collection: {settings.milvus_collection_name}")
        
        # Wait for Milvus to be ready
        if not wait_for_milvus(settings):
            logger.error("Failed to connect to Milvus")
            sys.exit(1)
        
        # Initialize clients (after Milvus is ready)
        watsonx_client = WatsonxClient(settings)
        milvus_client = MilvusClient(settings)
        doc_processor = DocumentProcessor(settings)
        
        # Check if collection already has data
        try:
            stats = milvus_client.get_stats()
            if stats.get('num_entities', 0) > 0:
                logger.info(f"Collection already contains {stats['num_entities']} documents")
                logger.info("Skipping data load (collection not empty)")
                return
        except Exception as e:
            logger.info(f"Collection stats check failed (may not exist yet): {e}")
        
        # Find Shakespeare text file
        shakespeare_file = Path("data/reference/complete works of Shakespear.txt")
        
        if not shakespeare_file.exists():
            logger.error(f"Shakespeare file not found: {shakespeare_file}")
            logger.error("Please ensure the file exists in data/reference/")
            sys.exit(1)
        
        logger.info(f"Found Shakespeare file: {shakespeare_file}")
        
        # Process the file
        logger.info("Processing Shakespeare text...")
        chunks = doc_processor.process_file(str(shakespeare_file))
        logger.info(f"Created {len(chunks)} chunks from Shakespeare text")
        
        # Generate embeddings and index the chunks
        logger.info("Generating embeddings and indexing chunks in Milvus...")
        texts = [chunk["text"] for chunk in chunks]
        embeddings = watsonx_client.generate_embeddings(texts)
        
        ids = [chunk["id"] for chunk in chunks]
        sources = [chunk["source"] for chunk in chunks]
        
        milvus_client.insert(
            ids=ids,
            texts=texts,
            vectors=embeddings,
            sources=sources,
        )
        
        # Verify indexing
        stats = milvus_client.get_stats()
        logger.info(f"✓ Successfully indexed {stats.get('num_entities', 0)} documents")
        
        logger.info("=== Data Loading Complete ===")
        
    except Exception as e:
        logger.error(f"Error loading data: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    load_shakespeare_data()

# Made with Bob