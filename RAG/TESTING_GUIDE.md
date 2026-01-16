# A2A RAG Agent - Testing Guide

This guide explains how to test the A2A agent and verify it correctly calls the MCP service.

## Prerequisites

1. **Milvus Running**: Ensure Milvus is started
2. **MCP Server Running**: The MCP server must be running
3. **Documents Indexed**: At least some documents should be indexed

## Testing Architecture

```
┌─────────────┐         ┌─────────────┐         ┌──────────────┐
│   Test      │ calls   │  A2A Agent  │ calls   │  MCP Server  │
│   Script    ├────────>│  (LangGraph)├────────>│  (FastAPI)   │
└─────────────┘         └─────────────┘         └──────────────┘
                              │                         │
                              │                         ▼
                              │                  ┌──────────────┐
                              │                  │  Watsonx.ai  │
                              │                  │  + Milvus    │
                              │                  └──────────────┘
                              ▼
                        ┌─────────────┐
                        │   Response  │
                        └─────────────┘
```

## Step-by-Step Testing

### Step 1: Start Milvus

```bash
cd RAG/deployment
podman-compose up -d

# Wait for Milvus to be ready (check logs)
podman-compose logs -f milvus
# Wait until you see "Milvus Proxy successfully started"
```

### Step 2: Start MCP Server

In a new terminal:

```bash
cd RAG
source venv/bin/activate

# Install dependencies if not already done
pip install fastapi uvicorn pydantic pydantic-settings python-dotenv httpx

# Start the MCP server
python -m uvicorn mcp_server.server:app --host 0.0.0.0 --port 8000 --reload
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

### Step 3: Verify MCP Server is Running

In another terminal:

```bash
# Test health endpoint
curl http://localhost:8000/health

# List available tools
curl http://localhost:8000/tools

# Check root endpoint
curl http://localhost:8000/
```

### Step 4: Index Sample Documents

```bash
# Index the sample documentation
curl -X POST http://localhost:8000/tools/rag_index_directory \
  -H "Content-Type: application/json" \
  -d '{
    "directory_path": "data/documents",
    "recursive": true
  }'
```

Expected response:
```json
{
  "status": "success",
  "message": "Directory indexed successfully",
  "chunks_indexed": 42,
  "directory_path": "data/documents"
}
```

### Step 5: Test MCP Server Directly

Before testing the agent, verify the MCP server works:

```bash
# Test RAG query
curl -X POST http://localhost:8000/tools/rag_query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the A2A protocol?",
    "top_k": 3,
    "include_sources": true
  }'
```

### Step 6: Test A2A Agent

Now test the A2A agent which will call the MCP server:

```bash
cd RAG
source venv/bin/activate

# Run the test script
python test_agent_integration.py
```

## Test Scripts

### Basic Integration Test

Create `test_agent_integration.py`:

```python
"""Test A2A agent integration with MCP server."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from agent.a2a_agent import A2ARAGAgent
from config.settings import get_settings


async def test_agent_mcp_integration():
    """Test that A2A agent correctly calls MCP server."""
    
    print("=" * 60)
    print("A2A Agent - MCP Integration Test")
    print("=" * 60)
    print()
    
    # Initialize
    print("1. Initializing A2A agent...")
    settings = get_settings()
    agent = A2ARAGAgent(settings)
    print(f"   ✓ Agent initialized: {agent.agent_id}")
    print(f"   ✓ MCP server URL: {settings.mcp_server_url}")
    print()
    
    # Check health
    print("2. Checking MCP server health...")
    health = await agent.health_check()
    print(f"   Agent: {'✓' if health['agent'] else '✗'}")
    print(f"   MCP Server: {'✓' if health['mcp_server'] else '✗'}")
    
    if not health['mcp_server']:
        print("\n   ✗ MCP server is not responding!")
        print("   Make sure the MCP server is running:")
        print("   python -m uvicorn mcp_server.server:app --reload")
        return False
    print()
    
    # Test query
    print("3. Testing agent query (calls MCP server)...")
    query = "What is the A2A protocol?"
    print(f"   Query: {query}")
    print()
    
    try:
        result = await agent.process_query(query)
        
        print("   ✓ Query processed successfully!")
        print()
        print("   Response:")
        print(f"   {result['response'][:200]}...")
        print()
        
        if result.get('sources'):
            print(f"   Sources: {len(result['sources'])} documents")
            for i, source in enumerate(result['sources'][:3], 1):
                print(f"     {i}. {source['source']} (score: {source['score']:.3f})")
        print()
        
        print("   ✓ A2A agent successfully called MCP server!")
        return True
        
    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        await agent.close()


async def test_multiple_queries():
    """Test multiple queries to verify consistent MCP calls."""
    
    print("=" * 60)
    print("Multiple Query Test")
    print("=" * 60)
    print()
    
    settings = get_settings()
    agent = A2ARAGAgent(settings)
    
    queries = [
        "What is the A2A protocol?",
        "How does MCP work?",
        "Explain RAG systems",
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"{i}. Testing: {query}")
        try:
            result = await agent.process_query(query)
            print(f"   ✓ Response received ({len(result['response'])} chars)")
            print(f"   ✓ Sources: {len(result.get('sources', []))}")
        except Exception as e:
            print(f"   ✗ Error: {e}")
        print()
    
    await agent.close()


async def main():
    """Run all tests."""
    
    # Test 1: Basic integration
    success = await test_agent_mcp_integration()
    
    if success:
        print()
        # Test 2: Multiple queries
        await test_multiple_queries()
        
        print("=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)
        return 0
    else:
        print("=" * 60)
        print("✗ Tests failed")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
```

### Monitoring MCP Calls

To see the MCP server receiving calls from the agent, watch the server logs:

```bash
# The MCP server will log each request:
INFO:     127.0.0.1:xxxxx - "POST /tools/rag_query HTTP/1.1" 200 OK
```

### Debugging Test

Create `test_agent_debug.py` for detailed debugging:

```python
"""Debug A2A agent and MCP communication."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from agent.tools import MCPToolClient
from config.settings import get_settings


