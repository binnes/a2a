"""Milvus vector store client for RAG operations."""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from pymilvus import (  # type: ignore
    connections,
    Collection,
    CollectionSchema,
    FieldSchema,
    DataType,
    utility,
)

from config.settings import Settings

logger = logging.getLogger(__name__)


class MilvusClient:
    """Client for interacting with Milvus vector database."""

    def __init__(self, settings: Settings):
        """Initialize Milvus client.

        Args:
            settings: Application settings containing Milvus configuration
        """
        self.settings = settings
        self.collection: Optional[Collection] = None
        self._connect()
        self._initialize_collection()

    def _connect(self) -> None:
        """Connect to Milvus server."""
        try:
            connections.connect(
                alias="default",
                host=self.settings.milvus_host,
                port=self.settings.milvus_port,
            )
            logger.info(
                f"Connected to Milvus at {self.settings.milvus_host}:{self.settings.milvus_port}"
            )
        except Exception as e:
            logger.error(f"Failed to connect to Milvus: {e}")
            raise

    def _initialize_collection(self) -> None:
        """Initialize or load the Milvus collection."""
        try:
            collection_name = self.settings.milvus_collection_name

            # Check if collection exists
            if utility.has_collection(collection_name):
                logger.info(f"Loading existing collection: {collection_name}")
                self.collection = Collection(collection_name)
            else:
                logger.info(f"Creating new collection: {collection_name}")
                self.collection = self._create_collection()

            # Load collection into memory
            if self.collection:
                self.collection.load()
            logger.info(f"Collection {collection_name} loaded successfully")

        except Exception as e:
            logger.error(f"Failed to initialize collection: {e}")
            raise

    def _create_collection(self) -> Collection:
        """Create a new Milvus collection with schema.

        Returns:
            Created collection instance
        """
        # Define schema fields
        fields = [
            FieldSchema(
                name="id",
                dtype=DataType.VARCHAR,
                is_primary=True,
                max_length=256,
                description="Unique document chunk ID",
            ),
            FieldSchema(
                name="text",
                dtype=DataType.VARCHAR,
                max_length=65535,
                description="Document text content",
            ),
            FieldSchema(
                name="vector",
                dtype=DataType.FLOAT_VECTOR,
                dim=self.settings.embedding_dimension,
                description="Embedding vector",
            ),
            FieldSchema(
                name="source",
                dtype=DataType.VARCHAR,
                max_length=512,
                description="Source document path",
            ),
            FieldSchema(
                name="timestamp",
                dtype=DataType.INT64,
                description="Unix timestamp of indexing",
            ),
        ]

        # Create schema
        schema = CollectionSchema(
            fields=fields,
            description="RAG knowledge base collection",
        )

        # Create collection
        collection = Collection(
            name=self.settings.milvus_collection_name,
            schema=schema,
        )

        # Create index for vector field
        index_params = {
            "metric_type": self.settings.milvus_metric_type,
            "index_type": "IVF_FLAT",
            "params": {"nlist": 1024},
        }

        collection.create_index(
            field_name="vector",
            index_params=index_params,
        )

        logger.info(f"Created collection with {self.settings.milvus_metric_type} metric")
        return collection

    def insert(
        self,
        ids: List[str],
        texts: List[str],
        vectors: List[List[float]],
        sources: List[str],
    ) -> None:
        """Insert documents into the collection.

        Args:
            ids: List of document IDs
            texts: List of text contents
            vectors: List of embedding vectors
            sources: List of source paths

        Raises:
            Exception: If insertion fails
        """
        try:
            if not self.collection:
                raise RuntimeError("Collection not initialized")

            # Prepare data
            timestamp = int(datetime.now().timestamp())
            timestamps = [timestamp] * len(ids)

            data = [
                ids,
                texts,
                vectors,
                sources,
                timestamps,
            ]

            # Insert data
            self.collection.insert(data)
            self.collection.flush()

            logger.info(f"Inserted {len(ids)} documents into collection")

        except Exception as e:
            logger.error(f"Failed to insert documents: {e}")
            raise

    def search(
        self,
        query_vector: List[float],
        top_k: Optional[int] = None,
        score_threshold: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Search for similar documents.

        Args:
            query_vector: Query embedding vector
            top_k: Number of top results to return
            score_threshold: Minimum similarity score threshold

        Returns:
            List of search results with metadata

        Raises:
            Exception: If search fails
        """
        try:
            if not self.collection:
                raise RuntimeError("Collection not initialized")

            top_k = top_k or self.settings.rag_top_k
            score_threshold = score_threshold or self.settings.rag_score_threshold

            # Define search parameters
            search_params = {
                "metric_type": self.settings.milvus_metric_type,
                "params": {"nprobe": 10},
            }

            # Perform search
            results = self.collection.search(
                data=[query_vector],
                anns_field="vector",
                param=search_params,
                limit=top_k,
                output_fields=["id", "text", "source", "timestamp"],
            )

            # Process results
            processed_results = []
            for hits in results:
                for hit in hits:
                    # Filter by score threshold
                    if hit.score >= score_threshold:
                        processed_results.append({
                            "id": hit.entity.get("id"),
                            "text": hit.entity.get("text"),
                            "source": hit.entity.get("source"),
                            "timestamp": hit.entity.get("timestamp"),
                            "score": hit.score,
                        })

            logger.info(f"Found {len(processed_results)} results above threshold")
            return processed_results

        except Exception as e:
            logger.error(f"Failed to search documents: {e}")
            raise

    def delete(self, ids: List[str]) -> None:
        """Delete documents by IDs.

        Args:
            ids: List of document IDs to delete

        Raises:
            Exception: If deletion fails
        """
        try:
            if not self.collection:
                raise RuntimeError("Collection not initialized")

            # Delete by IDs
            expr = f"id in {ids}"
            self.collection.delete(expr)
            self.collection.flush()

            logger.info(f"Deleted {len(ids)} documents from collection")

        except Exception as e:
            logger.error(f"Failed to delete documents: {e}")
            raise

    def get_stats(self) -> Dict[str, Any]:
        """Get collection statistics.

        Returns:
            Dictionary containing collection stats

        Raises:
            Exception: If stats retrieval fails
        """
        try:
            if not self.collection:
                raise RuntimeError("Collection not initialized")

            stats = self.collection.num_entities
            
            return {
                "collection_name": self.settings.milvus_collection_name,
                "num_entities": stats,
                "metric_type": self.settings.milvus_metric_type,
                "dimension": self.settings.embedding_dimension,
            }

        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            raise

    def clear_collection(self) -> None:
        """Clear all data from the collection.

        Raises:
            Exception: If clearing fails
        """
        try:
            if not self.collection:
                raise RuntimeError("Collection not initialized")

            # Drop and recreate collection
            self.collection.drop()
            logger.info(f"Dropped collection: {self.settings.milvus_collection_name}")

            # Recreate collection
            self.collection = self._create_collection()
            if self.collection:
                self.collection.load()
            logger.info("Collection recreated and loaded")

        except Exception as e:
            logger.error(f"Failed to clear collection: {e}")
            raise

    def health_check(self) -> bool:
        """Check if Milvus connection is healthy.

        Returns:
            True if healthy, False otherwise
        """
        try:
            if not self.collection:
                return False

            # Try to get collection stats
            _ = self.collection.num_entities
            return True

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    def disconnect(self) -> None:
        """Disconnect from Milvus server."""
        try:
            connections.disconnect("default")
            logger.info("Disconnected from Milvus")
        except Exception as e:
            logger.error(f"Failed to disconnect from Milvus: {e}")

# Made with Bob
