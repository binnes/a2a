"""Document processing pipeline for RAG knowledge base."""

import logging
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
import re

from pypdf import PdfReader  # type: ignore
from docx import Document  # type: ignore
from langchain_text_splitters import RecursiveCharacterTextSplitter  # type: ignore

from config.settings import Settings

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Process documents for RAG indexing."""

    def __init__(self, settings: Settings):
        """Initialize document processor.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.chunk_size = settings.rag_chunk_size
        self.chunk_overlap = settings.rag_chunk_overlap
        
        # Initialize LangChain text splitter
        # Convert word-based sizes to character-based (avg 5 chars per word)
        chunk_size_chars = self.chunk_size * 5
        chunk_overlap_chars = self.chunk_overlap * 5
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size_chars,
            chunk_overlap=chunk_overlap_chars,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    def process_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Process a single file and extract text chunks.

        Args:
            file_path: Path to the file to process

        Returns:
            List of document chunks with metadata

        Raises:
            Exception: If file processing fails
        """
        try:
            path = Path(file_path)
            
            if not path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            # Extract text based on file type
            if path.suffix.lower() == ".pdf":
                text = self._extract_pdf(path)
            elif path.suffix.lower() == ".docx":
                text = self._extract_docx(path)
            elif path.suffix.lower() in [".txt", ".md"]:
                text = self._extract_text(path)
            else:
                raise ValueError(f"Unsupported file type: {path.suffix}")

            # Clean and chunk text
            cleaned_text = self._clean_text(text)
            chunks = self._chunk_text(cleaned_text)

            # Create document chunks with metadata
            doc_chunks = []
            for i, chunk in enumerate(chunks):
                chunk_id = self._generate_chunk_id(file_path, i)
                doc_chunks.append({
                    "id": chunk_id,
                    "text": chunk,
                    "source": str(path),
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                })

            logger.info(f"Processed {file_path}: {len(chunks)} chunks")
            return doc_chunks

        except Exception as e:
            logger.error(f"Failed to process file {file_path}: {e}")
            raise

    def process_directory(
        self,
        directory_path: str,
        recursive: bool = True,
    ) -> List[Dict[str, Any]]:
        """Process all supported files in a directory.

        Args:
            directory_path: Path to the directory
            recursive: Whether to process subdirectories

        Returns:
            List of all document chunks from all files

        Raises:
            Exception: If directory processing fails
        """
        try:
            path = Path(directory_path)
            
            if not path.exists() or not path.is_dir():
                raise ValueError(f"Invalid directory: {directory_path}")

            all_chunks = []
            supported_extensions = {".pdf", ".docx", ".txt", ".md"}

            # Get all files
            if recursive:
                files = [f for f in path.rglob("*") if f.suffix.lower() in supported_extensions]
            else:
                files = [f for f in path.glob("*") if f.suffix.lower() in supported_extensions]

            logger.info(f"Found {len(files)} files to process")

            # Process each file
            for file_path in files:
                try:
                    chunks = self.process_file(str(file_path))
                    all_chunks.extend(chunks)
                except Exception as e:
                    logger.warning(f"Skipping file {file_path}: {e}")
                    continue

            logger.info(f"Processed {len(files)} files: {len(all_chunks)} total chunks")
            return all_chunks

        except Exception as e:
            logger.error(f"Failed to process directory {directory_path}: {e}")
            raise

    def _extract_pdf(self, path: Path) -> str:
        """Extract text from PDF file.

        Args:
            path: Path to PDF file

        Returns:
            Extracted text
        """
        try:
            reader = PdfReader(str(path))
            text_parts = []
            
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
            
            return "\n\n".join(text_parts)

        except Exception as e:
            logger.error(f"Failed to extract PDF text: {e}")
            raise

    def _extract_docx(self, path: Path) -> str:
        """Extract text from DOCX file.

        Args:
            path: Path to DOCX file

        Returns:
            Extracted text
        """
        try:
            doc = Document(str(path))
            text_parts = []
            
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_parts.append(paragraph.text)
            
            return "\n\n".join(text_parts)

        except Exception as e:
            logger.error(f"Failed to extract DOCX text: {e}")
            raise

    def _extract_text(self, path: Path) -> str:
        """Extract text from plain text file.

        Args:
            path: Path to text file

        Returns:
            Extracted text
        """
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()

        except Exception as e:
            logger.error(f"Failed to extract text: {e}")
            raise

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text.

        Args:
            text: Raw text to clean

        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        text = re.sub(r"\s+", " ", text)
        
        # Remove special characters but keep punctuation
        text = re.sub(r"[^\w\s.,!?;:()\-\"']", "", text)
        
        # Normalize line breaks
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        
        return text.strip()

    def _chunk_text(self, text: str) -> List[str]:
        """Split text into chunks with overlap using LangChain's RecursiveCharacterTextSplitter.

        Args:
            text: Text to chunk

        Returns:
            List of text chunks
        """
        # Use LangChain's text splitter for robust chunking
        chunks = self.text_splitter.split_text(text)
        return chunks

    def _generate_chunk_id(self, file_path: str, chunk_index: int) -> str:
        """Generate unique ID for a document chunk.

        Args:
            file_path: Source file path
            chunk_index: Index of the chunk

        Returns:
            Unique chunk ID
        """
        # Create hash from file path and chunk index
        content = f"{file_path}:{chunk_index}"
        hash_obj = hashlib.sha256(content.encode())
        return hash_obj.hexdigest()[:32]

    def get_supported_extensions(self) -> List[str]:
        """Get list of supported file extensions.

        Returns:
            List of supported extensions
        """
        return [".pdf", ".docx", ".txt", ".md"]

# Made with Bob
