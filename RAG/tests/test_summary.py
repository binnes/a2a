"""Summary test to verify core functionality."""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.document_processor import DocumentProcessor
from config.settings import get_settings


class TestCoreFunctionality:
    """Test core RAG functionality."""

    def test_document_processor_works(self):
        """Verify document processor can process Shakespeare file."""
        settings = get_settings()
        processor = DocumentProcessor(settings)
        
        shakespeare_file = "data/reference/complete works of Shakespear.txt"
        chunks = processor.process_file(shakespeare_file)
        
        assert len(chunks) > 1000, f"Should create many chunks, got {len(chunks)}"
        assert all('id' in chunk for chunk in chunks), "All chunks should have IDs"
        assert all('text' in chunk for chunk in chunks), "All chunks should have text"
        
        # Verify chunk sizes are reasonable (under 512 tokens ~= 400 words)
        chunk_word_counts = [len(chunk['text'].split()) for chunk in chunks]
        max_words = max(chunk_word_counts)
        assert max_words <= 400, f"Max chunk size {max_words} words should be <= 400"
        
        print(f"✓ Processed {len(chunks)} chunks from Shakespeare")
        print(f"✓ Max chunk size: {max_words} words")
        print(f"✓ All chunks have proper metadata")
        
    def test_settings_updated(self):
        """Verify settings are using correct model."""
        settings = get_settings()
        
        assert settings.embedding_model == "ibm/granite-embedding-278m-multilingual"
        assert settings.embedding_dimension == 768
        assert settings.rag_chunk_size == 80
        assert settings.rag_chunk_overlap == 10
        
        print(f"✓ Embedding model: {settings.embedding_model}")
        print(f"✓ Embedding dimension: {settings.embedding_dimension}")
        print(f"✓ Chunk size: {settings.rag_chunk_size} words")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

# Made with Bob
