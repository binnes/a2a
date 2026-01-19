# API Reference

Complete reference for the MCP Server REST API.

## Base URL

```
http://localhost:8000
```

## Authentication

Currently, the API does not require authentication. In production, implement appropriate authentication mechanisms (API keys, OAuth, etc.).

## Common Response Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad Request - Invalid parameters |
| 404 | Not Found - Endpoint or resource not found |
| 422 | Unprocessable Entity - Validation error |
| 500 | Internal Server Error |
| 503 | Service Unavailable - Dependencies unavailable |

## Endpoints

### Root

Get server information.

**Request:**
```http
GET /
```

**Response:**
```json
{
  "name": "MCP RAG Server",
  "version": "0.1.0",
  "description": "Model Context Protocol server for RAG operations"
}
```

---

### Health Check

Check the health status of the server and its dependencies.

**Request:**
```http
GET /health
```

**Response (Healthy):**
```json
{
  "status": "healthy",
  "components": {
    "watsonx": true,
    "milvus": true
  }
}
```

**Response (Unhealthy):**
```json
{
  "status": "unhealthy",
  "components": {
    "watsonx": true,
    "milvus": false
  }
}
```

**Status Codes:**
- `200 OK` - All components healthy
- `503 Service Unavailable` - One or more components unhealthy

**Example:**
```bash
curl http://localhost:8000/health
```

---

### List Tools

Get a list of all available MCP tools.

**Request:**
```http
GET /tools
```

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
    {
      "name": "rag_index",
      "description": "Index a single document",
      "endpoint": "/tools/rag_index",
      "method": "POST"
    },
    {
      "name": "rag_index_directory",
      "description": "Index all documents in a directory",
      "endpoint": "/tools/rag_index_directory",
      "method": "POST"
    },
    {
      "name": "rag_stats",
      "description": "Get knowledge base statistics",
      "endpoint": "/tools/rag_stats",
      "method": "GET"
    },
    {
      "name": "rag_clear",
      "description": "Clear the knowledge base",
      "endpoint": "/tools/rag_clear",
      "method": "DELETE"
    }
  ]
}
```

---

### RAG Query

Query the knowledge base and generate an answer using the LLM.

**Request:**
```http
POST /tools/rag_query
Content-Type: application/json
```

**Request Body:**
```json
{
  "query": "What is the A2A protocol?",
  "top_k": 5,
  "include_sources": true
}
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | Yes | - | The user's question or query |
| `top_k` | integer | No | 5 | Number of context chunks to retrieve (1-20) |
| `include_sources` | boolean | No | true | Include source information in response |

**Response:**
```json
{
  "answer": "The Agent-to-Agent Protocol (A2A) is a standardized communication framework that enables autonomous agents to discover, communicate, and collaborate with each other...",
  "context": [
    "The Agent-to-Agent Protocol (A2A) enables seamless communication between autonomous agents...",
    "A2A provides a standardized messaging framework for agent interactions..."
  ],
  "sources": [
    {
      "source": "data/documents/sample_doc.md",
      "score": 0.92,
      "chunk_id": "abc123..."
    },
    {
      "source": "data/documents/sample_doc.md",
      "score": 0.89,
      "chunk_id": "def456..."
    }
  ]
}
```

**Status Codes:**
- `200 OK` - Query successful
- `422 Unprocessable Entity` - Invalid parameters
- `500 Internal Server Error` - Query failed

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

### RAG Search

Perform semantic search without LLM generation.

**Request:**
```http
POST /tools/rag_search
Content-Type: application/json
```

**Request Body:**
```json
{
  "query": "agent communication",
  "top_k": 10
}
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | Yes | - | Search query |
| `top_k` | integer | No | 5 | Number of results to return (1-20) |

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
    },
    {
      "id": "def456...",
      "text": "Communication between agents uses...",
      "source": "data/documents/sample_doc.md",
      "timestamp": 1705420800,
      "score": 0.85
    }
  ],
  "count": 10
}
```

**Status Codes:**
- `200 OK` - Search successful
- `422 Unprocessable Entity` - Invalid parameters
- `500 Internal Server Error` - Search failed

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

### Index Document

Index a single document into the knowledge base.

**Request:**
```http
POST /tools/rag_index
Content-Type: application/json
```

**Request Body:**
```json
{
  "file_path": "data/documents/my_document.pdf"
}
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file_path` | string | Yes | Path to the document file (relative to project root) |

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
- `200 OK` - Indexing successful
- `422 Unprocessable Entity` - Invalid file path or unsupported format
- `500 Internal Server Error` - Indexing failed