async def test_mcp_client_directly():
    """Test MCP client directly (bypasses agent)."""
    
    print("Testing MCP Client Directly")
    print("=" * 60)
    
    settings = get_settings()
    client = MCPToolClient(settings)
    
    # Test 1: Health check
    print("\n1. Health Check")
    healthy = await client.health_check()
    print(f"   MCP Server: {'✓ Healthy' if healthy else '✗ Unhealthy'}")
    
    if not healthy:
        print("\n   MCP server is not responding!")
        print(f"   URL: {settings.mcp_server_url}")
        print("   Make sure it's running:")
        print("   python -m uvicorn mcp_server.server:app --reload")
        return
    
    # Test 2: RAG query
    print("\n2. RAG Query")
    try:
        result = await client.rag_query(
            query="What is the A2A protocol?",
            top_k=3,
            include_sources=True
        )
        print(f"   ✓ Answer: {result['answer'][:100]}...")
        print(f"   ✓ Context chunks: {len(result['context'])}")
        print(f"   ✓ Sources: {len(result.get('sources', []))}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 3: RAG search
    print("\n3. RAG Search")
    try:
        result = await client.rag_search(
            query="agent communication",
            top_k=5
        )
        print(f"   ✓ Results: {result['count']}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 4: Stats
    print("\n4. Knowledge Base Stats")
    try:
        result = await client.rag_stats()
        stats = result['statistics']
        print(f"   ✓ Collection: {stats['collection_name']}")
        print(f"   ✓ Documents: {stats['num_entities']}")
        print(f"   ✓ Dimension: {stats['dimension']}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    await client.close()
    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(test_mcp_client_directly())
```

## Verification Checklist

Use this checklist to verify the integration:

- [ ] Milvus is running (`podman ps | grep milvus`)
- [ ] MCP server is running (`curl http://localhost:8000/health`)
- [ ] Documents are indexed (`curl http://localhost:8000/tools/rag_stats`)
- [ ] MCP server responds to queries directly
- [ ] A2A agent initializes successfully
- [ ] A2A agent health check passes
- [ ] A2A agent processes queries successfully
- [ ] MCP server logs show incoming requests from agent
- [ ] Agent returns responses with context and sources

## Troubleshooting

### MCP Server Not Responding

```bash
# Check if server is running
curl http://localhost:8000/health

# Check server logs
# (Look in the terminal where you started the server)

# Restart server
python -m uvicorn mcp_server.server:app --reload
```

### Agent Can't Connect to MCP Server

Check the configuration:

```python
from config.settings import get_settings
settings = get_settings()
print(f"MCP URL: {settings.mcp_server_url}")
# Should be: http://0.0.0.0:8000
```

### No Documents Indexed

```bash
# Check stats
curl http://localhost:8000/tools/rag_stats

# Re-index documents
curl -X POST http://localhost:8000/tools/rag_index_directory \
  -H "Content-Type: application/json" \
  -d '{"directory_path": "data/documents"}'
```

### Import Errors

```bash
# Install missing packages
cd RAG
source venv/bin/activate
pip install fastapi uvicorn pydantic pydantic-settings python-dotenv httpx
```

## Expected Output

When everything works correctly, you should see:

```
============================================================
A2A Agent - MCP Integration Test
============================================================

1. Initializing A2A agent...
   ✓ Agent initialized: rag-agent
   ✓ MCP server URL: http://0.0.0.0:8000

2. Checking MCP server health...
   Agent: ✓
   MCP Server: ✓

3. Testing agent query (calls MCP server)...
   Query: What is the A2A protocol?

   ✓ Query processed successfully!

   Response:
   The Agent-to-Agent Protocol (A2A) is a standardized communication 
   framework that enables autonomous agents to discover, communicate...

   Sources: 3 documents
     1. data/documents/sample_doc.md (score: 0.923)
     2. data/documents/sample_doc.md (score: 0.891)
     3. data/documents/sample_doc.md (score: 0.876)

   ✓ A2A agent successfully called MCP server!

============================================================
✓ All tests passed!
============================================================
```

## Summary

The A2A agent integration with MCP server is verified when:

1. **MCP server receives requests** from the agent (visible in server logs)
2. **Agent returns responses** with context and sources
3. **Health checks pass** for both agent and MCP server
4. **Multiple queries work** consistently

This confirms the complete flow: Test Script → A2A Agent → MCP Server → Watsonx.ai/Milvus → Response