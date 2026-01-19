# Configuration Guide

Comprehensive configuration options for the A2A RAG Agent system.

## Configuration Files

### Primary Configuration

**File**: [`RAG/config/.env`](../../RAG/config/.env)

This file contains all environment variables for the system.

### Settings Module

**File**: [`RAG/config/settings.py`](../../RAG/config/settings.py)

Pydantic-based settings management with validation and type safety.

## Environment Variables

### Watsonx.ai Configuration

```bash
# API Credentials (Required)
WATSONX_API_KEY=your-api-key-here
WATSONX_PROJECT_ID=your-project-id-here
WATSONX_URL=https://us-south.ml.cloud.ibm.com

# Embedding Model
EMBEDDING_MODEL=ibm/granite-embedding-278m-multilingual
EMBEDDING_DIMENSION=768

# LLM Model
LLM_MODEL=openai/gpt-oss-120b
LLM_MAX_TOKENS=16384
LLM_TEMPERATURE=0.7
```

**Available Models**:

| Model | Type | Dimension | Token Limit |
|-------|------|-----------|-------------|
| `ibm/granite-embedding-278m-multilingual` | Embedding | 768 | 512 |
| `ibm/slate-125m-english-rtrvr-v2` | Embedding | 384 | 512 |
| `openai/gpt-oss-120b` | LLM | - | 16384 |
| `ibm/granite-3-8b-instruct` | LLM | - | 8192 |

### Milvus Configuration

```bash
# Connection
MILVUS_HOST=localhost
MILVUS_PORT=19530
MILVUS_USER=
MILVUS_PASSWORD=

# Collection
MILVUS_COLLECTION_NAME=rag_knowledge_base
MILVUS_INDEX_TYPE=IVF_FLAT
MILVUS_METRIC_TYPE=COSINE
MILVUS_NLIST=128
```

**Index Types**:

| Type | Description | Use Case |
|------|-------------|----------|
| `IVF_FLAT` | Inverted file with flat search | Balanced speed/accuracy |
| `IVF_SQ8` | IVF with scalar quantization | Memory-efficient |
| `HNSW` | Hierarchical navigable small world | High accuracy |
| `FLAT` | Brute force search | Small datasets |

**Metric Types**:

| Type | Description | Range |
|------|-------------|-------|
| `COSINE` | Cosine similarity | [-1, 1] |
| `L2` | Euclidean distance | [0, ∞) |
| `IP` | Inner product | (-∞, ∞) |

### MCP Server Configuration

```bash
# Server
MCP_SERVER_HOST=0.0.0.0
MCP_SERVER_PORT=8000
MCP_SERVER_RELOAD=false

# CORS
MCP_CORS_ORIGINS=["*"]
MCP_CORS_ALLOW_CREDENTIALS=true
```

### RAG Configuration

```bash
# Chunking
RAG_CHUNK_SIZE=80           # words
RAG_CHUNK_OVERLAP=10        # words
RAG_MIN_CHUNK_SIZE=20       # words

# Retrieval
RAG_TOP_K=5                 # number of results
RAG_SCORE_THRESHOLD=0.7     # similarity threshold
RAG_MAX_CONTEXT_LENGTH=2000 # tokens

# Generation
RAG_SYSTEM_PROMPT="You are a helpful assistant..."
RAG_INCLUDE_SOURCES=true
```

### Logging Configuration

```bash
# Logging
LOG_LEVEL=INFO              # DEBUG, INFO, WARNING, ERROR
LOG_FORMAT=json             # json or text
LOG_FILE=logs/rag.log
LOG_ROTATION=1 day
LOG_RETENTION=30 days
```

## Configuration Tuning

### Chunk Size Optimization

The chunk size affects both retrieval quality and token limits.

**Guidelines**:

```python
# Technical documentation (dense information)
RAG_CHUNK_SIZE=60-100  # words

# Narrative content (stories, articles)
RAG_CHUNK_SIZE=100-150  # words

# Code documentation
RAG_CHUNK_SIZE=50-80  # words

# Legal/policy documents
RAG_CHUNK_SIZE=80-120  # words
```

**Considerations**:
- Embedding model token limit (512 tokens for granite-embedding-278m)
- Context window of LLM (16384 tokens for gpt-oss-120b)
- Document structure and formatting
- Query complexity
- Word-to-token ratio (approximately 1.3 tokens per word)