**Example:**
```bash
curl -X POST http://localhost:8000/tools/rag_index \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "data/documents/my_document.pdf"
  }'
```

---

### Index Directory

Index all documents in a directory.

**Request:**
```http
POST /tools/rag_index_directory
Content-Type: application/json
```

**Request Body:**
```json
{
  "directory_path": "data/documents",
  "recursive": true
}
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `directory_path` | string | Yes | - | Path to the directory |
| `recursive` | boolean | No | true | Process subdirectories |

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
- `200 OK` - Indexing successful
- `422 Unprocessable Entity` - Invalid directory path
- `500 Internal Server Error` - Indexing failed

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

### Get Statistics

Get statistics about the knowledge base.

**Request:**
```http
GET /tools/rag_stats
```

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
- `200 OK` - Statistics retrieved
- `500 Internal Server Error` - Failed to retrieve statistics

**Example:**
```bash
curl http://localhost:8000/tools/rag_stats
```

---

### Clear Knowledge Base

Clear all data from the knowledge base.

⚠️ **Warning:** This operation is irreversible and will delete all indexed documents.

**Request:**
```http
DELETE /tools/rag_clear
```

**Response:**
```json
{
  "status": "success",
  "message": "Knowledge base cleared successfully"
}
```

**Status Codes:**
- `200 OK` - Knowledge base cleared
- `500 Internal Server Error` - Clear operation failed

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

### Common Errors

**400 Bad Request:**
```json
{
  "detail": "Invalid request parameters"
}
```

**404 Not Found:**
```json
{
  "detail": "Endpoint not found"
}
```

**422 Unprocessable Entity:**
```json
{
  "detail": [
    {
      "loc": ["body", "query"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**500 Internal Server Error:**
```json
{
  "detail": "Internal server error: [error details]"
}
```

**503 Service Unavailable:**
```json
{
  "detail": "Service dependencies unavailable"
}
```

---

## Rate Limiting

Currently, no rate limiting is implemented. In production, consider implementing rate limiting to prevent abuse.

---

## Interactive Documentation

The server provides interactive API documentation:

- **Swagger UI**: [`http://localhost:8000/docs`](http://localhost:8000/docs)
- **ReDoc**: [`http://localhost:8000/redoc`](http://localhost:8000/redoc)

These interfaces allow you to:
- Explore all endpoints
- Test API calls directly from the browser
- View request/response schemas
- Download OpenAPI specification

---

## Client Libraries

### Python

```python
import httpx
import asyncio

class RAGClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient()
    
    async def query(self, query: str, top_k: int = 5):
        response = await self.client.post(
            f"{self.base_url}/tools/rag_query",
            json={"query": query, "top_k": top_k}
        )
        return response.json()
    
    async def search(self, query: str, top_k: int = 5):
        response = await self.client.post(
            f"{self.base_url}/tools/rag_search",
            json={"query": query, "top_k": top_k}
        )
        return response.json()
    
    async def index(self, file_path: str):
        response = await self.client.post(
            f"{self.base_url}/tools/rag_index",
            json={"file_path": file_path}
        )
        return response.json()
    
    async def stats(self):
        response = await self.client.get(
            f"{self.base_url}/tools/rag_stats"
        )
        return response.json()
    
    async def close(self):
        await self.client.aclose()

# Usage
async def main():
    client = RAGClient()
    result = await client.query("What is the A2A protocol?")
    print(result["answer"])
    await client.close()

asyncio.run(main())
```

### JavaScript/TypeScript

```typescript
class RAGClient {
  constructor(private baseUrl: string = 'http://localhost:8000') {}
  
  async query(query: string, topK: number = 5) {
    const response = await fetch(`${this.baseUrl}/tools/rag_query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, top_k: topK })
    });
    return await response.json();
  }
  
  async search(query: string, topK: number = 5) {
    const response = await fetch(`${this.baseUrl}/tools/rag_search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, top_k: topK })
    });
    return await response.json();
  }
  
  async index(filePath: string) {
    const response = await fetch(`${this.baseUrl}/tools/rag_index`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ file_path: filePath })
    });
    return await response.json();
  }
  
  async stats() {
    const response = await fetch(`${this.baseUrl}/tools/rag_stats`);
    return await response.json();
  }
}

// Usage
const client = new RAGClient();
const result = await client.query("What is the A2A protocol?");
console.log(result.answer);
```

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

## See Also

- [Quick Start Guide](quickstart.md)
- [Configuration Guide](configuration.md)
- [Testing Guide](testing.md)
- [Troubleshooting](troubleshooting.md)