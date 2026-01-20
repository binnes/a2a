# Troubleshooting Guide

Common issues and solutions for the A2A RAG Agent system.

## Service Issues

### Milvus Connection Problems

#### Issue: Cannot connect to Milvus

**Symptoms**:
```
pymilvus.exceptions.MilvusException: <MilvusException: (code=1, message=Fail connecting to server)>
```

**Solutions**:

1. **Check if Milvus is running**:
```bash
podman ps | grep milvus
```

2. **View Milvus logs**:
```bash
cd RAG/deployment
podman-compose logs milvus
```

3. **Restart Milvus**:
```bash
cd RAG/deployment
podman-compose restart
```

4. **Verify Milvus health**:
```bash
curl http://localhost:9091/healthz
```

5. **Check port availability**:
```bash
lsof -i :19530
```

#### Issue: Milvus fails to start

**Symptoms**:
```
Error: port 19530 already in use
```

**Solutions**:

1. **Find and kill process using port**:
```bash
lsof -i :19530
kill -9 <PID>
```

2. **Use different port**:
```bash
# Edit deployment/podman-compose.yml
ports:
  - "19531:19530"  # Changed from 19530

# Update config/.env
MILVUS_PORT=19531
```

### MCP Server Issues

#### Issue: MCP server won't start

**Symptoms**:
```
ERROR: Address already in use
```

**Solutions**:

1. **Check if port 8000 is in use**:
```bash
lsof -i :8000
```

2. **Kill existing process**:
```bash
kill -9 <PID>
```

3. **Use different port**:
```bash
# Start on different port
python -m uvicorn mcp_server.server:app --port 8001

# Update config/.env
MCP_SERVER_PORT=8001
```

4. **Check server logs**:
```bash
tail -f logs/mcp_server.log
```

#### Issue: MCP server crashes on startup

**Symptoms**:
```
ImportError: cannot import name 'FastAPI'
```

**Solutions**:

1. **Verify virtual environment**:
```bash
which python
# Should show: /path/to/RAG/venv/bin/python
```

2. **Reinstall dependencies**:
```bash
cd RAG
source venv/bin/activate
pip install -r requirements.txt
```

3. **Check Python version**:
```bash
python --version
# Should be 3.11-3.13 for Watsonx.ai 1.5.0
```

## Watsonx.ai Issues

### Authentication Errors

#### Issue: Invalid API key

**Symptoms**:
```
401 Unauthorized: Invalid API key
```

**Solutions**:

1. **Verify API key in `.env`**:
```bash
cat config/.env | grep WATSONX_API_KEY
```

2. **Check API key format**:
   - Should start with `apikey_`
   - No extra spaces or quotes
   - No newlines

3. **Regenerate API key**:
   - Go to IBM Cloud console
   - Navigate to Watsonx.ai
   - Generate new API key
   - Update `config/.env`

#### Issue: Project ID not found

**Symptoms**:
```
404 Not Found: Project not found
```

**Solutions**:

1. **Verify project ID**:
```bash
cat config/.env | grep WATSONX_PROJECT_ID
```

2. **Check project exists**:
   - Log into Watsonx.ai console
   - Verify project is active
   - Copy correct project ID

3. **Check project permissions**:
   - Ensure API key has access to project
   - Verify project is not archived

### Model Issues

#### Issue: Model not found

**Symptoms**:
```
404 Not Found: Model 'openai/gpt-oss-120b' not found
```

**Solutions**:

1. **Check available models**:
```python
from ibm_watsonx_ai import APIClient, Credentials

credentials = Credentials(
    api_key="your-key",
    url="https://us-south.ml.cloud.ibm.com"
)
client = APIClient(credentials)
client.set.default_project("your-project-id")

# List available models
models = client.foundation_models.get_model_specs()
for model in models['resources']:
    print(model['model_id'])
```

2. **Use alternative model**:
```bash
# In config/.env
WATSONX_LLM_MODEL=ibm/granite-3-8b-instruct
```

#### Issue: Token limit exceeded

**Symptoms**:
```
400 Bad Request: Token limit exceeded (660 > 512)
```

**Solutions**:

1. **Reduce chunk size**:
```bash
# In config/.env
RAG_CHUNK_SIZE=200  # Reduced from 300
```

