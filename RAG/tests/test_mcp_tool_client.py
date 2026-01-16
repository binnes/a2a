"""Unit tests for MCP Tool Client."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import httpx

from agent.tools import MCPToolClient
from config.settings import Settings


@pytest.fixture
def mock_settings():
    """Create mock settings."""
    settings = Mock(spec=Settings)
    settings.mcp_server_url = "http://localhost:8000"
    return settings


@pytest.fixture
def mock_httpx_client():
    """Create mock httpx client."""
    client = AsyncMock(spec=httpx.AsyncClient)
    return client


class TestMCPToolClientInitialization:
    """Test MCP tool client initialization."""

    def test_successful_initialization(self, mock_settings):
        """Test successful client initialization."""
        # Execute
        client = MCPToolClient(mock_settings)
        
        # Verify
        assert client.base_url == "http://localhost:8000"
        assert client.client is not None


class TestMCPToolClientRAGQuery:
    """Test RAG query tool."""

    @pytest.mark.asyncio
    async def test_rag_query_success(self, mock_settings):
        """Test successful RAG query."""
        # Setup
        client = MCPToolClient(mock_settings)
        
        mock_response = AsyncMock()
        mock_response.json = Mock(return_value={
            "answer": "Test answer",
            "context": ["context1", "context2"],
            "sources": [{"source": "test.txt", "score": 0.9}],
        })
        mock_response.raise_for_status = Mock()
        
        client.client.post = AsyncMock(return_value=mock_response)
        
        # Execute
        result = await client.rag_query("test query")
        
        # Verify
        assert result["answer"] == "Test answer"
        assert len(result["context"]) == 2
        assert len(result["sources"]) == 1
        client.client.post.assert_called_once_with(
            "http://localhost:8000/tools/rag_query",
            json={
                "query": "test query",
                "top_k": None,
                "include_sources": True,
            },
        )

    @pytest.mark.asyncio
    async def test_rag_query_with_params(self, mock_settings):
        """Test RAG query with custom parameters."""
        # Setup
        client = MCPToolClient(mock_settings)
        
        mock_response = AsyncMock()
        mock_response.json = Mock(return_value={"answer": "Test"})
        mock_response.raise_for_status = Mock()
        
        client.client.post = AsyncMock(return_value=mock_response)
        
        # Execute
        await client.rag_query("test", top_k=10, include_sources=False)
        
        # Verify
        client.client.post.assert_called_once_with(
            "http://localhost:8000/tools/rag_query",
            json={
                "query": "test",
                "top_k": 10,
                "include_sources": False,
            },
        )

    @pytest.mark.asyncio
    async def test_rag_query_failure(self, mock_settings):
        """Test RAG query handles failures."""
        # Setup
        client = MCPToolClient(mock_settings)
        client.client.post = AsyncMock(side_effect=httpx.HTTPError("Connection failed"))
        
        # Execute & Verify
        with pytest.raises(httpx.HTTPError):
            await client.rag_query("test")


class TestMCPToolClientRAGSearch:
    """Test RAG search tool."""

    @pytest.mark.asyncio
    async def test_rag_search_success(self, mock_settings):
        """Test successful RAG search."""
        # Setup
        client = MCPToolClient(mock_settings)
        
        mock_response = AsyncMock()
        mock_response.json = Mock(return_value={
            "query": "test",
            "results": [
                {"text": "result1", "score": 0.9},
                {"text": "result2", "score": 0.8},
            ],
            "count": 2,
        })
        mock_response.raise_for_status = Mock()
        
        client.client.post = AsyncMock(return_value=mock_response)
        
        # Execute
        result = await client.rag_search("test query")
        
        # Verify
        assert result["query"] == "test"
        assert result["count"] == 2
        assert len(result["results"]) == 2
        client.client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_rag_search_with_top_k(self, mock_settings):
        """Test RAG search with top_k parameter."""
        # Setup
        client = MCPToolClient(mock_settings)
        
        mock_response = AsyncMock()
        mock_response.json = Mock(return_value={"results": []})
        mock_response.raise_for_status = Mock()
        
        client.client.post = AsyncMock(return_value=mock_response)
        
        # Execute
        await client.rag_search("test", top_k=5)
        
        # Verify
        client.client.post.assert_called_once_with(
            "http://localhost:8000/tools/rag_search",
            json={"query": "test", "top_k": 5},
        )


class TestMCPToolClientRAGIndex:
    """Test RAG index tool."""

    @pytest.mark.asyncio
    async def test_rag_index_success(self, mock_settings):
        """Test successful document indexing."""
        # Setup
        client = MCPToolClient(mock_settings)
        
        mock_response = AsyncMock()
        mock_response.json = Mock(return_value={
            "status": "success",
            "message": "Document indexed successfully",
            "chunks_indexed": 100,
            "file_path": "test.txt",
        })
        mock_response.raise_for_status = Mock()
        
        client.client.post = AsyncMock(return_value=mock_response)
        
        # Execute
        result = await client.rag_index("test.txt")
        
        # Verify
        assert result["status"] == "success"
        assert result["chunks_indexed"] == 100
        client.client.post.assert_called_once_with(
            "http://localhost:8000/tools/rag_index",
            json={"file_path": "test.txt"},
        )

    @pytest.mark.asyncio
    async def test_rag_index_failure(self, mock_settings):
        """Test indexing handles failures."""
        # Setup
        client = MCPToolClient(mock_settings)
        client.client.post = AsyncMock(side_effect=httpx.HTTPError("File not found"))
        
        # Execute & Verify
        with pytest.raises(httpx.HTTPError):
            await client.rag_index("nonexistent.txt")


class TestMCPToolClientRAGStats:
    """Test RAG stats tool."""

    @pytest.mark.asyncio
    async def test_rag_stats_success(self, mock_settings):
        """Test successful stats retrieval."""
        # Setup
        client = MCPToolClient(mock_settings)
        
        mock_response = AsyncMock()
        mock_response.json = Mock(return_value={
            "status": "success",
            "statistics": {
                "collection_name": "test_collection",
                "num_entities": 1000,
                "metric_type": "COSINE",
                "dimension": 768,
            },
        })
        mock_response.raise_for_status = Mock()
        
        client.client.get = AsyncMock(return_value=mock_response)
        
        # Execute
        result = await client.rag_stats()
        
        # Verify
        assert result["status"] == "success"
        assert result["statistics"]["num_entities"] == 1000
        client.client.get.assert_called_once_with(
            "http://localhost:8000/tools/rag_stats"
        )

    @pytest.mark.asyncio
    async def test_rag_stats_failure(self, mock_settings):
        """Test stats retrieval handles failures."""
        # Setup
        client = MCPToolClient(mock_settings)
        client.client.get = AsyncMock(side_effect=httpx.HTTPError("Server error"))
        
        # Execute & Verify
        with pytest.raises(httpx.HTTPError):
            await client.rag_stats()


class TestMCPToolClientHealthCheck:
    """Test health check."""

    @pytest.mark.asyncio
    async def test_health_check_healthy(self, mock_settings):
        """Test health check when server is healthy."""
        # Setup
        client = MCPToolClient(mock_settings)
        
        mock_response = AsyncMock()
        mock_response.status_code = 200
        
        client.client.get = AsyncMock(return_value=mock_response)
        
        # Execute
        is_healthy = await client.health_check()
        
        # Verify
        assert is_healthy is True
        client.client.get.assert_called_once_with(
            "http://localhost:8000/health"
        )

    @pytest.mark.asyncio
    async def test_health_check_unhealthy(self, mock_settings):
        """Test health check when server is unhealthy."""
        # Setup
        client = MCPToolClient(mock_settings)
        
        mock_response = AsyncMock()
        mock_response.status_code = 500
        
        client.client.get = AsyncMock(return_value=mock_response)
        
        # Execute
        is_healthy = await client.health_check()
        
        # Verify
        assert is_healthy is False

    @pytest.mark.asyncio
    async def test_health_check_connection_error(self, mock_settings):
        """Test health check handles connection errors."""
        # Setup
        client = MCPToolClient(mock_settings)
        client.client.get = AsyncMock(side_effect=httpx.HTTPError("Connection refused"))
        
        # Execute
        is_healthy = await client.health_check()
        
        # Verify
        assert is_healthy is False


class TestMCPToolClientClose:
    """Test client cleanup."""

    @pytest.mark.asyncio
    async def test_close_client(self, mock_settings):
        """Test closing the HTTP client."""
        # Setup
        client = MCPToolClient(mock_settings)
        client.client.aclose = AsyncMock()
        
        # Execute
        await client.close()
        
        # Verify
        client.client.aclose.assert_called_once()


class TestMCPToolClientIntegration:
    """Integration tests for MCP tool client."""

    @pytest.mark.asyncio
    async def test_query_workflow(self, mock_settings):
        """Test complete query workflow."""
        # Setup
        client = MCPToolClient(mock_settings)
        
        # Mock health check
        health_response = AsyncMock()
        health_response.status_code = 200
        
        # Mock query response
        query_response = AsyncMock()
        query_response.json = Mock(return_value={
            "answer": "Romeo is a character",
            "context": ["Romeo and Juliet"],
        })
        query_response.raise_for_status = Mock()
        
        client.client.get = AsyncMock(return_value=health_response)
        client.client.post = AsyncMock(return_value=query_response)
        
        # Execute
        is_healthy = await client.health_check()
        assert is_healthy is True
        
        result = await client.rag_query("Who is Romeo?")
        assert "Romeo" in result["answer"]
        
        # Cleanup
        await client.close()


# Made with Bob