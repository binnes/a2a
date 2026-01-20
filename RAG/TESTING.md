# A2A Agent Testing

## Overview

The refactored Shakespeare RAG A2A Agent has been updated to use the official `a2a-sdk` (v0.3.22) and follows the A2A 0.3.0 protocol specification. This document provides a quick reference for testing the agent.

## Complete Testing Plan

For the comprehensive testing plan, see: [A2A Testing Plan](../docs/docs/rag/a2a-testing-plan.md)

The complete plan covers:
- Unit tests for all components
- Integration tests for component interactions
- A2A protocol compliance tests
- End-to-end Shakespeare knowledge tests
- Deployment verification tests
- Performance benchmarks

## Quick Start Testing

### 1. Deploy the Stack

```bash
cd deployment/local
bash deploy.sh
```

This will start:
- Milvus vector database
- MCP Server
- A2A Agent
- Data loader (Shakespeare texts)

### 2. Verify Health

```bash
# Check MCP Server
curl http://localhost:8000/health

# Check A2A Agent
curl http://localhost:8001/health

# Check Agent Card
curl http://localhost:8001/.well-known/agent.json
```

### 3. Run Tests

```bash
# All tests
cd RAG
pytest tests/ -v

# Specific test categories
pytest tests/test_e2e_shakespeare.py -v
pytest tests/test_mcp_server_integration.py -v
```

## Test Categories

### Unit Tests
- `test_agent_state.py` - State definitions
- `test_mcp_tool_client.py` - MCP client
- `test_a2a_agent_workflow.py` - LangGraph workflow
- `test_agent_executor.py` - A2A executor

### Integration Tests
- `test_agent_mcp_integration.py` - Agent + MCP
- `test_executor_agent_integration.py` - Executor + Agent
- `test_langgraph_integration.py` - Complete workflow

### Protocol Tests
- `test_a2a_agent_card.py` - Agent card compliance
- `test_a2a_message_handling.py` - Message protocol
- `test_a2a_client.py` - Client SDK integration
- `test_a2a_streaming.py` - Streaming support

### E2E Tests
- `test_e2e_shakespeare_a2a.py` - Shakespeare queries via A2A
- `test_e2e_error_handling.py` - Error scenarios
- `test_e2e_performance.py` - Performance benchmarks

### Deployment Tests
- `test_deployment_build.py` - Container builds
- `test_deployment_runtime.py` - Container runtime
- `test_deployment_integration.py` - Service integration

## Sample A2A Client Test

Based on the official A2A SDK sample:

```python
import httpx
from uuid import uuid4
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import MessageSendParams, SendMessageRequest

async def test_a2a_query():
    base_url = 'http://localhost:8001'
    
    async with httpx.AsyncClient() as httpx_client:
        # Get agent card
        resolver = A2ACardResolver(
            httpx_client=httpx_client,
            base_url=base_url,
        )
        agent_card = await resolver.get_agent_card()
        
        # Create client
        client = A2AClient(
            httpx_client=httpx_client,
            agent_card=agent_card
        )
        
        # Send query
        request = SendMessageRequest(
            id=str(uuid4()),
            params=MessageSendParams(
                message={
                    "role": "user",
                    "parts": [{"kind": "text", "text": "Who is Romeo?"}],
                    "message_id": uuid4().hex,
                }
            )
        )
        
        response = await client.send_message(request)
        print(response.model_dump(mode='json', exclude_none=True))
```

## Test Priorities

### Phase 1: Critical Path (Immediate)
1. ✓ A2A agent card endpoint test
2. ✓ A2A client integration test
3. ✓ Basic Shakespeare query E2E test
4. ✓ Deployment verification test

### Phase 2: Core Functionality
5. Agent executor tests
6. LangGraph workflow tests
7. MCP tool client tests
8. Agent + MCP integration tests

### Phase 3: Comprehensive Coverage
9. Complete E2E test suite
10. Error handling tests
11. Performance tests
12. Multi-turn conversation tests

## Success Criteria

- ✓ All unit tests pass (80%+ coverage)
- ✓ All integration tests pass
- ✓ A2A protocol compliance verified
- ✓ Shakespeare queries return relevant answers
- ✓ All containers build and run successfully
- ✓ Query response time < 5 seconds (p95)

## Known Limitations

1. **Streaming**: Not implemented (`streaming=False` in agent card)
2. **Push Notifications**: Not implemented (`push_notifications=False`)
3. **Authentication**: No authentication currently
4. **Multi-turn**: Context management needs testing

## Next Steps

1. Review the [complete testing plan](../docs/docs/rag/a2a-testing-plan.md)
2. Deploy the stack locally
3. Run existing tests to establish baseline
4. Implement priority tests from Phase 1
5. Expand coverage with Phase 2 and 3 tests

## Resources

- [A2A Protocol Specification](https://github.com/IBM/agent-to-agent-protocol)
- [A2A SDK Documentation](https://github.com/IBM/a2a-sdk-python)
- [Complete Testing Plan](../docs/docs/rag/a2a-testing-plan.md)
- [RAG Agent Documentation](../docs/docs/rag/overview.md)