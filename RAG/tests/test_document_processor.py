"""Unit tests for Document Processor."""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.document_processor import DocumentProcessor
from config.settings import get_settings


@pytest.fixture
def processor():
    """Create document processor instance."""
    settings = get_settings()
    return DocumentProcessor(settings)


@pytest.fixture
def shakespeare_file():
    """Path to Shakespeare test file."""
    return "data/reference/complete works of Shakespear.txt"


@pytest.mark.unit
class TestDocumentProcessor:
    """Test suite for DocumentProcessor."""

    @pytest.mark.shakespeare
    def test_text_file_processing(self, processor, shakespeare_file):
        """Test 1.1.1: Verify text file extraction."""
        chunks = processor.process_file(shakespeare_file)
        
        assert len(chunks) > 0, "Should extract chunks from file"
        assert all(isinstance(chunk['text'], str) for chunk in chunks), "All chunks should be strings"
        assert any('Shakespeare' in chunk['text'] or 'SHAKESPEARE' in chunk['text'] 
                   for chunk in chunks), "Should contain Shakespeare content"
        print(f"✓ Extracted {len(chunks)} chunks from Shakespeare file")

    def test_text_chunking(self, processor, shakespeare_file):
        """Test 1.1.2: Verify text is chunked correctly with overlap."""
        chunks = processor.process_file(shakespeare_file)
        
        assert len(chunks) > 0, "Should create chunks"
        
        # Check chunk sizes are reasonable
        chunk_sizes = [len(chunk['text'].split()) for chunk in chunks]
        assert all(size <= processor.chunk_size * 1.5 for size in chunk_sizes), \
            "Chunks should not exceed size limit significantly"
        
        # Verify chunks are different
        if len(chunks) > 1:
            assert chunks[0]['text'] != chunks[1]['text'], "Chunks should be different"
        
        print(f"✓ Created {len(chunks)} chunks with proper sizing")

    def test_chunk_metadata_generation(self, processor, shakespeare_file):
        """Test 1.1.3: Verify chunk metadata is correct."""
        chunks = processor.process_file(shakespeare_file)
        
        # Check all required fields
        for chunk in chunks:
            assert 'id' in chunk, "Chunk should have ID"
            assert 'text' in chunk, "Chunk should have text"
            assert 'source' in chunk, "Chunk should have source"
            assert 'chunk_index' in chunk, "Chunk should have index"
            assert 'total_chunks' in chunk, "Chunk should have total count"
        
        # Check unique IDs
        ids = [chunk['id'] for chunk in chunks]
        assert len(set(ids)) == len(ids), "All chunk IDs should be unique"
        
        # Check sequential indices
        indices = [chunk['chunk_index'] for chunk in chunks]
        assert indices == list(range(len(chunks))), "Indices should be sequential"
        
        # Check total chunks is consistent
        assert all(chunk['total_chunks'] == len(chunks) for chunk in chunks), \
            "Total chunks should be consistent"
        
        print(f"✓ All {len(chunks)} chunks have correct metadata")

    def test_large_file_handling(self, processor, shakespeare_file):
        """Test 1.1.4: Verify processor handles large files."""
        import time
        
        start_time = time.time()
        chunks = processor.process_file(shakespeare_file)
        processing_time = time.time() - start_time
        
        assert processing_time < 300, f"Processing took {processing_time:.2f}s, should be < 300s"
        assert len(chunks) > 100, "Should create substantial number of chunks"
        assert len(chunks) < 100000, "Should not create excessive chunks"
        
        print(f"✓ Processed large file in {processing_time:.2f}s, created {len(chunks)} chunks")

    def test_text_cleaning(self, processor):
        """Test 1.1.5: Verify text cleaning removes unwanted characters."""
        # Test text with issues
        dirty_text = "This  has   extra    spaces\n\n\nand\r\nline\rbreaks"
        cleaned = processor._clean_text(dirty_text)
        
        assert "  " not in cleaned, "Should remove double spaces"
        assert cleaned.strip() == cleaned, "Should remove leading/trailing whitespace"
        assert "\r" not in cleaned, "Should normalize line breaks"
        
        print("✓ Text cleaning works correctly")

    def test_unsupported_file_type(self, processor, tmp_path):
        """Test 1.1.6: Verify error handling for unsupported files."""
        # Create a temporary file with unsupported extension
        test_file = tmp_path / "test.xyz"
        test_file.write_text("test content")
        
        with pytest.raises(ValueError, match="Unsupported file type"):
            processor.process_file(str(test_file))
        
        print("✓ Correctly rejects unsupported file types")

    def test_missing_file(self, processor):
        """Test 1.1.7: Verify error handling for missing files."""
        with pytest.raises(FileNotFoundError):
            processor.process_file("nonexistent_file.txt")
        
        print("✓ Correctly handles missing files")

    def test_supported_extensions(self, processor):
        """Test: Verify supported extensions list."""
        extensions = processor.get_supported_extensions()
        
        assert '.txt' in extensions, "Should support .txt"
        assert '.md' in extensions, "Should support .md"
        assert '.pdf' in extensions, "Should support .pdf"
        assert '.docx' in extensions, "Should support .docx"
        
        print(f"✓ Supports {len(extensions)} file types: {extensions}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

# Made with Bob
