"""Configuration management for A2A RAG Agent."""

from typing import Optional
from pydantic import Field  # type: ignore
from pydantic_settings import BaseSettings, SettingsConfigDict  # type: ignore


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file="config/.env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Watsonx.ai Configuration
    watsonx_api_key: str = Field(..., description="Watsonx.ai API key")
    watsonx_project_id: str = Field(..., description="Watsonx.ai project ID")
    watsonx_url: str = Field(
        default="https://us-south.ml.cloud.ibm.com",
        description="Watsonx.ai API endpoint",
    )

    # Embedding Model Configuration
    embedding_model: str = Field(
        default="ibm/granite-embedding-278m-multilingual",
        description="Embedding model name",
    )
    embedding_dimension: int = Field(
        default=768,
        description="Embedding vector dimension",
    )

    # LLM Configuration
    llm_model: str = Field(
        default="ibm/granite-13b-chat-v2",
        description="LLM model name",
    )
    llm_max_tokens: int = Field(
        default=2048,
        description="Maximum tokens for LLM generation",
    )
    llm_temperature: float = Field(
        default=0.7,
        description="Temperature for LLM generation",
    )

    # Milvus Configuration
    milvus_host: str = Field(default="localhost", description="Milvus host")
    milvus_port: int = Field(default=19530, description="Milvus port")
    milvus_collection_name: str = Field(
        default="rag_knowledge_base",
        description="Milvus collection name",
    )
    milvus_metric_type: str = Field(
        default="COSINE",
        description="Similarity metric type",
    )

    # MCP Server Configuration
    mcp_server_host: str = Field(default="0.0.0.0", description="MCP server host")
    mcp_server_port: int = Field(default=8000, description="MCP server port")
    mcp_server_url: Optional[str] = Field(default=None, description="MCP server URL (overrides host/port)")
    mcp_server_reload: bool = Field(default=False, description="Enable auto-reload")

    # A2A Agent Configuration
    a2a_agent_id: str = Field(default="rag-agent", description="A2A agent ID")
    a2a_agent_name: str = Field(
        default="RAG Knowledge Agent",
        description="A2A agent name",
    )
    a2a_agent_description: str = Field(
        default="Agent for querying RAG knowledge base using MCP tools",
        description="A2A agent description",
    )

    # RAG Configuration
    rag_chunk_size: int = Field(default=80, description="Document chunk size in words")
    rag_chunk_overlap: int = Field(default=10, description="Chunk overlap size in words")
    rag_top_k: int = Field(default=5, description="Number of top results to retrieve")
    rag_score_threshold: float = Field(
        default=0.7,
        description="Minimum similarity score threshold",
    )

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Log format (json or text)")

    @property
    def milvus_uri(self) -> str:
        """Get Milvus connection URI."""
        return f"http://{self.milvus_host}:{self.milvus_port}"

    def get_mcp_server_url(self) -> str:
        """Get MCP server URL."""
        if self.mcp_server_url:
            return self.mcp_server_url
        return f"http://{self.mcp_server_host}:{self.mcp_server_port}"


# Global settings instance
settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create settings instance."""
    global settings
    if settings is None:
        settings = Settings()
    return settings

# Made with Bob
