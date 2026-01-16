# A2A RAG Agent

An Agent-to-Agent (A2A) based Retrieval-Augmented Generation (RAG) agent that provides intelligent query services over a knowledge base using Model Context Protocol (MCP) tools.

## Overview

This project implements a complete RAG system with:

- **A2A Agent**: LangGraph-based agent for orchestrating RAG workflows
- **MCP Server**: FastAPI server exposing RAG operations as MCP tools
- **Watsonx.ai Integration**: IBM's AI platform for embeddings and LLM services
- **Milvus Vector Store**: High-performance vector database for semantic search
- **Podman Deployment**: Containerized Milvus for local development

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      A2A RAG Agent                          │
│                   (LangGraph Workflow)                      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    MCP Server (FastAPI)                     │
│  Tools: rag_query, rag_search, rag_index, rag_stats        │
└────────────┬───────────────────────────┬────────────────────┘
             │                           │
             ▼                           ▼
┌────────────────────────┐   ┌──────────────────────────────┐
│   Watsonx.ai Services  │   │   Milvus Vector Database     │
│  - Embeddings (Slate)  │   │  - COSINE similarity         │
│  - LLM (Granite)       │   │  - 384-dim vectors           │
└────────────────────────┘   └──────────────────────────────┘
```

## Features

### A2A Agent
- LangGraph-based state machine for workflow orchestration
- Asynchronous processing with error handling
- A2A protocol message handling
- Conversation history management

### MCP Server
- RESTful API for RAG operations
- Health check and monitoring endpoints
- Request/response validation with Pydantic
- Comprehensive error handling

### RAG Pipeline
- Document processing (PDF, DOCX, TXT, MD)
- Intelligent text chunking with overlap
- Semantic search with configurable thresholds
- Context-aware response generation

### Vector Store
- Milvus standalone deployment
- COSINE similarity metric
- Efficient indexing (IVF_FLAT)
- Metadata storage and filtering

## Prerequisites

- Python 3.10 or higher
- Podman or Docker
- IBM Watsonx.ai account with API key and project ID

## Quick Start

### 1. Clone and Setup

```bash
cd RAG
./deployment/setup.sh
```

This script will:
- Check Python and Podman installation
- Create a virtual environment
- Install dependencies
- Start Milvus with Podman
- Create necessary directories

### 2. Configure Credentials

Edit `config/.env` with your Watsonx.ai credentials:

```bash
WATSONX_API_KEY=your-api-key-here
WATSONX_PROJECT_ID=your-project-id-here
WATSONX_URL=https://us-south.ml.cloud.ibm.com
```

### 3. Start MCP Server

```bash
source venv/bin/activate
python -m uvicorn mcp_server.server:app --host 0.0.0.0 --port 8000
```

The MCP server will be available at `http://localhost:8000`

### 4. Index Documents

Add your documents to `data/documents/` and index them:

```bash
curl -X POST http://localhost:8000/tools/rag_index_directory \
  -H "Content-Type: application/json" \
  -d '{"directory_path": "data/documents", "recursive": true}'
```

### 5. Query the Knowledge Base

```bash
curl -X POST http://localhost:8000/tools/rag_query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the A2A protocol?", "top_k": 5}'
```

### 6. Run Sample Queries

```bash
python data/examples/sample_query.py
```

## Project Structure

```
RAG/
├── agent/                      # A2A agent implementation
│   ├── __init__.py
│   ├── a2a_agent.py           # Main agent with LangGraph
│   ├── state.py               # Agent state definitions
│   └── tools.py               # MCP tool client
├── mcp_server/                # MCP server implementation
│   ├── __init__.py
│   ├── server.py              # FastAPI server
│   └── rag_tools.py           # RAG tool implementations
├── services/                  # Core services
│   ├── __init__.py
│   ├── watsonx_client.py      # Watsonx.ai integration
│   ├── milvus_client.py       # Milvus vector store
│   └── document_processor.py  # Document processing
├── config/                    # Configuration
│   ├── __init__.py
│   ├── settings.py            # Settings management
│   └── .env.example           # Environment template
├── deployment/                # Deployment files
│   ├── podman-compose.yml     # Milvus deployment
│   └── setup.sh               # Setup script
├── data/                      # Data directory
│   ├── documents/             # Documents to index
│   └── examples/              # Example scripts
├── tests/                     # Test suite
├── requirements.txt           # Python dependencies
├── pyproject.toml            # Project metadata
└── README.md                 # This file
```

