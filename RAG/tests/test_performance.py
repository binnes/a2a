"""Performance tests for RAG system."""

import pytest
import time
import asyncio
from typing import List
import statistics

from config.settings import Settings
from services.watsonx_client import WatsonxClient
from services.milvus_client import MilvusClient
from services.document_processor import DocumentProcessor
from mcp_server.rag_tools import RAGTools


@pytest.fixture
def settings():
    """Get application settings."""
    return Settings()


@pytest.fixture
def watsonx_client(settings):
    """Create Watsonx client."""
    return WatsonxClient(settings)


@pytest.fixture
def milvus_client(settings):
    """Create Milvus client."""
    return MilvusClient(settings)


@pytest.fixture
def document_processor(settings):
    """Create document processor."""
    return DocumentProcessor(settings)


@pytest.fixture
def rag_tools(settings):
    """Create RAG tools."""
    return RAGTools(settings)


class TestEmbeddingPerformance:
    """Test embedding generation performance."""

    def test_single_embedding_latency(self, watsonx_client):
        """Test latency of single embedding generation."""
        # Execute
        start = time.time()
        embedding = watsonx_client.generate_embedding("test text")
        duration = time.time() - start
        
        # Verify
        assert len(embedding) == 768
        assert duration < 2.0  # Should complete in under 2 seconds
        print(f"\nSingle embedding latency: {duration:.3f}s")

    def test_batch_embedding_throughput(self, watsonx_client):
        """Test throughput of batch embedding generation."""
        # Setup
        texts = [f"test text {i}" for i in range(10)]
        
        # Execute
        start = time.time()
        embeddings = watsonx_client.generate_embeddings(texts)
        duration = time.time() - start
        
        # Verify
        assert len(embeddings) == 10
        throughput = len(texts) / duration
        print(f"\nBatch embedding throughput: {throughput:.2f} texts/sec")
        assert throughput > 1.0  # At least 1 text per second

    def test_embedding_consistency(self, watsonx_client):
        """Test embedding generation is consistent."""
        # Execute
        text = "consistent test text"
        embedding1 = watsonx_client.generate_embedding(text)
        embedding2 = watsonx_client.generate_embedding(text)
        
        # Verify - embeddings should be identical
        assert embedding1 == embedding2


class TestVectorSearchPerformance:
    """Test vector search performance."""

    def test_search_latency(self, milvus_client, watsonx_client):
        """Test search latency."""
        # Setup - ensure some data exists
        stats = milvus_client.get_stats()
        if stats["num_entities"] == 0:
            pytest.skip("No data in collection for search test")
        
        # Generate query vector
        query_vector = watsonx_client.generate_embedding("test query")
        
        # Execute
        start = time.time()
        results = milvus_client.search(query_vector, top_k=5)
        duration = time.time() - start
        
        # Verify
        assert duration < 0.5  # Should complete in under 500ms
        print(f"\nSearch latency: {duration:.3f}s")

    def test_search_with_different_top_k(self, milvus_client, watsonx_client):
        """Test search performance with different top_k values."""
        # Setup
        stats = milvus_client.get_stats()
        if stats["num_entities"] == 0:
            pytest.skip("No data in collection")
        
        query_vector = watsonx_client.generate_embedding("test")
        latencies = {}
        
        # Execute with different top_k values
        for k in [1, 5, 10, 20]:
            start = time.time()
            results = milvus_client.search(query_vector, top_k=k)
            latencies[k] = time.time() - start
        
        # Verify
        print(f"\nSearch latencies by top_k: {latencies}")
        # All should complete quickly
        assert all(lat < 1.0 for lat in latencies.values())


class TestDocumentProcessingPerformance:
    """Test document processing performance."""

    def test_chunking_performance(self, document_processor):
        """Test document chunking performance."""
        # Setup
        file_path = "data/reference/complete works of Shakespear.txt"
        
        # Execute
        start = time.time()
        chunks = document_processor.process_file(file_path)
        duration = time.time() - start
        
        # Verify
        assert len(chunks) > 0
        throughput = len(chunks) / duration
        print(f"\nChunking throughput: {throughput:.2f} chunks/sec")
        print(f"Total chunks: {len(chunks)}, Duration: {duration:.2f}s")


class TestEndToEndPerformance:
    """Test end-to-end RAG performance."""

    @pytest.mark.asyncio
    async def test_query_latency(self, rag_tools):
        """Test end-to-end query latency."""
        # Setup - ensure data exists
        stats = await rag_tools.get_stats()
        if stats["statistics"]["num_entities"] == 0:
            pytest.skip("No data indexed for query test")
        
        # Execute
        start = time.time()
        result = await rag_tools.query("test query")
        duration = time.time() - start
        
        # Verify
        assert "answer" in result
        print(f"\nEnd-to-end query latency: {duration:.3f}s")
        assert duration < 5.0  # Should complete in under 5 seconds

    @pytest.mark.asyncio
    async def test_search_only_latency(self, rag_tools):
        """Test search-only latency (no LLM)."""
        # Setup
        stats = await rag_tools.get_stats()
        if stats["statistics"]["num_entities"] == 0:
            pytest.skip("No data indexed")
        
        # Execute
        start = time.time()
        result = await rag_tools.search("test query")
        duration = time.time() - start
        
        # Verify
        assert "results" in result
        print(f"\nSearch-only latency: {duration:.3f}s")
        assert duration < 2.0  # Should be faster than full query


