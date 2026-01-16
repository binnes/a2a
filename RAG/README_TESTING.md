# RAG Testing Guide

## Overview

This document describes the simplified testing infrastructure for the RAG (Retrieval-Augmented Generation) system.

## Test Structure

```
RAG/
├── scripts/
│   ├── start_services.sh    # Start Milvus and MCP server
│   ├── stop_services.sh     # Stop all services
│   └── run_tests.sh         # Run all tests with setup
├── tests/
│   ├── test_document_processor.py  # Unit tests for document processing
│   ├── test_e2e_shakespeare.py     # End-to-end tests with Shakespeare data
│   └── test_summary.py             # Configuration validation tests
└── pytest.ini               # Pytest configuration
```

## Quick Start

### 1. Start Services

```bash
./scripts/start_services.sh
```

This will:
- Start Milvus vector database (via podman-compose)
- Start MCP server on port 8000
- Wait for services to be ready
- Verify health endpoints

### 2. Run Tests

```bash
./scripts/run_tests.sh
```

This will:
- Activate virtual environment
- Check that services are running
- Clear Milvus database
- Run all tests with pytest
- Display results

### 3. Stop Services

```bash
./scripts/stop_services.sh
```

This will:
- Stop MCP server
- Stop Milvus (via podman-compose)

## Test Categories

### Unit Tests (test_document_processor.py)

Tests for document processing functionality:
- Text chunking with word limits
- Chunk overlap handling
- Metadata extraction
- Error handling
- Edge cases (empty documents, special characters)

**Run only unit tests:**
```bash
pytest tests/test_document_processor.py -v
```

### Configuration Tests (test_summary.py)

Validates system configuration:
- Embedding model settings
- Chunk size configuration

**Run only config tests:**
```bash
pytest tests/test_summary.py -v
```

### End-to-End Tests (test_e2e_shakespeare.py)

Comprehensive tests using Shakespeare's complete works (196K lines):
- Document ingestion pipeline
- Vector search functionality
- Query processing
- Context retrieval
- Answer generation
- Multi-query handling

**Run only E2E tests:**
```bash
pytest tests/test_e2e_shakespeare.py -v
```

## Test Markers

Tests are organized with pytest markers:

- `@pytest.mark.unit` - Fast unit tests
- `@pytest.mark.integration` - Integration tests requiring services
- `@pytest.mark.e2e` - End-to-end tests with full pipeline
- `@pytest.mark.slow` - Tests that take longer to run

**Run specific markers:**
```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Skip slow tests
pytest -m "not slow"
```

## Configuration

### Environment Variables

Key settings in `config/.env`:

```bash
# Embedding Model
WATSONX_EMBEDDING_MODEL=granite-embedding-278m-multilingual
EMBEDDING_DIMENSION=768

# Chunking
CHUNK_SIZE_WORDS=200
CHUNK_OVERLAP_WORDS=30

# Milvus
MILVUS_HOST=localhost
MILVUS_PORT=19530
MILVUS_COLLECTION=rag_documents

# MCP Server
MCP_SERVER_URL=http://localhost:8000
```

### Pytest Configuration

Settings in `pytest.ini`:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    slow: Slow running tests
log_cli = true
log_cli_level = INFO
```

## Test Data

### Shakespeare Dataset

Location: `data/reference/complete works of Shakespear.txt`
- Size: 196,000+ lines
- Content: Complete works of Shakespeare
- Used for: End-to-end testing of document ingestion and retrieval

### Sample Documents

Location: `data/documents/`
- Small test documents for unit tests
- Various formats and edge cases

## Troubleshooting

### Services Not Starting

**Problem:** Milvus fails to start
```bash
# Check podman status
podman ps -a

# View Milvus logs
cd deployment && podman-compose logs
```

**Problem:** MCP server fails to start
```bash
# Check if port 8000 is in use
lsof -i :8000

# View server logs
tail -f /tmp/mcp_server.log
```

### Tests Failing

**Problem:** Embedding dimension mismatch
- Verify `EMBEDDING_DIMENSION` matches model output (768 for granite-embedding-278m-multilingual)
- Clear Milvus collection and recreate

**Problem:** Token limit exceeded
- Reduce `CHUNK_SIZE_WORDS` in config/.env
- Current recommended: 200 words (stays under 512 token limit)

**Problem:** Connection errors
- Ensure services are running: `curl http://localhost:8000/health`
- Check Milvus: `curl http://localhost:9091/healthz`

### Clearing Test Data

```bash
# Clear Milvus database
python -c "
from services.milvus_client import MilvusClient
from config.settings import settings
client = MilvusClient(settings)
client.clear_collection()
"
```

## CI/CD Integration

For automated testing:

```bash
#!/bin/bash
# CI test script

# Start services
./scripts/start_services.sh

# Wait for services
sleep 10

# Run tests
./scripts/run_tests.sh
TEST_EXIT=$?

# Stop services
./scripts/stop_services.sh

exit $TEST_EXIT
```

## Performance Benchmarks

Expected test execution times:

- Unit tests: < 5 seconds
- Configuration tests: < 2 seconds
- E2E tests (Shakespeare): 2-5 minutes
  - Document ingestion: 1-3 minutes
  - Query tests: 30-60 seconds

## Additional Resources

- [TEST_SPECIFICATION.md](TEST_SPECIFICATION.md) - Detailed test specifications
- [TEST_RESULTS.md](TEST_RESULTS.md) - Latest test execution results
- [FINAL_TEST_SUMMARY.md](FINAL_TEST_SUMMARY.md) - Executive summary
- [API_DOCUMENTATION.md](API_DOCUMENTATION.md) - API reference
- [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) - Implementation status

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review test logs in pytest output
3. Check service logs (/tmp/mcp_server.log, podman-compose logs)
4. Verify configuration in config/.env