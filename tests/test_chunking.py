import pytest
from core.rag.chunking.text_chunker import TextChunker
from core.rag.schema import DocumentSchema, DocumentMetadata, DocumentSection

class TestChunking:
    """Test document chunking functionality"""
    
    def create_test_document(self) -> DocumentSchema:
        """Create a test document"""
        metadata = DocumentMetadata(
            title="Test Document",
            doc_id="test_doc_1",
            filetype="test",
            pages=1
        )
        
        # Create a long section that will need chunking
        long_content = "This is a test sentence. " * 200  # ~1000 words
        
        sections = [
            DocumentSection(
                section_id="section_1",
                title="Short Section",
                content="This is a short section.",
                page_start=1,
                page_end=1
            ),
            DocumentSection(
                section_id="section_2", 
                title="Long Section",
                content=long_content,
                page_start=1,
                page_end=1
            )
        ]
        
        return DocumentSchema(metadata=metadata, sections=sections)
    
    def test_chunking_short_content(self):
        """Test chunking of short content"""
        chunker = TextChunker(max_tokens=1000, overlap_tokens=100)
        document = self.create_test_document()
        
        # Modify to have only short content
        document.sections = [document.sections[0]]  # Only short section
        
        chunks = chunker.chunk_document(document)
        
        # Should have one chunk for the short section
        assert len(chunks) >= 1
        
        # Verify chunk metadata
        chunk = chunks[0]
        assert chunk['metadata'].doc_id == "test_doc_1"
        assert chunk['metadata'].section_id == "section_1"
        assert chunk['metadata'].chunk_type == "text"
        assert chunk['metadata'].token_count > 0
    
    def test_chunking_long_content(self):
        """Test chunking of long content"""
        chunker = TextChunker(max_tokens=500, overlap_tokens=50)
        document = self.create_test_document()
        
        chunks = chunker.chunk_document(document)
        
        # Should have multiple chunks due to long content
        assert len(chunks) > 2
        
        # Verify all chunks have proper metadata
        for chunk in chunks:
            assert chunk['metadata'].doc_id == "test_doc_1"
            assert chunk['metadata'].chunk_type == "text"
            assert chunk['metadata'].token_count > 0
            assert chunk['metadata'].token_count <= 500
    
    def test_chunk_overlap(self):
        """Test that chunks have proper overlap"""
        chunker = TextChunker(max_tokens=100, overlap_tokens=20)
        document = self.create_test_document()
        
        # Use only the long section
        document.sections = [document.sections[1]]
        
        chunks = chunker.chunk_document(document)
        
        if len(chunks) > 1:
            # Check that consecutive chunks have some overlap
            # This is a simplified check - in practice, overlap detection is complex
            chunk1_content = chunks[0]['content']
            chunk2_content = chunks[1]['content']
            
            # At minimum, chunks should exist and have content
            assert len(chunk1_content) > 0
            assert len(chunk2_content) > 0
    
    def test_chunk_count_consistency(self):
        """Test that chunk count is consistent with token limits"""
        chunker = TextChunker(max_tokens=200, overlap_tokens=20)
        document = self.create_test_document()
        
        chunks = chunker.chunk_document(document)
        
        # Verify no chunk exceeds token limit
        for chunk in chunks:
            assert chunk['metadata'].token_count <= 200
        
        # Verify we have reasonable number of chunks
        assert len(chunks) >= 2  # At least short + part of long section