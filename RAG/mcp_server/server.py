"""MCP server implementation for RAG operations."""

import logging
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status  # type: ignore
from fastapi.responses import JSONResponse  # type: ignore
from pydantic import BaseModel, Field  # type: ignore

from config.settings import get_settings
from mcp_server.rag_tools import RAGTools

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Request/Response Models
class QueryRequest(BaseModel):
    """Request model for RAG query."""

    query: str = Field(..., description="User query string")
    top_k: Optional[int] = Field(None, description="Number of results to retrieve")
    include_sources: bool = Field(True, description="Include source information")


class QueryResponse(BaseModel):
    """Response model for RAG query."""

    answer: str = Field(..., description="Generated answer")
    context: list[str] = Field(..., description="Retrieved context chunks")
    sources: Optional[list[Dict[str, Any]]] = Field(None, description="Source information")


class IndexDocumentRequest(BaseModel):
    """Request model for document indexing."""

    file_path: str = Field(..., description="Path to document file")


class IndexDirectoryRequest(BaseModel):
    """Request model for directory indexing."""

    directory_path: str = Field(..., description="Path to directory")
    recursive: bool = Field(True, description="Process subdirectories")


class SearchRequest(BaseModel):
    """Request model for semantic search."""

    query: str = Field(..., description="Search query string")
    top_k: Optional[int] = Field(None, description="Number of results to retrieve")


class HealthResponse(BaseModel):
    """Response model for health check."""

    status: str = Field(..., description="Overall health status")
    components: Dict[str, bool] = Field(..., description="Component health status")


# Global RAG tools instance
rag_tools: Optional[RAGTools] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI app."""
    global rag_tools
    
    # Startup
    logger.info("Starting MCP server...")
    settings = get_settings()
    rag_tools = RAGTools(settings)
    logger.info("MCP server started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down MCP server...")
    if rag_tools and rag_tools.milvus:
        rag_tools.milvus.disconnect()
    logger.info("MCP server shut down")


# Create FastAPI app
app = FastAPI(
    title="MCP RAG Server",
    description="Model Context Protocol server for RAG operations",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "MCP RAG Server",
        "version": "0.1.0",
        "description": "Model Context Protocol server for RAG operations",
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    try:
        if not rag_tools:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="RAG tools not initialized",
            )

        component_health = rag_tools.health_check()
        all_healthy = all(component_health.values())

        return HealthResponse(
            status="healthy" if all_healthy else "degraded",
            components=component_health,
        )

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )


@app.post("/tools/rag_query", response_model=QueryResponse)
async def rag_query(request: QueryRequest):
    """Query the RAG knowledge base.

    This tool retrieves relevant context from the knowledge base and generates
    an answer using the LLM.
    """
    try:
        if not rag_tools:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="RAG tools not initialized",
            )

        result = await rag_tools.query(
            query=request.query,
            top_k=request.top_k,
            include_sources=request.include_sources,
        )

        return QueryResponse(**result)

    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@app.post("/tools/rag_index")
async def rag_index_document(request: IndexDocumentRequest):
    """Index a document into the knowledge base.

    This tool processes a document, generates embeddings, and stores them
    in the vector database.
    """
    try:
        if not rag_tools:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="RAG tools not initialized",
            )

        result = await rag_tools.index_document(request.file_path)
        return JSONResponse(content=result)

    except Exception as e:
        logger.error(f"Indexing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@app.post("/tools/rag_index_directory")
async def rag_index_directory(request: IndexDirectoryRequest):
    """Index all documents in a directory.

    This tool processes all supported documents in a directory and indexes them
    into the knowledge base.
    """
    try:
        if not rag_tools:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="RAG tools not initialized",
            )

        result = await rag_tools.index_directory(
            directory_path=request.directory_path,
            recursive=request.recursive,
        )
        return JSONResponse(content=result)

    except Exception as e:
        logger.error(f"Directory indexing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@app.post("/tools/rag_search")
async def rag_search(request: SearchRequest):
    """Semantic search in the knowledge base.

    This tool performs semantic search without LLM generation, returning
    the most relevant document chunks.
    """
    try:
        if not rag_tools:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="RAG tools not initialized",
            )

        result = await rag_tools.search(
            query=request.query,
            top_k=request.top_k,
        )
        return JSONResponse(content=result)

    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@app.get("/tools/rag_stats")
async def rag_stats():
    """Get knowledge base statistics.

    Returns statistics about the indexed documents and collection.
    """
    try:
        if not rag_tools:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="RAG tools not initialized",
            )

        result = await rag_tools.get_stats()
        return JSONResponse(content=result)

    except Exception as e:
        logger.error(f"Stats retrieval failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@app.delete("/tools/rag_clear")
async def rag_clear():
    """Clear the knowledge base.

    WARNING: This will delete all indexed documents from the knowledge base.
    """
    try:
        if not rag_tools:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="RAG tools not initialized",
            )

        result = await rag_tools.clear_knowledge_base()
        return JSONResponse(content=result)

    except Exception as e:
        logger.error(f"Clear operation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@app.get("/tools")
async def list_tools():
    """List available MCP tools.

    Returns a list of all available RAG tools with their descriptions.
    """
    return {
        "tools": [
            {
                "name": "rag_query",
                "description": "Query the RAG knowledge base with LLM generation",
                "endpoint": "/tools/rag_query",
                "method": "POST",
            },
            {
                "name": "rag_index",
                "description": "Index a single document into the knowledge base",
                "endpoint": "/tools/rag_index",
                "method": "POST",
            },
            {
                "name": "rag_index_directory",
                "description": "Index all documents in a directory",
                "endpoint": "/tools/rag_index_directory",
                "method": "POST",
            },
            {
                "name": "rag_search",
                "description": "Semantic search without LLM generation",
                "endpoint": "/tools/rag_search",
                "method": "POST",
            },
            {
                "name": "rag_stats",
                "description": "Get knowledge base statistics",
                "endpoint": "/tools/rag_stats",
                "method": "GET",
            },
            {
                "name": "rag_clear",
                "description": "Clear all data from the knowledge base",
                "endpoint": "/tools/rag_clear",
                "method": "DELETE",
            },
        ]
    }


class MCPServer:
    """MCP Server wrapper class."""

    def __init__(self, settings=None):
        """Initialize MCP server.

        Args:
            settings: Optional settings override
        """
        self.app = app
        self.settings = settings or get_settings()

    def run(self, host: Optional[str] = None, port: Optional[int] = None, reload: Optional[bool] = None):
        """Run the MCP server.

        Args:
            host: Server host (default from settings)
            port: Server port (default from settings)
            reload: Enable auto-reload (default from settings)
        """
        import uvicorn  # type: ignore

        host = host or self.settings.mcp_server_host
        port = port or self.settings.mcp_server_port
        reload = reload if reload is not None else self.settings.mcp_server_reload

        logger.info(f"Starting MCP server on {host}:{port}")
        uvicorn.run(
            "mcp_server.server:app",
            host=host,
            port=port,
            reload=reload,
        )

# Made with Bob
