"""A2A Agent FastAPI Server."""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException  # type: ignore
from fastapi.responses import JSONResponse  # type: ignore
from pydantic import BaseModel, Field  # type: ignore
import uvicorn  # type: ignore

from agent.a2a_agent import A2ARAGAgent
from agent.state import A2AMessage
from config.settings import Settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Request/Response Models
class A2AMessageRequest(BaseModel):
    """Request model for A2A messages."""
    agent_id: str = Field(..., description="Sender agent ID")
    message_type: str = Field(..., description="Message type")
    content: Dict[str, Any] = Field(..., description="Message content")
    correlation_id: Optional[str] = Field(None, description="Correlation ID")


class QueryRequest(BaseModel):
    """Request model for direct queries."""
    query: str = Field(..., description="User query string")


# Global agent instance
agent_instance: Optional[A2ARAGAgent] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan."""
    global agent_instance
    
    # Startup
    settings = Settings()
    agent_instance = A2ARAGAgent(settings)
    logger.info(f"A2A Agent {agent_instance.agent_id} started")
    
    yield
    
    # Shutdown
    if agent_instance:
        await agent_instance.close()
        logger.info("A2A Agent stopped")


# Create FastAPI app
app = FastAPI(
    title="A2A RAG Agent",
    description="Agent-to-Agent RAG service",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    if not agent_instance:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    health = await agent_instance.health_check()
    return JSONResponse(content=health)


@app.get("/capabilities")
async def get_capabilities():
    """Get agent capabilities."""
    if not agent_instance:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    return JSONResponse(content=agent_instance.get_capabilities())


@app.post("/a2a/message")
async def handle_message(request: A2AMessageRequest):
    """Handle incoming A2A message."""
    if not agent_instance:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        message: A2AMessage = {
            "agent_id": request.agent_id,
            "message_type": request.message_type,
            "content": request.content,
            "timestamp": datetime.utcnow().isoformat(),
            "correlation_id": request.correlation_id,
        }
        
        response = await agent_instance.handle_a2a_message(message)
        return JSONResponse(content=response)
    
    except Exception as e:
        logger.error(f"Error handling A2A message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query")
async def process_query(request: QueryRequest):
    """Process a direct query (non-A2A)."""
    if not agent_instance:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        result = await agent_instance.process_query(request.query)
        return JSONResponse(content=result)
    
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    """Run the A2A agent server when executed as a module."""
    settings = Settings()
    # A2A agent runs on port 8001 by default
    host = "0.0.0.0"
    port = 8001
    logger.info(f"Starting A2A Agent server on {host}:{port}")
    
    uvicorn.run(
        "agent.server:app",
        host=host,
        port=port,
        log_level="info",
    )

# Made with Bob