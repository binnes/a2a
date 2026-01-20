# Quick Start Guide

Get the A2A RAG Agent up and running in minutes.

## Prerequisites

- Python 3.11-3.13 (required for Watsonx.ai 1.5.0)
- Podman or Docker
- IBM Watsonx.ai account with API key and project ID

## Installation

### 1. Clone and Navigate

```bash
cd RAG
```

### 2. Run Setup Script

```bash
./deployment/setup.sh
```

This script will:
- Check Python and Podman installation
- Create a virtual environment
- Install dependencies
- Start Milvus with Podman
- Create necessary directories

### 3. Configure Credentials

Edit `config/.env`:

```bash
# Watsonx.ai Configuration
WATSONX_API_KEY=your-api-key-here
WATSONX_PROJECT_ID=your-project-id-here
WATSONX_URL=https://us-south.ml.cloud.ibm.com

# Embedding Model (768 dimensions)
EMBEDDING_MODEL=ibm/granite-embedding-278m-multilingual
EMBEDDING_DIMENSION=768

# LLM Model
LLM_MODEL=openai/gpt-oss-120b
LLM_MAX_TOKENS=16384

# Chunking Configuration
RAG_CHUNK_SIZE=80  # words
RAG_CHUNK_OVERLAP=10  # words
```

## Starting Services

### Option 1: Using the Start Script (Recommended)

```bash
cd RAG
./scripts/start_services.sh
```

This will:
1. Start Milvus vector database
2. Start MCP server on port 8000
3. Verify all services are healthy

### Option 2: Manual Start

```bash
# Terminal 1: Start Milvus
cd RAG/deployment
podman-compose up -d

# Terminal 2: Start MCP Server
cd RAG
source venv/bin/activate
python -m uvicorn mcp_server.server:app --host 0.0.0.0 --port 8000
```

## Verify Installation

### Check Service Health

```bash
# Check MCP server
curl http://localhost:8000/health

# Expected response:
# {
#   "status": "healthy",
#   "components": {
#     "watsonx": true,
#     "milvus": true
#   }
# }
```

### List Available Tools

```bash
curl http://localhost:8000/tools
```

## Index Your First Document

### 1. Add Documents

Place your documents in `data/documents/`:

```bash
cp your-document.pdf RAG/data/documents/
```

Supported formats: PDF, DOCX, TXT, Markdown

### 2. Index the Document

```bash
curl -X POST http://localhost:8000/tools/rag_index \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "data/documents/your-document.pdf"
  }'
```

Or index an entire directory:

```bash
curl -X POST http://localhost:8000/tools/rag_index_directory \
  -H "Content-Type: application/json" \
  -d '{
    "directory_path": "data/documents",
    "recursive": true
  }'
```

### 3. Verify Indexing

```bash
curl http://localhost:8000/tools/rag_stats
```

Expected response:
```json
{
  "status": "success",
  "statistics": {
    "collection_name": "rag_knowledge_base",
    "num_entities": 156,
    "metric_type": "COSINE",
    "dimension": 768
  }
}
```

## Query the Knowledge Base

### Simple Query

```bash
curl -X POST http://localhost:8000/tools/rag_query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the A2A protocol?",
    "top_k": 5,
    "include_sources": true
  }'
```

### Using Python

```python
import httpx
import asyncio

async def query_rag(query: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/tools/rag_query",
            json={
                "query": query,
                "top_k": 5,
                "include_sources": True
            }
        )
        return response.json()

# Usage
result = asyncio.run(query_rag("What is the A2A protocol?"))
print(result["answer"])
```

### Using the A2A Agent

```python
from agent.a2a_agent import A2ARAGAgent
from config.settings import get_settings

async def main():
    settings = get_settings()
    agent = A2ARAGAgent(settings)
    
    # Process query
    result = await agent.process_query("What is the A2A protocol?")
    print(result["response"])
    
    # Cleanup
    await agent.close()

asyncio.run(main())
```

## Running Tests

### Quick Test (Core Tests)

```bash
cd RAG
./scripts/run_tests.sh
```

### Comprehensive Tests

```bash
cd RAG
source venv/bin/activate
python -m pytest tests/ -v
```

### Test Specific Components

```bash
# A2A and MCP integration tests
python -m pytest tests/ -v -k "a2a or mcp"

# Document processor tests
python -m pytest tests/test_document_processor.py -v

# End-to-end tests
python -m pytest tests/test_e2e_shakespeare.py -v
```

## Stopping Services

```bash
cd RAG
./scripts/stop_services.sh
```

Or manually:

```bash
# Stop MCP server (Ctrl+C in the terminal)

# Stop Milvus
cd RAG/deployment
podman-compose down
```

## Next Steps

- [API Reference](api-reference.md) - Detailed API documentation
- [Configuration Guide](configuration.md) - Advanced configuration options
- [Testing Guide](testing.md) - Comprehensive testing information
- [Troubleshooting](troubleshooting.md) - Common issues and solutions

## Example Workflows

### Workflow 1: Technical Documentation

```bash
# 1. Index documentation
curl -X POST http://localhost:8000/tools/rag_index_directory \
  -H "Content-Type: application/json" \
  -d '{"directory_path": "data/documents/tech-docs"}'

# 2. Query
curl -X POST http://localhost:8000/tools/rag_query \
  -H "Content-Type: application/json" \
  -d '{"query": "How do I configure the API?"}'
```

### Workflow 2: Research Papers

```bash
# 1. Index papers
curl -X POST http://localhost:8000/tools/rag_index_directory \
  -H "Content-Type: application/json" \
  -d '{"directory_path": "data/documents/papers"}'

# 2. Search for related content
curl -X POST http://localhost:8000/tools/rag_search \
  -H "Content-Type: application/json" \
  -d '{"query": "machine learning optimization", "top_k": 10}'
```

## Tips for Success

1. **Chunk Size**: Adjust `RAG_CHUNK_SIZE` based on your content
   - Technical docs: 200-300 tokens
   - Narrative content: 400-500 tokens

2. **Top-K**: Balance between precision and recall
   - Focused queries: 3-5 results
   - Exploratory queries: 10-20 results

3. **Score Threshold**: Filter irrelevant results
   - High precision: 0.8-0.9
   - High recall: 0.6-0.7

4. **Model Selection**: Choose appropriate models
   - Embeddings: Match dimension to your needs
   - LLM: Balance between speed and quality