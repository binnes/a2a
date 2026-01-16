"""Agent tools for MCP integration."""

import logging
from typing import Dict, Any, Optional
import httpx  # type: ignore

from config.settings import Settings

logger = logging.getLogger(__name__)


class MCPToolClient:
    """Client for calling MCP RAG tools."""

    def __init__(self, settings: Settings):
        """Initialize MCP tool client.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.base_url = settings.mcp_server_url
        self.client = httpx.AsyncClient(timeout=30.0)

    async def rag_query(
        self,
        query: str,
        top_k: Optional[int] = None,
        include_sources: bool = True,
    ) -> Dict[str, Any]:
        """Call the rag_query MCP tool.

        Args:
            query: User query string
            top_k: Number of results to retrieve
            include_sources: Include source information

        Returns:
            Query response with answer and context

        Raises:
            Exception: If the tool call fails
        """
        try:
            response = await self.client.post(
                f"{self.base_url}/tools/rag_query",
                json={
                    "query": query,
                    "top_k": top_k,
                    "include_sources": include_sources,
                },
            )
            response.raise_for_status()
            return response.json()

        except Exception as e:
            logger.error(f"RAG query tool failed: {e}")
            raise

    async def rag_search(
        self,
        query: str,
        top_k: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Call the rag_search MCP tool.

        Args:
            query: Search query string
            top_k: Number of results to retrieve

        Returns:
            Search results

        Raises:
            Exception: If the tool call fails
        """
        try:
            response = await self.client.post(
                f"{self.base_url}/tools/rag_search",
                json={
                    "query": query,
                    "top_k": top_k,
                },
            )
            response.raise_for_status()
            return response.json()

        except Exception as e:
            logger.error(f"RAG search tool failed: {e}")
            raise

    async def rag_index(self, file_path: str) -> Dict[str, Any]:
        """Call the rag_index MCP tool.

        Args:
            file_path: Path to document file

        Returns:
            Indexing result

        Raises:
            Exception: If the tool call fails
        """
        try:
            response = await self.client.post(
                f"{self.base_url}/tools/rag_index",
                json={"file_path": file_path},
            )
            response.raise_for_status()
            return response.json()

        except Exception as e:
            logger.error(f"RAG index tool failed: {e}")
            raise

    async def rag_stats(self) -> Dict[str, Any]:
        """Call the rag_stats MCP tool.

        Returns:
            Knowledge base statistics

        Raises:
            Exception: If the tool call fails
        """
        try:
            response = await self.client.get(f"{self.base_url}/tools/rag_stats")
            response.raise_for_status()
            return response.json()

        except Exception as e:
            logger.error(f"RAG stats tool failed: {e}")
            raise

    async def health_check(self) -> bool:
        """Check if MCP server is healthy.

        Returns:
            True if healthy, False otherwise
        """
        try:
            response = await self.client.get(f"{self.base_url}/health")
            return response.status_code == 200

        except Exception as e:
            logger.error(f"MCP health check failed: {e}")
            return False

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

# Made with Bob
