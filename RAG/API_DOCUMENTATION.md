# MCP Server API Documentation

## Overview

The MCP (Model Context Protocol) Server provides RESTful API endpoints for RAG (Retrieval-Augmented Generation) operations. This document describes all available endpoints, request/response formats, and usage examples.

## Base URL

```
http://localhost:8000
```

## Authentication

Currently, the API does not require authentication. In production, implement appropriate authentication mechanisms.

## Endpoints

### 1. Root Endpoint

Get server information.

**Endpoint:** `GET /`

**Response:**
```json
{
  "name": "MCP RAG Server",
  "version": "0.1.0",
  "description": "Model Context Protocol server for RAG operations"
}
```

**Example:**
```bash
curl http://localhost:8000/
```

---

### 2. Health Check

Check the health status of the server and its dependencies.

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "components": {
    "watsonx": true,
    "milvus": true
  }
}
```

**Status Codes:**
- `200 OK`: All components healthy
- `503 Service Unavailable`: One or more components unhealthy

**Example:**
```bash
curl http://localhost:8000/health
```

---

### 3. List Tools

Get a list of all available MCP tools.

**Endpoint:** `GET /tools`

**Response:**
```json
{
  "tools": [
    {
      "name": "rag_query",
      "description": "Query the RAG knowledge base with LLM generation",
      "endpoint": "/tools/rag_query",
      "method": "POST"
    },
    {
      "name": "rag_search",
      "description": "Semantic search without LLM generation",
      "endpoint": "/tools/rag_search",
      "method": "POST"
    },
    ...
  ]
}
```

**Example:**
```bash
curl http://localhost:8000/tools
```

---

### 4. RAG Query

Query the knowledge base and generate an answer using the LLM.

**Endpoint:** `POST /tools/rag_query`

**Request Body:**
```json
{
  "query": "What is the A2A protocol?",
  "top_k": 5,
  "include_sources": true
}
```

**Parameters:**
- `query` (string, required): The user's question or query
- `top_k` (integer, optional): Number of context chunks to retrieve (default: 5)
- `include_sources` (boolean, optional): Include source information in response (default: true)

**Response:**
```json
{
  "answer": "The Agent-to-Agent Protocol (A2A) is a standardized communication framework...",
  "context": [
    "The Agent-to-Agent Protocol (A2A) enables seamless communication...",
    "A2A provides a standardized messaging framework..."
  ],
  "sources": [
    {
      "source": "data/documents/sample_doc.md",
      "score": 0.92,
      "chunk_id": "abc123..."
    }
  ]
}
```

**Status Codes:**
- `200 OK`: Query successful
- `500 Internal Server Error`: Query failed

**Example:**
```bash
curl -X POST http://localhost:8000/tools/rag_query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the A2A protocol?",
    "top_k": 5,
    "include_sources": true
  }'
```

---

### 5. RAG Search

Perform semantic search without LLM generation.

**Endpoint:** `POST /tools/rag_search`

**Request Body:**
```json
{
  "query": "agent communication",
  "top_k": 10
}
```

**Parameters:**
- `query` (string, required): Search query
- `top_k` (integer, optional): Number of results to return (default: 5)

**Response:**
```json
{
  "query": "agent communication",
  "results": [
    {
      "id": "abc123...",
      "text": "The Agent-to-Agent Protocol enables...",
      "source": "data/documents/sample_doc.md",
      "timestamp": 1705420800,
      "score": 0.89
    }
  ],
  "count": 10
}
```

**Status Codes:**
- `200 OK`: Search successful
- `500 Internal Server Error`: Search failed

**Example:**
```bash
curl -X POST http://localhost:8000/tools/rag_search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "agent communication",
    "top_k": 10
  }'
```

---

### 6. Index Document

Index a single document into the knowledge base.

**Endpoint:** `POST /tools/rag_index`

**Request Body:**
```json
{
  "file_path": "data/documents/my_document.pdf"
}
```

**Parameters:**
- `file_path` (string, required): Path to the document file

**Supported Formats:**
- PDF (`.pdf`)
- Word Documents (`.docx`)
- Text Files (`.txt`)
- Markdown (`.md`)

**Response:**
```json
{
  "status": "success",
  "message": "Document indexed successfully",
  "chunks_indexed": 42,
  "file_path": "data/documents/my_document.pdf"
}
```

**Status Codes:**
- `200 OK`: Indexing successful
- `500 Internal Server Error`: Indexing failed

**Example:**
```bash
curl -X POST http://localhost:8000/tools/rag_index \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "data/documents/my_document.pdf"
  }'