2. **Reduce chunk overlap**:
```bash
RAG_CHUNK_OVERLAP=20  # Reduced from 40
```

3. **Use model with higher limit**:
```bash
# Some models support up to 8192 tokens
WATSONX_EMBEDDING_MODEL=ibm/granite-embedding-278m-multilingual
```

## Document Processing Issues

### Indexing Failures

#### Issue: Unsupported file type

**Symptoms**:
```
ValueError: Unsupported file type: .xyz
```

**Solutions**:

1. **Check supported formats**:
   - PDF (`.pdf`)
   - Word (`.docx`)
   - Text (`.txt`)
   - Markdown (`.md`)

2. **Convert file to supported format**:
```bash
# Convert to PDF or text
pandoc document.xyz -o document.pdf
```

#### Issue: File not found

**Symptoms**:
```
FileNotFoundError: [Errno 2] No such file or directory: 'data/documents/file.pdf'
```

**Solutions**:

1. **Check file path**:
```bash
ls -la data/documents/
```

2. **Use absolute path**:
```bash
# Instead of relative path
file_path="/full/path/to/RAG/data/documents/file.pdf"
```

3. **Verify file permissions**:
```bash
chmod 644 data/documents/file.pdf
```

#### Issue: PDF extraction fails

**Symptoms**:
```
PDFSyntaxError: PDF file is corrupted
```

**Solutions**:

1. **Repair PDF**:
```bash
# Using ghostscript
gs -o repaired.pdf -sDEVICE=pdfwrite -dPDFSETTINGS=/prepress corrupted.pdf
```

2. **Convert to text first**:
```bash
pdftotext document.pdf document.txt
# Then index the text file
```

## Query Issues

### No Results Returned

#### Issue: Query returns empty results

**Symptoms**:
```json
{
  "results": [],
  "count": 0
}
```

**Solutions**:

1. **Check if documents are indexed**:
```bash
curl http://localhost:8000/tools/rag_stats
```

2. **Lower score threshold**:
```bash
# In config/.env
RAG_SCORE_THRESHOLD=0.6  # Lowered from 0.7
```

3. **Increase top-k**:
```bash
RAG_TOP_K=10  # Increased from 5
```

4. **Verify embeddings**:
```python
from services.watsonx_client import WatsonxClient
from config.settings import get_settings

client = WatsonxClient(get_settings())
embedding = client.generate_embedding("test query")
print(f"Embedding dimension: {len(embedding)}")
# Should match EMBEDDING_DIMENSION in config
```

### Poor Quality Responses

#### Issue: Irrelevant or incorrect answers

**Solutions**:

1. **Adjust LLM temperature**:
```bash
# More deterministic
WATSONX_LLM_TEMPERATURE=0.3  # Reduced from 0.7
```

2. **Increase context**:
```bash
RAG_TOP_K=10  # More context chunks
RAG_MAX_CONTEXT_LENGTH=3000  # More tokens
```

3. **Improve system prompt**:
```bash
RAG_SYSTEM_PROMPT="You are a helpful assistant. Answer based only on the provided context. If the context doesn't contain the answer, say so."
```

4. **Re-index with better chunking**:
```bash
# Clear and re-index
curl -X DELETE http://localhost:8000/tools/rag_clear
curl -X POST http://localhost:8000/tools/rag_index_directory \
  -H "Content-Type: application/json" \
  -d '{"directory_path": "data/documents"}'
```

## Performance Issues

### Slow Query Responses

#### Issue: Queries take too long

**Solutions**:

1. **Optimize Milvus index**:
```bash
# In config/.env
MILVUS_INDEX_TYPE=IVF_SQ8  # Faster than IVF_FLAT
MILVUS_NLIST=256
```

2. **Reduce top-k**:
```bash
RAG_TOP_K=3  # Reduced from 5
```

3. **Reduce max tokens**:
```bash
WATSONX_LLM_MAX_TOKENS=256  # Reduced from 512
```

4. **Enable caching**:
```bash
ENABLE_EMBEDDING_CACHE=true
CACHE_TTL=3600
```

### High Memory Usage

#### Issue: System uses too much memory

**Solutions**:

1. **Use quantized index**:
```bash
MILVUS_INDEX_TYPE=IVF_SQ8  # Uses less memory
```

