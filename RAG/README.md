# A2A RAG Agent

A production-ready Retrieval-Augmented Generation (RAG) agent implementing the Agent-to-Agent (A2A) protocol with Model Context Protocol (MCP) tools.

## Quick Start

### Local Deployment (Podman)

```bash
# Deploy locally with automatic Shakespeare data loading
cd deployment
./deploy.sh local

# Query Shakespeare
curl -X POST http://localhost:8000/tools/rag_query \
  -H "Content-Type: application/json" \
  -d '{"query": "What did Hamlet say about being?"}'
```

### IBM Code Engine Deployment

```bash
# Deploy to IBM Cloud with automatic Shakespeare data loading
cd deployment
./deploy.sh ibm-code-engine
```

### Legacy Setup (Manual)

```bash
# 1. Setup
./deployment/setup.sh

# 2. Configure credentials
# Edit config/.env with your Watsonx.ai credentials

# 3. Start services
./scripts/start_services.sh

# 4. Query the system
curl -X POST http://localhost:8000/tools/rag_query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the A2A protocol?", "top_k": 5}'
```

## Architecture

```
User → A2A Agent (LangGraph) → MCP Server (FastAPI) → Watsonx.ai + Milvus
```

**Components:**
- **A2A Agent**: LangGraph-based workflow orchestration
- **MCP Server**: RESTful API with 9 endpoints
- **Watsonx.ai**: Embeddings (768-dim) + LLM (GPT-OSS-120B)
- **Milvus**: Vector database with COSINE similarity

## Status

✅ **Production-Ready**
- 34/34 tests passing (100% coverage)
- Comprehensive documentation
- Deployment automation
- Performance optimized

## Deployment Options

### 🏠 Local (Podman)

Best for development and testing. Includes automatic Shakespeare data loading.

```bash
cd deployment/local
cp .env.example .env
# Edit .env with credentials
./deploy.sh
```

**Services:**
- Milvus: http://localhost:19530
- MCP Server: http://localhost:8000
- A2A Agent: http://localhost:8001

**Documentation:** [Local Deployment Guide](../docs/docs/deployment/local.md)

### ☁️ IBM Code Engine

Best for production and demos. Includes automatic Shakespeare data loading via job.

```bash
cd deployment/ibm-code-engine
cp .env.example .env
# Edit .env with credentials
./deploy-all.sh
```

**Documentation:** [IBM Code Engine Guide](../docs/docs/deployment/ibm-code-engine.md)

## Documentation

📚 **Complete documentation available in the MkDocs site:**

- **[Overview](../docs/docs/rag/overview.md)** - Architecture and components
- **[Quick Start](../docs/docs/rag/quickstart.md)** - Detailed setup guide
- **[API Reference](../docs/docs/rag/api-reference.md)** - Complete API docs
- **[Configuration](../docs/docs/rag/configuration.md)** - Configuration options
- **[Testing](../docs/docs/rag/testing.md)** - Testing guide
- **[Troubleshooting](../docs/docs/rag/troubleshooting.md)** - Common issues
- **[Local Deployment](../docs/docs/deployment/local.md)** - Deploy with Podman
- **[IBM Code Engine](../docs/docs/deployment/ibm-code-engine.md)** - Deploy to cloud

### View Documentation

```bash
cd docs
pip install -r requirements.txt
mkdocs serve
# Open http://127.0.0.1:8000
```

## Key Features

- **Document Processing**: PDF, DOCX, TXT, Markdown support
- **Semantic Search**: COSINE similarity with configurable thresholds
- **Context-Aware Generation**: LLM responses with source attribution
- **Async Processing**: High-performance concurrent operations
- **Health Monitoring**: Comprehensive health checks
- **Error Handling**: Retry logic with exponential backoff
- **Automatic Data Loading**: Shakespeare text loaded automatically on deployment
- **Dual Deployment**: Local (Podman) and cloud (IBM Code Engine) options

## Project Structure

```
RAG/
├── agent/              # A2A agent (LangGraph)
├── mcp_server/         # MCP server (FastAPI)
├── services/           # Core services (Watsonx, Milvus, Document processor)
├── config/             # Configuration management
├── deployment/         # Deployment configurations
│   ├── local/          # Local Podman deployment
│   ├── ibm-code-engine/# IBM Code Engine deployment
│   └── deploy.sh       # Unified deployment script
├── scripts/            # Utility scripts
├── tests/              # Test suite (34 tests)
└── data/               # Documents and examples
    └── reference/      # Shakespeare and other reference texts
```

## Requirements

- Python 3.11-3.13 (for Watsonx.ai 1.5.0)
- Podman or Docker
- IBM Watsonx.ai account

## Common Commands

```bash
# Start services
./scripts/start_services.sh

# Stop services
./scripts/stop_services.sh

# Run tests
./scripts/run_tests.sh

# Check health
curl http://localhost:8000/health

# Get statistics
curl http://localhost:8000/tools/rag_stats

# Index documents
curl -X POST http://localhost:8000/tools/rag_index_directory \
  -H "Content-Type: application/json" \
  -d '{"directory_path": "data/documents", "recursive": true}'
```

## Performance

| Metric | Value |
|--------|-------|
| Document indexing | 0.37s for 196K lines |
| Query response | < 5 seconds |
| Concurrent queries | 10+ simultaneous |
| Vector search | < 1 second |

## Support

- **Documentation**: See [`docs/docs/rag/`](../docs/docs/rag/)
- **Issues**: [GitHub Issues](https://github.com/ibm/a2a-rag-agent/issues)
- **Troubleshooting**: See [Troubleshooting Guide](../docs/docs/rag/troubleshooting.md)

## Built With

This project was created using **[IBM Bob](https://github.com/ibm/bob)** - an AI-powered development assistant that helps build production-ready applications with best practices and comprehensive documentation.

## License

Apache 2.0

---

**Note**: This README provides a quick overview. For comprehensive documentation, see the [MkDocs site](https://binnes.github.io/a2a/).