```

---

### 7. Index Directory

Index all documents in a directory.

**Endpoint:** `POST /tools/rag_index_directory`

**Request Body:**
```json
{
  "directory_path": "data/documents",
  "recursive": true
}
```

**Parameters:**
- `directory_path` (string, required): Path to the directory
- `recursive` (boolean, optional): Process subdirectories (default: true)

**Response:**
```json
{
  "status": "success",
  "message": "Directory indexed successfully",
  "chunks_indexed": 156,
  "directory_path": "data/documents"
}
```

**Status Codes:**
- `200 OK`: Indexing successful
- `500 Internal Server Error`: Indexing failed

**Example:**
```bash
curl -X POST http://localhost:8000/tools/rag_index_directory \
  -H "Content-Type: application/json" \
  -d '{
    "directory_path": "data/documents",
    "recursive": true
  }'
```

---

### 8. Get Statistics

Get statistics about the knowledge base.

**Endpoint:** `GET /tools/rag_stats`

**Response:**
```json
{
  "status": "success",
  "statistics": {
    "collection_name": "rag_knowledge_base",
    "num_entities": 156,
    "metric_type": "COSINE",
    "dimension": 384
  }
}
```

**Status Codes:**
- `200 OK`: Statistics retrieved
- `500 Internal Server Error`: Failed to retrieve statistics

**Example:**
```bash
curl http://localhost:8000/tools/rag_stats
```

---

### 9. Clear Knowledge Base

Clear all data from the knowledge base.

**Endpoint:** `DELETE /tools/rag_clear`

**⚠️ Warning:** This operation is irreversible and will delete all indexed documents.

**Response:**
```json
{
  "status": "success",
  "message": "Knowledge base cleared successfully"
}
```

**Status Codes:**
- `200 OK`: Knowledge base cleared
- `500 Internal Server Error`: Clear operation failed

**Example:**
```bash
curl -X DELETE http://localhost:8000/tools/rag_clear
```

---

## Error Responses

All endpoints may return error responses in the following format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

**Common Status Codes:**
- `400 Bad Request`: Invalid request parameters
- `404 Not Found`: Endpoint not found
- `500 Internal Server Error`: Server-side error
- `503 Service Unavailable`: Service dependencies unavailable

---

## Rate Limiting

Currently, no rate limiting is implemented. In production, consider implementing rate limiting to prevent abuse.

---

## Best Practices

### 1. Query Optimization

- Use specific, well-formed questions
- Adjust `top_k` based on your needs (3-5 for focused, 10-20 for comprehensive)
- Enable `include_sources` for transparency

### 2. Indexing

- Index documents in batches using `rag_index_directory`
- Use appropriate file formats (PDF, DOCX, TXT, MD)
- Ensure documents are well-structured and readable

### 3. Search

- Use `rag_search` for exploratory queries
- Use `rag_query` for question-answering
- Monitor similarity scores to tune thresholds

### 4. Monitoring

- Regularly check `/health` endpoint
- Monitor `/tools/rag_stats` for collection size
- Track response times and error rates

---

## Python Client Example

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

---

## JavaScript/TypeScript Client Example

```typescript
async function queryRAG(query: string) {
  const response = await fetch('http://localhost:8000/tools/rag_query', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      query: query,
      top_k: 5,
      include_sources: true
    })
  });
  
  return await response.json();
}

// Usage
const result = await queryRAG("What is the A2A protocol?");
console.log(result.answer);
```

---

## cURL Examples Collection

### Complete Workflow

```bash
# 1. Check health
curl http://localhost:8000/health

# 2. Index documents
curl -X POST http://localhost:8000/tools/rag_index_directory \
  -H "Content-Type: application/json" \
  -d '{"directory_path": "data/documents", "recursive": true}'

# 3. Check statistics
curl http://localhost:8000/tools/rag_stats

# 4. Query knowledge base
curl -X POST http://localhost:8000/tools/rag_query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the A2A protocol?", "top_k": 5}'

# 5. Search without LLM
curl -X POST http://localhost:8000/tools/rag_search \
  -H "Content-Type: application/json" \
  -d '{"query": "agent communication", "top_k": 10}'
```

---

## OpenAPI/Swagger Documentation

The server provides interactive API documentation at:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

These interfaces allow you to:
- Explore all endpoints
- Test API calls directly from the browser
- View request/response schemas
- Download OpenAPI specification

---

## Support

For issues or questions:
- GitHub Issues: [Project Issues](https://github.com/ibm/a2a-rag-agent/issues)
- Documentation: [Main README](README.md)