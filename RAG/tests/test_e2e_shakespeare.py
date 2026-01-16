"""End-to-end tests for RAG pipeline with Shakespeare data."""

import pytest
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.a2a_agent import A2ARAGAgent
from config.settings import get_settings
from services.document_processor import DocumentProcessor
from services.milvus_client import MilvusClient
from services.watsonx_client import WatsonxClient
from mcp_server.rag_tools import RAGTools


@pytest.fixture(scope="module")
def settings():
    """Get settings."""
    return get_settings()


@pytest.fixture(scope="module")
def shakespeare_file():
    """Path to Shakespeare test file."""
    return "data/reference/complete works of Shakespear.txt"


@pytest.fixture(scope="module")
async def rag_tools(settings):
    """Create RAG tools instance."""
    tools = RAGTools(settings)
    yield tools
    # Cleanup
    if tools.milvus:
        tools.milvus.disconnect()


@pytest.fixture(scope="function")
async def agent(settings):
    """Create A2A agent instance for each test."""
    agent = A2ARAGAgent(settings)
    yield agent
    # Cleanup
    try:
        await agent.close()
    except Exception:
        pass  # Ignore cleanup errors


class TestShakespeareE2E:
    """End-to-end tests with Shakespeare complete works."""

    @pytest.mark.asyncio
    async def test_01_clear_knowledge_base(self, rag_tools):
        """Clear existing knowledge base before testing."""
        result = await rag_tools.clear_knowledge_base()
        assert result['status'] == 'success'
        print("✓ Knowledge base cleared")

    @pytest.mark.asyncio
    async def test_02_index_shakespeare(self, rag_tools, shakespeare_file):
        """Test indexing Shakespeare complete works."""
        result = await rag_tools.index_document(shakespeare_file)
        
        assert result['status'] == 'success'
        assert result['chunks_indexed'] > 1000, "Should create many chunks from large file"
        print(f"✓ Indexed {result['chunks_indexed']} chunks from Shakespeare")

    @pytest.mark.asyncio
    async def test_03_verify_indexing(self, rag_tools):
        """Verify documents are in knowledge base."""
        stats = await rag_tools.get_stats()
        
        assert stats['status'] == 'success'
        assert stats['statistics']['num_entities'] > 1000
        print(f"✓ Knowledge base contains {stats['statistics']['num_entities']} entities")

    @pytest.mark.asyncio
    async def test_04_query_romeo(self, rag_tools):
        """Test query about Romeo."""
        result = await rag_tools.query(
            query="Who is Romeo?",
            top_k=3,
            include_sources=True
        )
        
        assert 'answer' in result
        assert len(result['answer']) > 50, "Answer should be substantial"
        assert len(result['context']) > 0, "Should have context"
        assert len(result['sources']) > 0, "Should have sources"
        
        # Check relevance
        answer_lower = result['answer'].lower()
        assert 'romeo' in answer_lower or 'juliet' in answer_lower
        
        print(f"✓ Romeo query answered: {result['answer'][:100]}...")

    @pytest.mark.asyncio
    async def test_05_query_hamlet(self, rag_tools):
        """Test query about Hamlet."""
        result = await rag_tools.query(
            query="What happens in Hamlet?",
            top_k=3,
            include_sources=True
        )
        
        assert 'answer' in result
        assert len(result['answer']) > 50
        assert len(result['context']) > 0
        
        answer_lower = result['answer'].lower()
        assert 'hamlet' in answer_lower
        
        print(f"✓ Hamlet query answered: {result['answer'][:100]}...")

    @pytest.mark.asyncio
    async def test_06_query_macbeth(self, rag_tools):
        """Test query about Macbeth."""
        result = await rag_tools.query(
            query="Describe Macbeth's character",
            top_k=3,
            include_sources=True
        )
        
        assert 'answer' in result
        assert len(result['answer']) > 50
        
        answer_lower = result['answer'].lower()
        assert 'macbeth' in answer_lower
        
        print(f"✓ Macbeth query answered: {result['answer'][:100]}...")

    @pytest.mark.asyncio
    async def test_07_search_without_llm(self, rag_tools):
        """Test semantic search without LLM generation."""
        result = await rag_tools.search(
            query="love and tragedy",
            top_k=5
        )
        
        assert 'results' in result
        assert result['count'] > 0
        assert len(result['results']) <= 5
        
        # Check results have required fields
        for r in result['results']:
            assert 'text' in r
            assert 'score' in r
            assert 'source' in r
        
        print(f"✓ Search returned {result['count']} results")

    @pytest.mark.asyncio
    async def test_08_agent_query_romeo(self, agent):
        """Test A2A agent query about Romeo."""
        result = await agent.process_query("Who is Romeo?")
        
        assert 'response' in result
        assert len(result['response']) > 50
        assert 'sources' in result
        assert len(result['sources']) > 0
        
        # Check all sources have required fields
        for source in result['sources']:
            assert 'source' in source
            assert 'score' in source
            assert source['score'] > 0.5, "Relevance score should be reasonable"
        
        print(f"✓ Agent answered Romeo query: {result['response'][:100]}...")

    @pytest.mark.asyncio
    async def test_09_agent_query_juliet(self, agent):
        """Test A2A agent query about Juliet."""
        result = await agent.process_query("Who is Juliet?")
        
        assert 'response' in result
        assert len(result['response']) > 50
        assert 'sources' in result
        
        response_lower = result['response'].lower()
        assert 'juliet' in response_lower
        
        print(f"✓ Agent answered Juliet query: {result['response'][:100]}...")

    @pytest.mark.asyncio
    async def test_10_agent_query_theme(self, agent):
        """Test A2A agent query about themes."""
        result = await agent.process_query("What are the main themes in Romeo and Juliet?")
        
        assert 'response' in result
        assert len(result['response']) > 50
        
        response_lower = result['response'].lower()
        # Should mention themes like love, tragedy, fate, etc.
        theme_words = ['love', 'tragedy', 'fate', 'death', 'family', 'conflict']
        assert any(word in response_lower for word in theme_words)
        
        print(f"✓ Agent answered theme query: {result['response'][:100]}...")

    @pytest.mark.asyncio
    async def test_11_agent_a2a_message(self, agent):
        """Test A2A protocol message handling."""
        from agent.state import A2AMessage
        from datetime import datetime
        
        query_message: A2AMessage = {
            'agent_id': 'test-agent',
            'message_type': 'query',
            'content': {'query': 'What is the story of Hamlet?'},
            'timestamp': datetime.utcnow().isoformat(),
            'correlation_id': 'test-123'
        }
        
        response = await agent.handle_a2a_message(query_message)
        
        assert response['message_type'] == 'response'
        assert response['correlation_id'] == 'test-123'
        assert 'content' in response
        assert 'response' in response['content']
        
        print(f"✓ A2A message handled correctly")

    @pytest.mark.asyncio
    async def test_12_agent_health_check(self, agent):
        """Test agent health check."""
        health = await agent.health_check()
        
        assert 'agent' in health
        assert 'mcp_server' in health
        assert health['agent'] == True
        
        print(f"✓ Agent health check passed")

    @pytest.mark.asyncio
    async def test_13_agent_capabilities(self, agent):
        """Test agent capabilities."""
        caps = agent.get_capabilities()
        
        assert 'agent_id' in caps
        assert 'capabilities' in caps
        assert 'rag_query' in caps['capabilities']
        
        print(f"✓ Agent capabilities: {caps['capabilities']}")

    @pytest.mark.asyncio
    async def test_14_multiple_queries(self, agent):
        """Test multiple queries in sequence."""
        queries = [
            "Who wrote Romeo and Juliet?",
            "What happens in the balcony scene?",
            "How does the play end?"
        ]
        
        for query in queries:
            result = await agent.process_query(query)
            assert 'response' in result
            assert len(result['response']) > 20
            print(f"✓ Query '{query[:30]}...' answered")

    @pytest.mark.asyncio
    async def test_15_concurrent_queries(self, agent):
        """Test concurrent query handling."""
        queries = [
            "Who is Romeo?",
            "Who is Juliet?",
            "Who is Hamlet?",
            "Who is Macbeth?",
            "Who is Othello?"
        ]
        
        # Run queries concurrently
        results = await asyncio.gather(*[agent.process_query(q) for q in queries])
        
        assert len(results) == len(queries)
        for result in results:
            assert 'response' in result
            assert len(result['response']) > 20
        
        print(f"✓ {len(queries)} concurrent queries handled successfully")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

# Made with Bob
