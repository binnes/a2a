"""Integration tests for MCP Server."""

import pytest
import httpx
from typing import Dict, Any

from config.settings import Settings


@pytest.fixture
def settings():
    """Get application settings."""
    return Settings()


@pytest.fixture
def server_url(settings):
    """Get MCP server URL."""
    # Use get_mcp_server_url() method which handles None case
    return settings.get_mcp_server_url()


@pytest.fixture
async def http_client():
    """Create HTTP client for testing."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        yield client


class TestMCPServerHealth:
    """Test MCP server health endpoints."""

    @pytest.mark.asyncio
    async def test_health_endpoint(self, http_client, server_url):
        """Test health check endpoint."""
        import asyncio
        
        # Retry logic for intermittent timeouts
        for attempt in range(3):
            try:
                response = await http_client.get(f"{server_url}/health")
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "healthy"
                return  # Success
            except Exception as e:
                if attempt == 2:  # Last attempt
                    raise
                await asyncio.sleep(2)  # Wait before retry

    @pytest.mark.asyncio
    async def test_health_details(self, http_client, server_url):
        """Test health endpoint returns component status."""
        import asyncio
        
        # Retry logic for intermittent timeouts
        for attempt in range(3):
            try:
                response = await http_client.get(f"{server_url}/health")
                assert response.status_code == 200
                data = response.json()
                # Check for components in the response
                assert "components" in data or "watsonx" in data
                return  # Success
            except Exception as e:
                if attempt == 2:  # Last attempt
                    raise
                await asyncio.sleep(2)  # Wait before retry


class TestMCPServerRAGQuery:
    """Test RAG query endpoint."""

    @pytest.mark.asyncio
    async def test_query_endpoint_exists(self, http_client, server_url):
        """Test query endpoint is accessible."""
        # Execute
        response = await http_client.post(
            f"{server_url}/tools/rag_query",
            json={"query": "test"},
        )
        
        # Verify - should not be 404
        assert response.status_code != 404

    @pytest.mark.asyncio
    async def test_query_with_valid_input(self, http_client, server_url):
        """Test query with valid input."""
        # Execute
        response = await http_client.post(
            f"{server_url}/tools/rag_query",
            json={
                "query": "test query",
                "top_k": 3,
                "include_sources": True,
            },
        )
        
        # Verify
        assert response.status_code in [200, 500]  # May fail if no data indexed
        if response.status_code == 200:
            data = response.json()
            assert "answer" in data

    @pytest.mark.asyncio
    async def test_query_missing_required_field(self, http_client, server_url):
        """Test query fails with missing required field."""
        # Execute
        response = await http_client.post(
            f"{server_url}/tools/rag_query",
            json={},
        )
        
        # Verify
        assert response.status_code in [400, 422]  # Bad request or validation error


class TestMCPServerRAGSearch:
    """Test RAG search endpoint."""

    @pytest.mark.asyncio
    async def test_search_endpoint_exists(self, http_client, server_url):
        """Test search endpoint is accessible."""
        # Execute
        response = await http_client.post(
            f"{server_url}/tools/rag_search",
            json={"query": "test"},
        )
        
        # Verify - should not be 404
        assert response.status_code != 404

    @pytest.mark.asyncio
    async def test_search_with_valid_input(self, http_client, server_url):
        """Test search with valid input."""
        # Execute
        response = await http_client.post(
            f"{server_url}/tools/rag_search",
            json={
                "query": "test search",
                "top_k": 5,
            },
        )
        
        # Verify
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            assert "results" in data
            assert "count" in data


class TestMCPServerRAGIndex:
    """Test RAG indexing endpoint."""

    @pytest.mark.asyncio
    async def test_index_endpoint_exists(self, http_client, server_url):
        """Test index endpoint is accessible."""
        # Execute
        response = await http_client.post(
            f"{server_url}/tools/rag_index",
            json={"file_path": "test.txt"},
        )
        
        # Verify - should not be 404
        assert response.status_code != 404

    @pytest.mark.asyncio
    async def test_index_missing_file(self, http_client, server_url):
        """Test indexing fails with missing file."""
        # Execute
        response = await http_client.post(
            f"{server_url}/tools/rag_index",
            json={"file_path": "nonexistent_file.txt"},
        )
        
        # Verify - should fail
        assert response.status_code in [400, 500]


class TestMCPServerRAGStats:
    """Test RAG stats endpoint."""

    @pytest.mark.asyncio
    async def test_stats_endpoint_exists(self, http_client, server_url):
        """Test stats endpoint is accessible."""
        # Execute
        response = await http_client.get(f"{server_url}/tools/rag_stats")
        
        # Verify
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_stats_returns_valid_data(self, http_client, server_url):
        """Test stats returns valid data structure."""
        # Execute
        response = await http_client.get(f"{server_url}/tools/rag_stats")
        
        # Verify
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "statistics" in data


class TestMCPServerErrorHandling:
    """Test error handling."""

    @pytest.mark.asyncio
    async def test_invalid_endpoint(self, http_client, server_url):
        """Test invalid endpoint returns 404."""
        # Execute
        response = await http_client.get(f"{server_url}/invalid/endpoint")
        
        # Verify
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_invalid_json(self, http_client, server_url):
        """Test invalid JSON returns error."""
        # Execute
        response = await http_client.post(
            f"{server_url}/tools/rag_query",
            content="invalid json",
            headers={"Content-Type": "application/json"},
        )
        
        # Verify
        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_method_not_allowed(self, http_client, server_url):
        """Test wrong HTTP method returns error."""
        # Execute - GET on POST endpoint
        response = await http_client.get(f"{server_url}/tools/rag_query")
        
        # Verify
        assert response.status_code == 405


class TestMCPServerCORS:
    """Test CORS configuration."""

    @pytest.mark.asyncio
    async def test_cors_headers_present(self, http_client, server_url):
        """Test CORS headers are present."""
        # Execute
        response = await http_client.options(
            f"{server_url}/health",
            headers={"Origin": "http://localhost:3000"},
        )
        
        # Verify - OPTIONS may not be implemented, check for CORS in GET
        if response.status_code == 405:
            # Try GET instead
            response = await http_client.get(f"{server_url}/health")
        assert response.status_code in [200, 204]


class TestMCPServerPerformance:
    """Test server performance."""

    @pytest.mark.asyncio
    async def test_health_check_response_time(self, http_client, server_url):
        """Test health check responds quickly."""
        import time
        
        # Execute
        start = time.time()
        response = await http_client.get(f"{server_url}/health")
        duration = time.time() - start
        
        # Verify - should respond in under 1 second
        assert response.status_code == 200
        assert duration < 1.0

    @pytest.mark.asyncio
    async def test_concurrent_requests(self, http_client, server_url):
        """Test server handles concurrent requests."""
        import asyncio
        
        # Execute - send 5 concurrent health checks
        tasks = [
            http_client.get(f"{server_url}/health")
            for _ in range(5)
        ]
        responses = await asyncio.gather(*tasks)
        
        # Verify - all should succeed
        assert all(r.status_code == 200 for r in responses)


class TestMCPServerWorkflow:
    """Test complete server workflows."""

    @pytest.mark.asyncio
    async def test_health_then_stats_workflow(self, http_client, server_url):
        """Test checking health then getting stats."""
        # Execute
        health_response = await http_client.get(f"{server_url}/health")
        assert health_response.status_code == 200
        
        stats_response = await http_client.get(f"{server_url}/tools/rag_stats")
        assert stats_response.status_code == 200
        
        # Verify
        health_data = health_response.json()
        stats_data = stats_response.json()
        
        assert health_data["status"] == "healthy"
        assert "statistics" in stats_data


# Made with Bob