2. **Reduce batch size**:
```bash
EMBEDDING_BATCH_SIZE=16  # Reduced from 32
BATCH_SIZE=50  # Reduced from 100
```

3. **Limit concurrent processing**:
```bash
MAX_CONCURRENT_DOCUMENTS=3  # Reduced from 5
MAX_CONCURRENT_QUERIES=5  # Reduced from 10
```

## Testing Issues

### Test Failures

#### Issue: Tests fail with connection errors

**Solutions**:

1. **Ensure services are running**:
```bash
./scripts/start_services.sh
```

2. **Wait for services to be ready**:
```bash
# Wait 30 seconds after starting
sleep 30
```

3. **Check service health**:
```bash
curl http://localhost:8000/health
```

#### Issue: Import errors in tests

**Solutions**:

1. **Activate virtual environment**:
```bash
source venv/bin/activate
```

2. **Install test dependencies**:
```bash
pip install pytest pytest-asyncio
```

3. **Set PYTHONPATH**:
```bash
export PYTHONPATH=/path/to/RAG:$PYTHONPATH
```

## Data Issues

### Collection Errors

#### Issue: Dimension mismatch

**Symptoms**:
```
MilvusException: dimension mismatch: expected 384, got 768
```

**Solutions**:

1. **Clear collection**:
```bash
curl -X DELETE http://localhost:8000/tools/rag_clear
```

2. **Update dimension in config**:
```bash
# Match your embedding model
EMBEDDING_DIMENSION=384  # or 768
```

3. **Re-index documents**:
```bash
curl -X POST http://localhost:8000/tools/rag_index_directory \
  -H "Content-Type: application/json" \
  -d '{"directory_path": "data/documents"}'
```

#### Issue: Collection not found

**Symptoms**:
```
MilvusException: Collection 'rag_knowledge_base' not found
```

**Solutions**:

1. **Restart Milvus**:
```bash
cd RAG/deployment
podman-compose restart
```

2. **Check collection name**:
```bash
# In config/.env
MILVUS_COLLECTION_NAME=rag_knowledge_base
```

3. **Create collection manually**:
```python
from services.milvus_client import MilvusClient
from config.settings import get_settings

client = MilvusClient(get_settings())
# Collection will be created automatically
```

## Logging and Debugging

### Enable Debug Logging

```bash
# In config/.env
LOG_LEVEL=DEBUG
```

### View Logs

```bash
# MCP server logs
tail -f logs/mcp_server.log

# Milvus logs
cd RAG/deployment
podman-compose logs -f milvus

# Application logs
tail -f logs/rag.log
```

### Debug Mode

```python
# Enable debug mode in code
import logging
logging.basicConfig(level=logging.DEBUG)

# Or set environment variable
export LOG_LEVEL=DEBUG
```

## Getting Help

### Collect Diagnostic Information

```bash
# System information
python --version
podman --version

# Service status
curl http://localhost:8000/health
curl http://localhost:9091/healthz

# Configuration
cat config/.env | grep -v API_KEY

# Logs
tail -100 logs/mcp_server.log
```

### Report Issues

When reporting issues, include:

1. Error message and stack trace
2. Configuration (without sensitive data)
3. Steps to reproduce
4. System information
5. Relevant logs

### Resources

- [GitHub Issues](https://github.com/ibm/a2a-rag-agent/issues)
- [Quick Start Guide](quickstart.md)
- [Configuration Guide](configuration.md)
- [API Reference](api-reference.md)

## Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| `Connection refused` | Service not running | Start services with `./scripts/start_services.sh` |
| `401 Unauthorized` | Invalid API key | Check `WATSONX_API_KEY` in `.env` |
| `404 Not Found` | Wrong endpoint/model | Verify URL and model name |
| `422 Unprocessable Entity` | Invalid parameters | Check request body format |
| `500 Internal Server Error` | Server-side error | Check logs for details |
| `503 Service Unavailable` | Dependencies down | Check Milvus and Watsonx.ai |
| `Token limit exceeded` | Chunk too large | Reduce `RAG_CHUNK_SIZE` |
| `Dimension mismatch` | Wrong embedding model | Clear collection and re-index |
| `Collection not found` | Milvus not initialized | Restart Milvus |
| `File not found` | Wrong path | Check file path and permissions |