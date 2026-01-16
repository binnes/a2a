"""RAG tools for MCP server."""

import logging
from typing import List, Dict, Any, Optional

from services.watsonx_client import WatsonxClient
from services.milvus_client import MilvusClient
from services.document_processor import DocumentProcessor
from config.settings import Settings

logger = logging.getLogger(__name__)


class RAGTools:
    """RAG operations tools for MCP server."""

    def __init__(self, settings: Settings):
        """Initialize RAG tools.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.watsonx = WatsonxClient(settings)
        self.milvus = MilvusClient(settings)
        self.processor = DocumentProcessor(settings)

    async def query(
        self,
        query: str,
        top_k: Optional[int] = None,
        include_sources: bool = True,
    ) -> Dict[str, Any]:
        """Query the RAG knowledge base.

        Args:
            query: User query string
            top_k: Number of top results to retrieve
            include_sources: Whether to include source information

        Returns:
            Dictionary containing answer and context

        Raises:
            Exception: If query fails
        """
        try:
            logger.info(f"Processing query: {query}")

            # Generate query embedding
            query_embedding = self.watsonx.generate_embedding(query)

            # Search for relevant documents
            search_results = self.milvus.search(
                query_vector=query_embedding,
                top_k=top_k,
            )

            if not search_results:
                return {
                    "answer": "I couldn't find any relevant information to answer your query.",
                    "context": [],
                    "sources": [],
                }

            # Prepare context from search results
            context_texts = [result["text"] for result in search_results]
            context = "\n\n".join(context_texts)

            # Generate answer using LLM
            prompt = self._build_rag_prompt(query, context)
            answer = self.watsonx.generate_text(prompt)

            # Prepare response
            response = {
                "answer": answer,
                "context": context_texts,
            }

            if include_sources:
                sources = [
                    {
                        "source": result["source"],
                        "score": result["score"],
                        "chunk_id": result["id"],
                    }
                    for result in search_results
                ]
                response["sources"] = sources

            logger.info(f"Query processed successfully with {len(search_results)} results")
            return response

        except Exception as e:
            logger.error(f"Failed to process query: {e}")
            raise

    async def index_document(self, file_path: str) -> Dict[str, Any]:
        """Index a single document into the knowledge base.

        Args:
            file_path: Path to the document file

        Returns:
            Dictionary containing indexing results

        Raises:
            Exception: If indexing fails
        """
        try:
            logger.info(f"Indexing document: {file_path}")

            # Process document into chunks
            chunks = self.processor.process_file(file_path)

            if not chunks:
                return {
                    "status": "error",
                    "message": "No content extracted from document",
                    "chunks_indexed": 0,
                }

            # Generate embeddings for all chunks
            texts = [chunk["text"] for chunk in chunks]
            embeddings = self.watsonx.generate_embeddings(texts)

            # Prepare data for insertion
            ids = [chunk["id"] for chunk in chunks]
            sources = [chunk["source"] for chunk in chunks]

            # Insert into Milvus
            self.milvus.insert(
                ids=ids,
                texts=texts,
                vectors=embeddings,
                sources=sources,
            )

            logger.info(f"Successfully indexed {len(chunks)} chunks from {file_path}")

            return {
                "status": "success",
                "message": f"Document indexed successfully",
                "chunks_indexed": len(chunks),
                "file_path": file_path,
            }

        except Exception as e:
            logger.error(f"Failed to index document: {e}")
            raise

    async def index_directory(
        self,
        directory_path: str,
        recursive: bool = True,
    ) -> Dict[str, Any]:
        """Index all documents in a directory.

        Args:
            directory_path: Path to the directory
            recursive: Whether to process subdirectories

        Returns:
            Dictionary containing indexing results

        Raises:
            Exception: If indexing fails
        """
        try:
            logger.info(f"Indexing directory: {directory_path}")

            # Process all documents in directory
            all_chunks = self.processor.process_directory(
                directory_path,
                recursive=recursive,
            )

            if not all_chunks:
                return {
                    "status": "error",
                    "message": "No documents found or processed",
                    "chunks_indexed": 0,
                }

            # Generate embeddings for all chunks
            texts = [chunk["text"] for chunk in all_chunks]
            embeddings = self.watsonx.generate_embeddings(texts)

            # Prepare data for insertion
            ids = [chunk["id"] for chunk in all_chunks]
            sources = [chunk["source"] for chunk in all_chunks]

            # Insert into Milvus
            self.milvus.insert(
                ids=ids,
                texts=texts,
                vectors=embeddings,
                sources=sources,
            )

            logger.info(f"Successfully indexed {len(all_chunks)} chunks from directory")

            return {
                "status": "success",
                "message": f"Directory indexed successfully",
                "chunks_indexed": len(all_chunks),
                "directory_path": directory_path,
            }

        except Exception as e:
            logger.error(f"Failed to index directory: {e}")
            raise

    async def search(
        self,
        query: str,
        top_k: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Semantic search without LLM generation.

        Args:
            query: Search query string
            top_k: Number of top results to retrieve

        Returns:
            Dictionary containing search results

        Raises:
            Exception: If search fails
        """
        try:
            logger.info(f"Searching for: {query}")

            # Generate query embedding
            query_embedding = self.watsonx.generate_embedding(query)

            # Search for relevant documents
            search_results = self.milvus.search(
                query_vector=query_embedding,
                top_k=top_k,
            )

            logger.info(f"Found {len(search_results)} results")

            return {
                "query": query,
                "results": search_results,
                "count": len(search_results),
            }

        except Exception as e:
            logger.error(f"Failed to search: {e}")
            raise

    async def get_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics.

        Returns:
            Dictionary containing statistics

        Raises:
            Exception: If stats retrieval fails
        """
        try:
            stats = self.milvus.get_stats()
            
            return {
                "status": "success",
                "statistics": stats,
            }

        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            raise

    async def clear_knowledge_base(self) -> Dict[str, Any]:
        """Clear all data from the knowledge base.

        Returns:
            Dictionary containing operation result

        Raises:
            Exception: If clearing fails
        """
        try:
            logger.warning("Clearing knowledge base")
            
            self.milvus.clear_collection()
            
            return {
                "status": "success",
                "message": "Knowledge base cleared successfully",
            }

        except Exception as e:
            logger.error(f"Failed to clear knowledge base: {e}")
            raise

    def _build_rag_prompt(self, query: str, context: str) -> str:
        """Build RAG prompt for LLM.

        Args:
            query: User query
            context: Retrieved context

        Returns:
            Formatted prompt string
        """
        prompt = f"""You are a helpful AI assistant. Use the following context to answer the user's question. If the context doesn't contain relevant information, say so.

Context:
{context}

Question: {query}

Answer:"""
        return prompt

    def health_check(self) -> Dict[str, bool]:
        """Check health of all components.

        Returns:
            Dictionary with health status of each component
        """
        return {
            "watsonx": self.watsonx.health_check(),
            "milvus": self.milvus.health_check(),
        }

# Made with Bob
