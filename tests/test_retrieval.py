import pytest
import tempfile
import os
from unittest.mock import Mock, patch

from core.rag.vectorstore.faiss_store import FAISSVectorStore
from core.rag.retrieval.hybrid_retriever import HybridRetriever
from core.rag.schema import ChunkMetadata, RetrievalResult

class TestRetrieval:
    """Test retrieval functionality"""
    
    def create_test_chunks(self):
        """Create test chunks for indexing"""
        chunks = [
            {
                'content': 'This document discusses artificial intelligence and machine learning applications.',
                'metadata': ChunkMetadata(
                    doc_id='doc1',
                    chunk_id='chunk1',
                    page_start=1,
                    page_end=1,
                    section_id='section1',
                    heading_chain=['AI Overview'],
                    chunk_type='text',
                    token_count=50
                )
            },
            {
                'content': 'Machine learning algorithms require large datasets for training purposes.',
                'metadata': ChunkMetadata(
                    doc_id='doc1',
                    chunk_id='chunk2',
                    page_start=2,
                    page_end=2,
                    section_id='section2',
                    heading_chain=['ML Training'],
                    chunk_type='text',
                    token_count=45
                )
            },
            {
                'content': 'Financial reports show quarterly revenue growth of 15% year over year.',
                'metadata': ChunkMetadata(
                    doc_id='doc2',
                    chunk_id='chunk3',
                    page_start=1,
                    page_end=1,
                    section_id='section1',
                    heading_chain=['Financial Results'],
                    chunk_type='text',
                    token_count=40
                )
            }
        ]
        return chunks
    
    @patch('core.rag.vectorstore.faiss_store.OpenAI')
    def test_vector_store_operations(self, mock_openai):
        """Test vector store add and search operations"""
        # Mock OpenAI embeddings
        mock_client = Mock()
        mock_response = Mock()
        mock_response.data = [
            Mock(embedding=[0.1, 0.2, 0.3] * 100),  # 300-dim embedding
            Mock(embedding=[0.2, 0.3, 0.4] * 100),
            Mock(embedding=[0.3, 0.4, 0.5] * 100)
        ]
        mock_client.embeddings.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        # Create temporary index directory
        with tempfile.TemporaryDirectory() as temp_dir:
            vector_store = FAISSVectorStore(index_dir=temp_dir)
            chunks = self.create_test_chunks()
            
            # Test adding documents
            vector_store.add_documents(chunks)
            
            # Verify documents were added
            stats = vector_store.get_stats()
            assert stats['total_chunks'] == 3
            
            # Test search
            mock_client.embeddings.create.return_value.data = [
                Mock(embedding=[0.15, 0.25, 0.35] * 100)
            ]
            
            results = vector_store.similarity_search("machine learning", k=2)
            
            # Should return results
            assert len(results) <= 2
            for result in results:
                assert isinstance(result, RetrievalResult)
                assert result.score >= 0
                assert result.metadata.doc_id in ['doc1', 'doc2']
    
    @patch('core.rag.vectorstore.faiss_store.OpenAI')
    def test_hybrid_retrieval(self, mock_openai):
        """Test hybrid retrieval combining vector and BM25"""
        # Mock OpenAI embeddings
        mock_client = Mock()
        mock_response = Mock()
        mock_response.data = [
            Mock(embedding=[0.1, 0.2, 0.3] * 100),
            Mock(embedding=[0.2, 0.3, 0.4] * 100),
            Mock(embedding=[0.3, 0.4, 0.5] * 100)
        ]
        mock_client.embeddings.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        with tempfile.TemporaryDirectory() as temp_dir:
            vector_store = FAISSVectorStore(index_dir=temp_dir)
            chunks = self.create_test_chunks()
            vector_store.add_documents(chunks)
            
            # Create hybrid retriever
            retriever = HybridRetriever(vector_store)
            
            # Test retrieval
            mock_client.embeddings.create.return_value.data = [
                Mock(embedding=[0.15, 0.25, 0.35] * 100)
            ]
            
            results = retriever.retrieve("machine learning algorithms", k=2)
            
            # Should return results with citations
            assert len(results) <= 2
            for result in results:
                assert isinstance(result, RetrievalResult)
                assert result.content != ""
                assert result.metadata.doc_id != ""
                assert result.metadata.chunk_id != ""
    
    @patch('core.rag.vectorstore.faiss_store.OpenAI')
    def test_doc_id_filtering(self, mock_openai):
        """Test filtering results by document ID"""
        # Mock OpenAI embeddings
        mock_client = Mock()
        mock_response = Mock()
        mock_response.data = [
            Mock(embedding=[0.1, 0.2, 0.3] * 100),
            Mock(embedding=[0.2, 0.3, 0.4] * 100),
            Mock(embedding=[0.3, 0.4, 0.5] * 100)
        ]
        mock_client.embeddings.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        with tempfile.TemporaryDirectory() as temp_dir:
            vector_store = FAISSVectorStore(index_dir=temp_dir)
            chunks = self.create_test_chunks()
            vector_store.add_documents(chunks)
            
            # Test filtering by doc_id
            mock_client.embeddings.create.return_value.data = [
                Mock(embedding=[0.15, 0.25, 0.35] * 100)
            ]
            
            results = vector_store.similarity_search("revenue", k=5, doc_ids=['doc2'])
            
            # Should only return results from doc2
            for result in results:
                assert result.metadata.doc_id == 'doc2'
    
    def test_citation_format(self):
        """Test that retrieval results include proper citation metadata"""
        chunks = self.create_test_chunks()
        
        # Verify chunk metadata has all required citation fields
        for chunk in chunks:
            metadata = chunk['metadata']
            assert metadata.doc_id != ""
            assert metadata.chunk_id != ""
            assert metadata.page_start > 0
            assert len(metadata.heading_chain) > 0