## API Reference

### MCP Server Endpoints

#### Health Check
```
GET /health
```

Returns health status of all components.

#### List Tools
```
GET /tools
```

Lists all available MCP tools.

#### RAG Query
```
POST /tools/rag_query
{
  "query": "string",
  "top_k": 5,
  "include_sources": true
}
```

Query the knowledge base with LLM generation.

#### RAG Search
```
POST /tools/rag_search
{
  "query": "string",
  "top_k": 5
}
```

Semantic search without LLM generation.

#### Index Document
```
POST /tools/rag_index
{
  "file_path": "path/to/document.pdf"
}
```

Index a single document.

#### Index Directory
```
POST /tools/rag_index_directory
{
  "directory_path": "path/to/directory",
  "recursive": true
}
```

Index all documents in a directory.

#### Get Statistics
```
GET /tools/rag_stats
```

Get knowledge base statistics.

#### Clear Knowledge Base
```
DELETE /tools/rag_clear
```

Clear all indexed documents (use with caution).

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `WATSONX_API_KEY` | Watsonx.ai API key | Required |
| `WATSONX_PROJECT_ID` | Watsonx.ai project ID | Required |
| `WATSONX_URL` | Watsonx.ai endpoint | `https://us-south.ml.cloud.ibm.com` |
| `EMBEDDING_MODEL` | Embedding model name | `ibm/slate-125m-english-rtrvr` |
| `EMBEDDING_DIMENSION` | Embedding vector dimension | `384` |
| `LLM_MODEL` | LLM model name | `ibm/granite-13b-chat-v2` |
| `MILVUS_HOST` | Milvus host | `localhost` |
| `MILVUS_PORT` | Milvus port | `19530` |
| `MCP_SERVER_PORT` | MCP server port | `8000` |
| `RAG_CHUNK_SIZE` | Document chunk size | `512` |
| `RAG_CHUNK_OVERLAP` | Chunk overlap size | `50` |
| `RAG_TOP_K` | Number of results | `5` |
| `RAG_SCORE_THRESHOLD` | Similarity threshold | `0.7` |

### Supported File Formats

- PDF (`.pdf`)
- Word Documents (`.docx`)
- Text Files (`.txt`)
- Markdown (`.md`)

## Development

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black .
ruff check .
```

### Starting Milvus

```bash
cd deployment
podman-compose up -d
```

### Stopping Milvus

```bash
cd deployment
podman-compose down
```

### Viewing Logs

```bash
cd deployment
podman-compose logs -f milvus
```

## Troubleshooting

### Milvus Connection Issues

1. Check if Milvus is running:
   ```bash
   podman ps | grep milvus
   ```

2. Check Milvus logs:
   ```bash
   cd deployment && podman-compose logs milvus
   ```

3. Restart Milvus:
   ```bash
   cd deployment && podman-compose restart
   ```

### Watsonx.ai Authentication Errors

1. Verify your API key and project ID in `config/.env`
2. Check API key permissions in Watsonx.ai console
3. Ensure the Watsonx.ai URL is correct for your region

### Import Errors

Make sure you're in the virtual environment:
```bash
source venv/bin/activate
```

## Performance Tuning

### Chunk Size
- Smaller chunks (256-512): Better precision, more results
- Larger chunks (1024-2048): Better context, fewer results

### Top K
- Lower values (3-5): Faster, more focused
- Higher values (10-20): More comprehensive, slower

### Similarity Threshold
- Higher threshold (0.8-0.9): More precise, fewer results
- Lower threshold (0.5-0.7): More results, less precise

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

Apache 2.0

## Support

For issues and questions:
- GitHub Issues: [Project Issues](https://github.com/ibm/a2a-rag-agent/issues)
- Documentation: [Project Docs](https://github.com/ibm/a2a-rag-agent/docs)

## Acknowledgments

- IBM Watsonx.ai team
- Milvus community
- LangChain and LangGraph projects
- A2A protocol contributors