### Chunk Overlap

Overlap ensures context continuity across chunks.

```python
# Standard overlap (recommended)
RAG_CHUNK_OVERLAP=10  # ~12.5% of 80-word chunks

# High overlap (better context, more storage)
RAG_CHUNK_OVERLAP=20  # ~25% of 80-word chunks

# Low overlap (less storage, potential context loss)
RAG_CHUNK_OVERLAP=5  # ~6% of 80-word chunks
```

### Top-K Selection

Number of chunks to retrieve for context.

```python
# Focused queries (specific questions)
RAG_TOP_K=3-5

# Exploratory queries (broad topics)
RAG_TOP_K=10-15

# Comprehensive analysis
RAG_TOP_K=15-20
```

**Trade-offs**:
- Higher K: More context, slower, more tokens
- Lower K: Faster, less context, may miss relevant info

### Score Threshold

Minimum similarity score for retrieved chunks.

```python
# High precision (strict matching)
RAG_SCORE_THRESHOLD=0.85

# Balanced (recommended)
RAG_SCORE_THRESHOLD=0.70

# High recall (include more results)
RAG_SCORE_THRESHOLD=0.60
```

### LLM Parameters

```bash
# Temperature (creativity vs consistency)
LLM_TEMPERATURE=0.7  # Balanced
# 0.0-0.3: Deterministic, factual
# 0.4-0.7: Balanced
# 0.8-1.0: Creative, varied

# Max tokens (response length)
LLM_MAX_TOKENS=16384  # Maximum for gpt-oss-120b
# 512: Brief responses
# 1024: Standard responses
# 4096: Detailed responses
# 16384: Comprehensive responses

# Top P (nucleus sampling)
LLM_TOP_P=0.9
# 0.9: Balanced diversity
# 0.95: More diverse
# 0.8: More focused
```

## Performance Tuning

### Milvus Optimization

```bash
# For large collections (>1M vectors)
MILVUS_INDEX_TYPE=IVF_SQ8
MILVUS_NLIST=1024
MILVUS_NPROBE=16

# For small collections (<100K vectors)
MILVUS_INDEX_TYPE=HNSW
MILVUS_M=16
MILVUS_EF_CONSTRUCTION=200

# For memory-constrained environments
MILVUS_INDEX_TYPE=IVF_SQ8
MILVUS_NLIST=256
```

### Concurrent Processing

```bash
# Document processing
MAX_CONCURRENT_DOCUMENTS=5
BATCH_SIZE=100

# Embedding generation
EMBEDDING_BATCH_SIZE=32
MAX_EMBEDDING_RETRIES=3

# Query processing
MAX_CONCURRENT_QUERIES=10
QUERY_TIMEOUT=30  # seconds
```

### Caching

```bash
# Enable caching
ENABLE_EMBEDDING_CACHE=true
CACHE_TTL=3600  # seconds
CACHE_MAX_SIZE=1000  # entries

# Redis cache (optional)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

## Security Configuration

### API Authentication

```bash
# Enable authentication
ENABLE_AUTH=true
AUTH_TYPE=api_key  # api_key, oauth, jwt

# API Key authentication
API_KEY_HEADER=X-API-Key
API_KEYS=["key1", "key2"]

# JWT authentication
JWT_SECRET=your-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION=3600
```

### CORS Configuration

```bash
# Production CORS
MCP_CORS_ORIGINS=["https://yourdomain.com"]
MCP_CORS_ALLOW_CREDENTIALS=true
MCP_CORS_ALLOW_METHODS=["GET", "POST", "DELETE"]
MCP_CORS_ALLOW_HEADERS=["Content-Type", "Authorization"]

# Development CORS (permissive)
MCP_CORS_ORIGINS=["*"]
```

### Rate Limiting

```bash
# Enable rate limiting
ENABLE_RATE_LIMIT=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_PERIOD=60  # seconds

