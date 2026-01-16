# A2A RAG System - Comprehensive Test Specification

## Overview

This document defines systematic tests to verify the functionality of the A2A RAG implementation, including all components: document processing, vector storage, embeddings, LLM generation, MCP server, and A2A agent orchestration.

## Test Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Test Layers                              │
├─────────────────────────────────────────────────────────────┤
│ 1. Unit Tests        - Individual component testing         │
│ 2. Integration Tests - Component interaction testing        │
│ 3. End-to-End Tests  - Full pipeline testing               │
│ 4. Performance Tests - Load and scalability testing         │
│ 5. A2A Protocol Tests- Protocol compliance testing          │
└─────────────────────────────────────────────────────────────┘
```

---

## 1. Unit Tests

### 1.1 Document Processor Tests (`services/document_processor.py`)

#### Test Suite: `test_document_processor.py`

**Test 1.1.1: Text File Processing**
- **Objective**: Verify text file extraction
- **Input**: `data/reference/complete works of Shakespear.txt`
- **Expected Output**: 
  - Text extracted successfully
  - No errors during processing
  - Text length > 0
- **Assertions**:
  ```python
  assert len(text) > 0
  assert isinstance(text, str)
  assert "Shakespeare" in text or "SHAKESPEARE" in text
  ```

**Test 1.1.2: Text Chunking**
- **Objective**: Verify text is chunked correctly with overlap
- **Input**: Sample text from Shakespeare file
- **Expected Output**:
  - Chunks created with configured size
  - Overlap between consecutive chunks
  - All chunks have text content
- **Assertions**:
  ```python
  assert len(chunks) > 0
  assert all(len(chunk.split()) <= chunk_size for chunk in chunks)
  assert chunks[0] != chunks[1]  # Different chunks
  # Verify overlap exists
  ```

**Test 1.1.3: Chunk Metadata Generation**
- **Objective**: Verify chunk metadata is correct
- **Input**: Processed Shakespeare file
- **Expected Output**:
  - Each chunk has unique ID
  - Source path is correct
  - Chunk index is sequential
  - Total chunks count is accurate
- **Assertions**:
  ```python
  assert all('id' in chunk for chunk in chunks)
  assert all('source' in chunk for chunk in chunks)
  assert all('chunk_index' in chunk for chunk in chunks)
  assert len(set(c['id'] for c in chunks)) == len(chunks)  # Unique IDs
  ```

**Test 1.1.4: Large File Handling**
- **Objective**: Verify processor handles large files (196K lines)
- **Input**: Complete Shakespeare works file
- **Expected Output**:
  - File processed without memory errors
  - Reasonable number of chunks created
  - Processing completes within timeout
- **Assertions**:
  ```python
  assert processing_time < 300  # 5 minutes max
  assert len(chunks) > 100  # Reasonable chunk count
  assert len(chunks) < 100000  # Not excessive
  ```

**Test 1.1.5: Text Cleaning**
- **Objective**: Verify text cleaning removes unwanted characters
- **Input**: Text with special characters, extra whitespace
- **Expected Output**:
  - Excessive whitespace removed
  - Special characters handled
  - Punctuation preserved
- **Assertions**:
  ```python
  assert "  " not in cleaned_text  # No double spaces
  assert cleaned_text.strip() == cleaned_text  # No leading/trailing
  ```

**Test 1.1.6: Unsupported File Type**
- **Objective**: Verify error handling for unsupported files
- **Input**: File with unsupported extension
- **Expected Output**: ValueError raised
- **Assertions**:
  ```python
  with pytest.raises(ValueError, match="Unsupported file type"):
      processor.process_file("test.xyz")
  ```

**Test 1.1.7: Missing File**
- **Objective**: Verify error handling for missing files
- **Input**: Non-existent file path
- **Expected Output**: FileNotFoundError raised
- **Assertions**:
  ```python
  with pytest.raises(FileNotFoundError):
      processor.process_file("nonexistent.txt")
  ```

---

### 1.2 Milvus Client Tests (`services/milvus_client.py`)

#### Test Suite: `test_milvus_client.py`

**Test 1.2.1: Connection Establishment**
- **Objective**: Verify Milvus connection
- **Expected Output**: Connection successful
- **Assertions**:
  ```python
  assert client.collection is not None
  assert client.health_check() == True
  ```

**Test 1.2.2: Collection Creation**
- **Objective**: Verify collection is created with correct schema
- **Expected Output**:
  - Collection exists
  - Schema has required fields
  - Index created on vector field
- **Assertions**:
  ```python
  assert utility.has_collection(collection_name)
  assert 'vector' in collection.schema.fields
  assert collection.has_index()
  ```

**Test 1.2.3: Document Insertion**
- **Objective**: Verify documents can be inserted
- **Input**: Sample document chunks with embeddings
- **Expected Output**:
  - All documents inserted
  - No errors
  - Entity count increases
- **Assertions**:
  ```python
  initial_count = collection.num_entities
  client.insert(ids, texts, vectors, sources)
  assert collection.num_entities == initial_count + len(ids)
  ```

**Test 1.2.4: Vector Search**
- **Objective**: Verify semantic search works
- **Input**: Query vector
- **Expected Output**:
  - Results returned
  - Results sorted by score
  - Results above threshold
- **Assertions**:
  ```python
  results = client.search(query_vector, top_k=5)
  assert len(results) <= 5
  assert all(r['score'] >= threshold for r in results)
  assert results[0]['score'] >= results[-1]['score']  # Sorted
  ```

**Test 1.2.5: Document Deletion**
- **Objective**: Verify documents can be deleted
- **Input**: List of document IDs
- **Expected Output**:
  - Documents removed
  - Entity count decreases
- **Assertions**:
  ```python
  initial_count = collection.num_entities
  client.delete(ids_to_delete)
  assert collection.num_entities == initial_count - len(ids_to_delete)
  ```

**Test 1.2.6: Collection Statistics**
- **Objective**: Verify stats retrieval
- **Expected Output**:
  - Stats contain entity count
  - Stats contain collection name
  - Stats contain dimension
- **Assertions**:
  ```python
  stats = client.get_stats()
  assert 'num_entities' in stats
  assert 'collection_name' in stats
  assert stats['dimension'] == expected_dimension
  ```

**Test 1.2.7: Collection Clear**
- **Objective**: Verify collection can be cleared
- **Expected Output**:
  - All entities removed
  - Collection still exists
  - Collection can be used again
- **Assertions**:
  ```python
  client.clear_collection()
  assert collection.num_entities == 0
  assert utility.has_collection(collection_name)
  ```

---

### 1.3 Watsonx Client Tests (`services/watsonx_client.py`)

#### Test Suite: `test_watsonx_client.py`

**Test 1.3.1: Client Initialization**
- **Objective**: Verify Watsonx client initializes
- **Expected Output**:
  - API client created
  - Embeddings model loaded
  - LLM model loaded
- **Assertions**:
  ```python
  assert client._api_client is not None
  assert client._embeddings is not None
  assert client._llm is not None
  ```

**Test 1.3.2: Single Text Embedding**
- **Objective**: Verify single text embedding generation
- **Input**: "Romeo and Juliet"
- **Expected Output**:
  - Embedding vector returned
  - Correct dimension
  - All values are floats
- **Assertions**:
  ```python
  embedding = client.generate_embedding(text)
  assert len(embedding) == expected_dimension
  assert all(isinstance(v, float) for v in embedding)
  ```

**Test 1.3.3: Batch Embedding Generation**
- **Objective**: Verify batch embedding generation
- **Input**: List of 10 text chunks
- **Expected Output**:
  - All embeddings generated
  - Correct dimensions
  - Different embeddings for different texts
- **Assertions**:
  ```python
  embeddings = client.generate_embeddings(texts)
  assert len(embeddings) == len(texts)
  assert all(len(e) == expected_dimension for e in embeddings)
  assert embeddings[0] != embeddings[1]  # Different
  ```

**Test 1.3.4: Text Generation**
- **Objective**: Verify LLM text generation
- **Input**: Prompt about Shakespeare
- **Expected Output**:
  - Text generated
  - Non-empty response
  - Reasonable length
- **Assertions**:
  ```python
  response = client.generate_text(prompt)
  assert len(response) > 0
  assert len(response) < max_tokens * 2  # Reasonable length
  ```

**Test 1.3.5: Chat Response Generation**
- **Objective**: Verify chat-style generation
- **Input**: List of messages
- **Expected Output**:
  - Response generated
  - Contextually relevant
- **Assertions**:
  ```python
  response = client.generate_chat_response(messages)
  assert len(response) > 0
  assert isinstance(response, str)
  ```

**Test 1.3.6: Retry Mechanism**
- **Objective**: Verify retry on transient failures
- **Input**: Simulate API failure
- **Expected Output**:
  - Retries attempted
  - Eventually succeeds or fails gracefully
- **Assertions**:
  ```python
  # Mock API to fail twice then succeed
  assert retry_count == 2
  assert result is not None
  ```

**Test 1.3.7: Health Check**
- **Objective**: Verify health check works
- **Expected Output**: True if healthy
- **Assertions**:
  ```python
  assert client.health_check() == True
  ```

---

### 1.4 MCP Tool Client Tests (`agent/tools.py`)

#### Test Suite: `test_mcp_tools.py`

**Test 1.4.1: RAG Query Tool**
- **Objective**: Verify RAG query tool calls MCP server
- **Input**: Query string
- **Expected Output**:
  - HTTP POST to correct endpoint
  - Response contains answer, context, sources
- **Assertions**:
  ```python
  result = await client.rag_query(query)
  assert 'answer' in result
  assert 'context' in result
  assert 'sources' in result
  ```

**Test 1.4.2: RAG Search Tool**
- **Objective**: Verify search tool works
- **Input**: Search query
- **Expected Output**:
  - Results returned
  - No LLM generation
- **Assertions**:
  ```python
  result = await client.rag_search(query)
  assert 'results' in result
  assert 'count' in result
  ```

**Test 1.4.3: RAG Index Tool**
- **Objective**: Verify indexing tool works
- **Input**: File path
- **Expected Output**:
  - Success status
  - Chunks indexed count
- **Assertions**:
  ```python
  result = await client.rag_index(file_path)
  assert result['status'] == 'success'
  assert result['chunks_indexed'] > 0
  ```

**Test 1.4.4: RAG Stats Tool**
- **Objective**: Verify stats tool works
- **Expected Output**: Statistics returned
- **Assertions**:
  ```python
  result = await client.rag_stats()
  assert 'statistics' in result
  ```

**Test 1.4.5: Health Check**
- **Objective**: Verify MCP server health check
- **Expected Output**: True if server is up
- **Assertions**:
  ```python
  assert await client.health_check() == True
  ```

**Test 1.4.6: Connection Timeout**
- **Objective**: Verify timeout handling
- **Input**: Slow/unresponsive server
- **Expected Output**: Timeout exception
- **Assertions**:
  ```python
  with pytest.raises(httpx.TimeoutException):
      await client.rag_query(query)
  ```

**Test 1.4.7: Server Error Handling**
- **Objective**: Verify 500 error handling
- **Expected Output**: Exception raised with error details
- **Assertions**:
  ```python
  with pytest.raises(Exception):
      await client.rag_query(invalid_query)
  ```

---

## 2. Integration Tests

### 2.1 Document Processing Pipeline Tests

#### Test Suite: `test_document_pipeline.py`

**Test 2.1.1: End-to-End Document Indexing**
- **Objective**: Verify complete document indexing flow
- **Input**: Shakespeare complete works file
- **Steps**:
  1. Process document into chunks
  2. Generate embeddings for chunks
  3. Insert into Milvus
- **Expected Output**:
  - All chunks indexed
  - Searchable in Milvus
- **Assertions**:
  ```python
  chunks = processor.process_file(file_path)
  embeddings = watsonx.generate_embeddings([c['text'] for c in chunks])
  milvus.insert(ids, texts, embeddings, sources)
  assert milvus.collection.num_entities > 0
  ```

**Test 2.1.2: Query After Indexing**
- **Objective**: Verify documents are searchable after indexing
- **Input**: Query about Shakespeare
- **Expected Output**:
  - Relevant results returned
  - Results from indexed document
- **Assertions**:
  ```python
  query_embedding = watsonx.generate_embedding(query)
  results = milvus.search(query_embedding)
  assert len(results) > 0
  assert any('Shakespeare' in r['source'] for r in results)
  ```

---

### 2.2 MCP Server Integration Tests

#### Test Suite: `test_mcp_server_integration.py`

**Test 2.2.1: Server Startup**
- **Objective**: Verify MCP server starts correctly
- **Expected Output**:
  - Server running on configured port
  - Health endpoint responds
- **Assertions**:
  ```python
  response = requests.get(f"{base_url}/health")
  assert response.status_code == 200
  ```

**Test 2.2.2: RAG Query Endpoint**
- **Objective**: Verify query endpoint works end-to-end
- **Input**: Query about Shakespeare
- **Expected Output**:
  - Answer generated
  - Context retrieved
  - Sources included
- **Assertions**:
  ```python
  response = requests.post(f"{base_url}/tools/rag_query", json=payload)
  assert response.status_code == 200
  data = response.json()
  assert 'answer' in data
  assert len(data['context']) > 0
  ```

**Test 2.2.3: Index Document Endpoint**
- **Objective**: Verify indexing endpoint works
- **Input**: Shakespeare file path
- **Expected Output**:
  - Document indexed
  - Success status
- **Assertions**:
  ```python
  response = requests.post(f"{base_url}/tools/rag_index", json=payload)
  assert response.status_code == 200
  assert response.json()['status'] == 'success'
  ```

**Test 2.2.4: Search Endpoint**
- **Objective**: Verify search endpoint works
- **Input**: Search query
- **Expected Output**: Search results
- **Assertions**:
  ```python
  response = requests.post(f"{base_url}/tools/rag_search", json=payload)
  assert response.status_code == 200
  assert 'results' in response.json()
  ```

**Test 2.2.5: Stats Endpoint**
- **Objective**: Verify stats endpoint works
- **Expected Output**: Collection statistics
- **Assertions**:
  ```python
  response = requests.get(f"{base_url}/tools/rag_stats")
  assert response.status_code == 200
  assert 'statistics' in response.json()
  ```

**Test 2.2.6: Clear Endpoint**
- **Objective**: Verify clear endpoint works
- **Expected Output**:
  - Collection cleared
  - Success status
- **Assertions**:
  ```python
  response = requests.delete(f"{base_url}/tools/rag_clear")
  assert response.status_code == 200
  ```

---

### 2.3 A2A Agent Integration Tests

#### Test Suite: `test_a2a_agent_integration.py`

**Test 2.3.1: Agent Initialization**
- **Objective**: Verify agent initializes correctly
- **Expected Output**:
  - Agent created
  - MCP client initialized
  - Graph compiled
- **Assertions**:
  ```python
  agent = A2ARAGAgent(settings)
  assert agent.agent_id is not None
  assert agent.mcp_client is not None
  assert agent.graph is not None
  ```

**Test 2.3.2: Agent Query Processing**
- **Objective**: Verify agent processes queries through workflow
- **Input**: Query about Shakespeare
- **Expected Output**:
  - Query processed through all nodes
  - Response generated
  - Sources included
- **Assertions**:
  ```python
  result = await agent.process_query(query)
  assert 'response' in result
  assert 'sources' in result
  assert len(result['sources']) > 0
  ```

**Test 2.3.3: Agent-MCP Communication**
- **Objective**: Verify agent calls MCP server correctly
- **Input**: Query
- **Expected Output**:
  - HTTP request to MCP server
  - Response received
- **Assertions**:
  ```python
  # Monitor MCP server logs
  result = await agent.process_query(query)
  assert mcp_server_received_request == True
  ```

**Test 2.3.4: A2A Message Handling**
- **Objective**: Verify agent handles A2A protocol messages
- **Input**: A2A query message
- **Expected Output**:
  - Message processed
  - A2A response message returned
- **Assertions**:
  ```python
  response_msg = await agent.handle_a2a_message(query_msg)
  assert response_msg['message_type'] == 'response'
  assert 'content' in response_msg
  ```

**Test 2.3.5: Error Handling in Workflow**
- **Objective**: Verify error handling in agent workflow
- **Input**: Invalid query or MCP server down
- **Expected Output**:
  - Error caught
  - Error message returned
- **Assertions**:
  ```python
  result = await agent.process_query(invalid_query)
  assert 'error' in result or 'error' in result['response']
  ```

**Test 2.3.6: Agent Health Check**
- **Objective**: Verify agent health check
- **Expected Output**:
  - Agent status
  - MCP server status
- **Assertions**:
  ```python
  health = await agent.health_check()
  assert 'agent' in health
  assert 'mcp_server' in health
  ```

**Test 2.3.7: Agent Capabilities**
- **Objective**: Verify agent reports capabilities correctly
- **Expected Output**: Capabilities dictionary
- **Assertions**:
  ```python
  caps = agent.get_capabilities()
  assert 'agent_id' in caps
  assert 'capabilities' in caps
  assert 'rag_query' in caps['capabilities']
  ```

---

## 3. End-to-End Tests

### 3.1 Complete RAG Pipeline Test

#### Test Suite: `test_e2e_rag_pipeline.py`

**Test 3.1.1: Shakespeare Knowledge Base Test**
- **Objective**: Verify complete RAG pipeline with Shakespeare works
- **Steps**:
  1. Clear existing knowledge base
  2. Index Shakespeare complete works
  3. Query about specific plays/characters
  4. Verify accurate responses
- **Test Queries**:
  - "Who is Romeo?"
  - "What happens in Hamlet?"
  - "Describe Macbeth's character"
  - "What is the theme of King Lear?"
- **Expected Output**:
  - Relevant answers for each query
  - Sources from Shakespeare file
  - High relevance scores
- **Assertions**:
  ```python
  for query in test_queries:
      result = await agent.process_query(query)
      assert len(result['response']) > 50  # Substantial answer
      assert any('Shakespeare' in s['source'] for s in result['sources'])
      assert all(s['score'] > 0.7 for s in result['sources'])
  ```

**Test 3.1.2: Multi-Turn Conversation**
- **Objective**: Verify agent handles conversation context
- **Input**: Series of related queries
- **Expected Output**:
  - Each query answered
  - Context maintained
- **Assertions**:
  ```python
  queries = [
      "Who wrote Romeo and Juliet?",
      "What other plays did he write?",
      "Tell me about Hamlet"
  ]
  for query in queries:
      result = await agent.process_query(query)
      assert result['response'] is not None
  ```

---

## 4. Performance Tests

### 4.1 Load and Scalability Tests

#### Test Suite: `test_performance.py`

**Test 4.1.1: Large Document Indexing Performance**
- **Objective**: Measure indexing performance for large file
- **Input**: Shakespeare complete works (196K lines)
- **Metrics**:
  - Indexing time
  - Memory usage
  - Chunks per second
- **Expected Output**:
  - Indexing completes < 5 minutes
  - Memory < 2GB
  - No crashes
- **Assertions**:
  ```python
  start_time = time.time()
  result = await rag_tools.index_document(file_path)
  duration = time.time() - start_time
  assert duration < 300  # 5 minutes
  assert result['chunks_indexed'] > 1000
  ```

**Test 4.1.2: Concurrent Query Performance**
- **Objective**: Measure performance under concurrent load
- **Input**: 10 concurrent queries
- **Metrics**:
  - Average response time
  - Throughput (queries/second)
  - Error rate
- **Expected Output**:
  - All queries succeed
  - Average response < 5 seconds
  - No errors
- **Assertions**:
  ```python
  results = await asyncio.gather(*[agent.process_query(q) for q in queries])
  assert all(r['response'] is not None for r in results)
  assert avg_response_time < 5.0
  ```

**Test 4.1.3: Search Performance**
- **Objective**: Measure search speed
- **Input**: 100 search queries
- **Metrics**:
  - Average search time
  - P95 latency
- **Expected Output**:
  - Average < 1 second
  - P95 < 2 seconds
- **Assertions**:
  ```python
  times = [measure_search_time(q) for q in queries]
  assert statistics.mean(times) < 1.0
  assert statistics.quantiles(times, n=20)[18] < 2.0  # P95
  ```

**Test 4.1.4: Memory Leak Test**
- **Objective**: Verify no memory leaks over time
- **Input**: 1000 queries
- **Metrics**: Memory usage over time
- **Expected Output**: Memory stable
- **Assertions**:
  ```python
  initial_memory = get_memory_usage()
  for _ in range(1000):
      await agent.process_query(random.choice(queries))
  final_memory = get_memory_usage()
  assert final_memory < initial_memory * 1.5  # Max 50% increase
  ```

---

## 5. A2A Protocol Compliance Tests

### 5.1 Protocol Format Tests

#### Test Suite: `test_a2a_protocol.py`

**Test 5.1.1: Message Format Validation**
- **Objective**: Verify A2A messages follow protocol
- **Expected Output**:
  - Required fields present
  - Correct types
  - Valid timestamps
- **Assertions**:
  ```python
  msg = agent.create_a2a_message(content)
  assert 'agent_id' in msg
  assert 'message_type' in msg
  assert 'content' in msg
  assert 'timestamp' in msg
  assert isinstance(msg['timestamp'], str)
  ```

**Test 5.1.2: Query Message Handling**
- **Objective**: Verify query messages processed correctly
- **Input**: A2A query message
- **Expected Output**: A2A response message
- **Assertions**:
  ```python
  response = await agent.handle_a2a_message(query_msg)
  assert response['message_type'] == 'response'
  assert response['correlation_id'] == query_msg['correlation_id']
  ```

**Test 5.1.3: Error Message Format**
- **Objective**: Verify error messages follow protocol
- **Input**: Invalid request
- **Expected Output**: A2A error message
- **Assertions**:
  ```python
  response = await agent.handle_a2a_message(invalid_msg)
  assert response['message_type'] == 'error'
  assert 'error' in response['content']
  ```

---

## 6. Test Data

### 6.1 Primary Test Document
- **File**: `data/reference/complete works of Shakespear.txt`
- **Size**: 196,396 lines
- **Content**: Complete works of William Shakespeare
- **Use Cases**:
  - Large file processing
  - Literary knowledge base
  - Complex query testing

### 6.2 Test Queries for Shakespeare Knowledge Base

```python
SHAKESPEARE_TEST_QUERIES = [
    # Character queries
    "Who is Romeo?",
    "Describe Hamlet's character",
    "What is Lady Macbeth known for?",
    "Who is Juliet?",
    
    # Plot queries
    "What happens in Romeo and Juliet?",
    "Summarize the plot of Hamlet",
    "What is the story of Macbeth?",
    "Explain the ending of King Lear",
    
    # Theme queries
    "What are the main themes in Hamlet?",
    "What does Romeo and Juliet teach us?",
    "What is the moral of Macbeth?",
    
    # Specific scene queries
    "What happens in the balcony scene?",
    "Describe the ghost scene in Hamlet",
    "What happens to Macbeth at the end?",
    
    # Quote queries
    "What is the 'To be or not to be' speech about?",
    "Explain 'Romeo, Romeo, wherefore art thou Romeo'",
    
    # Comparative queries
    "Compare Romeo and Hamlet",
    "What do Macbeth and Hamlet have in common?",
]
```

---

## 7. Test Execution Plan

### 7.1 Test Sequence

```bash
# 1. Setup
cd RAG
source venv/bin/activate
podman-compose -f deployment/podman-compose.yml up -d