class TestConcurrentPerformance:
    """Test concurrent operation performance."""

    @pytest.mark.asyncio
    async def test_concurrent_queries(self, rag_tools):
        """Test handling concurrent queries."""
        # Setup
        stats = await rag_tools.get_stats()
        if stats["statistics"]["num_entities"] == 0:
            pytest.skip("No data indexed")
        
        queries = [f"test query {i}" for i in range(5)]
        
        # Execute
        start = time.time()
        tasks = [rag_tools.search(q) for q in queries]
        results = await asyncio.gather(*tasks)
        duration = time.time() - start
        
        # Verify
        assert len(results) == 5
        avg_latency = duration / len(queries)
        print(f"\nConcurrent queries: {len(queries)}")
        print(f"Total time: {duration:.3f}s")
        print(f"Average latency: {avg_latency:.3f}s")

    def test_concurrent_embeddings(self, watsonx_client):
        """Test concurrent embedding generation."""
        # Setup
        texts = [f"text {i}" for i in range(5)]
        
        # Execute - sequential
        start = time.time()
        for text in texts:
            watsonx_client.generate_embedding(text)
        sequential_duration = time.time() - start
        
        # Execute - batch
        start = time.time()
        watsonx_client.generate_embeddings(texts)
        batch_duration = time.time() - start
        
        # Verify
        print(f"\nSequential embeddings: {sequential_duration:.3f}s")
        print(f"Batch embeddings: {batch_duration:.3f}s")
        print(f"Speedup: {sequential_duration/batch_duration:.2f}x")


class TestScalabilityMetrics:
    """Test system scalability metrics."""

    def test_collection_size_impact(self, milvus_client):
        """Test impact of collection size on search."""
        # Execute
        stats = milvus_client.get_stats()
        
        # Verify
        print(f"\nCollection statistics:")
        print(f"  Entities: {stats['num_entities']}")
        print(f"  Dimension: {stats['dimension']}")
        print(f"  Metric: {stats['metric_type']}")

    @pytest.mark.asyncio
    async def test_query_complexity_impact(self, rag_tools):
        """Test impact of query complexity on latency."""
        # Setup
        stats = await rag_tools.get_stats()
        if stats["statistics"]["num_entities"] == 0:
            pytest.skip("No data indexed")
        
        queries = {
            "simple": "Romeo",
            "medium": "Who is Romeo?",
            "complex": "What is the relationship between Romeo and Juliet in the play?",
        }
        
        latencies = {}
        
        # Execute
        for complexity, query in queries.items():
            start = time.time()
            await rag_tools.search(query)
            latencies[complexity] = time.time() - start
        
        # Verify
        print(f"\nQuery latencies by complexity:")
        for complexity, latency in latencies.items():
            print(f"  {complexity}: {latency:.3f}s")


class TestMemoryUsage:
    """Test memory usage patterns."""

    @pytest.mark.skipif(True, reason="psutil not required - optional performance metric")
    def test_batch_processing_memory(self, document_processor):
        """Test memory usage during batch processing."""
        try:
            import psutil
            import os
            
            # Get initial memory
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Execute
            file_path = "data/reference/complete works of Shakespear.txt"
            chunks = document_processor.process_file(file_path)
            
            # Get final memory
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory
            
            # Verify
            print(f"\nMemory usage:")
            print(f"  Initial: {initial_memory:.2f} MB")
            print(f"  Final: {final_memory:.2f} MB")
            print(f"  Increase: {memory_increase:.2f} MB")
            print(f"  Chunks processed: {len(chunks)}")
        except ImportError:
            pytest.skip("psutil not installed")


class TestReliabilityMetrics:
    """Test system reliability metrics."""

    def test_embedding_retry_success(self, watsonx_client):
        """Test embedding generation succeeds with retries."""
        # Execute multiple times to test reliability
        success_count = 0
        attempts = 5
        
        for i in range(attempts):
            try:
                embedding = watsonx_client.generate_embedding(f"test {i}")
                if len(embedding) == 768:
                    success_count += 1
            except Exception:
                pass
        
        # Verify
        success_rate = success_count / attempts
        print(f"\nEmbedding success rate: {success_rate:.1%} ({success_count}/{attempts})")
        assert success_rate >= 0.8  # At least 80% success rate

    def test_search_consistency(self, milvus_client, watsonx_client):
        """Test search returns consistent results."""
        # Setup
        stats = milvus_client.get_stats()
        if stats["num_entities"] == 0:
            pytest.skip("No data indexed")
        
        query_vector = watsonx_client.generate_embedding("test query")
        
        # Execute multiple searches
        results_list = []
        for _ in range(3):
            results = milvus_client.search(query_vector, top_k=5)
            results_list.append([r["id"] for r in results])
        
        # Verify - all searches should return same IDs
        assert results_list[0] == results_list[1] == results_list[2]
        print(f"\nSearch consistency: 100% (3/3 identical)")


# Made with Bob