# Per-endpoint limits
QUERY_RATE_LIMIT=20
INDEX_RATE_LIMIT=10
```

## Environment-Specific Configuration

### Development

```bash
# .env.development
LOG_LEVEL=DEBUG
MCP_SERVER_RELOAD=true
ENABLE_AUTH=false
MCP_CORS_ORIGINS=["*"]
WATSONX_LLM_TEMPERATURE=0.7
```

### Staging

```bash
# .env.staging
LOG_LEVEL=INFO
MCP_SERVER_RELOAD=false
ENABLE_AUTH=true
MCP_CORS_ORIGINS=["https://staging.yourdomain.com"]
WATSONX_LLM_TEMPERATURE=0.5
```

### Production

```bash
# .env.production
LOG_LEVEL=WARNING
MCP_SERVER_RELOAD=false
ENABLE_AUTH=true
ENABLE_RATE_LIMIT=true
MCP_CORS_ORIGINS=["https://yourdomain.com"]
WATSONX_LLM_TEMPERATURE=0.3
ENABLE_EMBEDDING_CACHE=true
```

## Configuration Validation

### Using Settings Module

```python
from config.settings import get_settings

# Load and validate settings
settings = get_settings()

# Access settings
print(f"Embedding model: {settings.watsonx_embedding_model}")
print(f"Chunk size: {settings.rag_chunk_size}")
print(f"Top K: {settings.rag_top_k}")

# Validate configuration
assert settings.embedding_dimension == 384
assert settings.rag_chunk_size <= 512
```

### Configuration Checks

```bash
# Verify configuration
cd RAG
python -c "
from config.settings import get_settings
settings = get_settings()
print('Configuration valid!')
print(f'Embedding model: {settings.watsonx_embedding_model}')
print(f'Milvus host: {settings.milvus_host}')
"
```

## Troubleshooting

### Common Issues

**Issue**: Token limit exceeded

```bash
# Solution: Reduce chunk size
RAG_CHUNK_SIZE=200  # Reduced from 300
```

**Issue**: Low retrieval quality

```bash
# Solution: Adjust threshold and top-k
RAG_SCORE_THRESHOLD=0.65  # Lowered from 0.7
RAG_TOP_K=10  # Increased from 5
```

**Issue**: Slow query responses

```bash
# Solution: Optimize Milvus and reduce top-k
MILVUS_INDEX_TYPE=IVF_SQ8
RAG_TOP_K=3  # Reduced from 5
WATSONX_LLM_MAX_TOKENS=256  # Reduced from 512
```

**Issue**: High memory usage

```bash
# Solution: Use quantized index and reduce batch size
MILVUS_INDEX_TYPE=IVF_SQ8
EMBEDDING_BATCH_SIZE=16  # Reduced from 32
```

## Configuration Templates

### Minimal Configuration

```bash
# Minimal .env for quick start
WATSONX_API_KEY=your-key
WATSONX_PROJECT_ID=your-project
EMBEDDING_MODEL=ibm/granite-embedding-278m-multilingual
LLM_MODEL=openai/gpt-oss-120b
```

### Production Configuration

```bash
# Production .env with all optimizations
WATSONX_API_KEY=your-key
WATSONX_PROJECT_ID=your-project
WATSONX_URL=https://us-south.ml.cloud.ibm.com
EMBEDDING_MODEL=ibm/granite-embedding-278m-multilingual
EMBEDDING_DIMENSION=768
LLM_MODEL=openai/gpt-oss-120b
LLM_MAX_TOKENS=16384
LLM_TEMPERATURE=0.3

MILVUS_HOST=milvus-prod.internal
MILVUS_PORT=19530
MILVUS_COLLECTION_NAME=rag_production
MILVUS_INDEX_TYPE=IVF_SQ8
MILVUS_METRIC_TYPE=COSINE

MCP_SERVER_HOST=0.0.0.0
MCP_SERVER_PORT=8000
MCP_CORS_ORIGINS=["https://yourdomain.com"]

RAG_CHUNK_SIZE=80
RAG_CHUNK_OVERLAP=10
RAG_TOP_K=5
RAG_SCORE_THRESHOLD=0.7

LOG_LEVEL=WARNING
ENABLE_AUTH=true
ENABLE_RATE_LIMIT=true
ENABLE_EMBEDDING_CACHE=true
```

## See Also

- [Quick Start Guide](quickstart.md)
- [API Reference](api-reference.md)
- [Testing Guide](testing.md)
- [Troubleshooting](troubleshooting.md)