# 2. Start MCP Server
python -m uvicorn mcp_server.server:app --host 0.0.0.0 --port 8000 &

# 3. Run Unit Tests
pytest tests/test_document_processor.py -v
pytest tests/test_milvus_client.py -v
pytest tests/test_watsonx_client.py -v
pytest tests/test_mcp_tools.py -v

# 4. Run Integration Tests
pytest tests/test_document_pipeline.py -v
pytest tests/test_mcp_server_integration.py -v
pytest tests/test_a2a_agent_integration.py -v

# 5. Run E2E Tests
pytest tests/test_e2e_rag_pipeline.py -v

# 6. Run Performance Tests
pytest tests/test_performance.py -v

# 7. Run Protocol Tests
pytest tests/test_a2a_protocol.py -v
```

### 7.2 Continuous Integration

```yaml
# .github/workflows/test.yml
name: RAG Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Start Milvus
        run: docker-compose up -d
      - name: Run tests
        run: pytest tests/ -v --cov=. --cov-report=xml
```

---

## 8. Success Criteria

### 8.1 Unit Tests
- ✅ All unit tests pass
- ✅ Code coverage > 80%
- ✅ No critical bugs

### 8.2 Integration Tests
- ✅ All integration tests pass
- ✅ Components communicate correctly
- ✅ Error handling works

### 8.3 End-to-End Tests
- ✅ Complete pipeline works
- ✅ Shakespeare queries answered accurately
- ✅ Sources correctly attributed

### 8.4 Performance Tests
- ✅ Indexing < 5 minutes for large file
- ✅ Query response < 5 seconds
- ✅ No memory leaks
- ✅ Handles concurrent load

### 8.5 Protocol Tests
- ✅ A2A messages formatted correctly
- ✅ Protocol compliance verified
- ✅ Error handling follows protocol

---

## 9. Test Maintenance

### 9.1 Regular Updates
- Update test queries as knowledge base grows
- Add new test cases for new features
- Review and update performance benchmarks

### 9.2 Test Data Management
- Keep Shakespeare file as primary test document
- Add additional test documents as needed
- Version control test data

### 9.3 Documentation
- Keep this specification updated
- Document test failures and resolutions
- Maintain test coverage reports

---

## Appendix A: Test Utilities

```python
# test_utils.py

import time
import psutil
from typing import List, Dict, Any

def measure_execution_time(func):
    """Decorator to measure function execution time."""
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start
        return result, duration
    return wrapper

def get_memory_usage():
    """Get current memory usage in MB."""
    process = psutil.Process()
    return process.memory_info().rss / 1024 / 1024

def assert_response_quality(response: Dict[str, Any], min_length: int = 50):
    """Assert response meets quality criteria."""
    assert 'response' in response
    assert len(response['response']) >= min_length
    assert 'sources' in response
    assert len(response['sources']) > 0
    assert all(s['score'] > 0.5 for s in response['sources'])

def create_test_chunks(count: int = 10) -> List[Dict[str, Any]]:
    """Create test document chunks."""
    return [
        {
            'id': f'test_chunk_{i}',
            'text': f'Test content {i}',
            'source': 'test_file.txt',
            'chunk_index': i,
            'total_chunks': count
        }
        for i in range(count)
    ]
```

---

**Document Version**: 1.0  
**Last Updated**: 2026-01-16  
**Author**: Bob (AI Assistant)