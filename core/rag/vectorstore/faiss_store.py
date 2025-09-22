import os
import json
import pickle
import numpy as np
import faiss
from typing import List, Dict, Any, Optional
from openai import OpenAI

from core.rag.vectorstore.base_vectorstore import BaseVectorStore
from core.rag.schema import RetrievalResult, ChunkMetadata
from core.config.rag_config import get_rag_config

class FAISSVectorStore(BaseVectorStore):
    """FAISS-based vector store implementation"""
    
    def __init__(self, index_dir: str = None):
        self.config = get_rag_config()
        self.index_dir = index_dir or self.config.index_dir
        self.client = OpenAI(api_key=self.config.openai_api_key)
        
        os.makedirs(self.index_dir, exist_ok=True)
        
        self.index_path = os.path.join(self.index_dir, "faiss.index")
        self.metadata_path = os.path.join(self.index_dir, "metadata.json")
        
        # Initialize or load index
        self.index = None
        self.metadata = {}
        self.doc_count = 0
        
        self._load_index()
    
    def add_documents(self, chunks: List[Dict[str, Any]]) -> None:
        """Add document chunks to FAISS index"""
        if not chunks:
            return
        
        # Generate embeddings
        texts = [chunk['content'] for chunk in chunks]
        embeddings = self._get_embeddings(texts)
        
        # Initialize index if needed
        if self.index is None:
            dimension = len(embeddings[0])
            self.index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
        
        # Normalize embeddings for cosine similarity
        embeddings_array = np.array(embeddings).astype('float32')
        faiss.normalize_L2(embeddings_array)
        
        # Add to index
        start_id = len(self.metadata)
        self.index.add(embeddings_array)
        
        # Store metadata
        for i, chunk in enumerate(chunks):
            chunk_id = start_id + i
            self.metadata[str(chunk_id)] = {
                'content': chunk['content'],
                'metadata': chunk['metadata'].dict()
            }
        
        self.doc_count += len(chunks)
        self._save_index()
    
    def similarity_search(self, query: str, k: int = 10, doc_ids: Optional[List[str]] = None) -> List[RetrievalResult]:
        """Perform similarity search"""
        if self.index is None or self.index.ntotal == 0:
            return []
        
        # Get query embedding
        query_embedding = self._get_embeddings([query])[0]
        query_vector = np.array([query_embedding]).astype('float32')
        faiss.normalize_L2(query_vector)
        
        # Search
        scores, indices = self.index.search(query_vector, min(k, self.index.ntotal))
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:  # FAISS returns -1 for invalid indices
                continue
                
            chunk_data = self.metadata.get(str(idx))
            if not chunk_data:
                continue
            
            # Filter by doc_ids if specified
            if doc_ids and chunk_data['metadata']['doc_id'] not in doc_ids:
                continue
            
            result = RetrievalResult(
                content=chunk_data['content'],
                score=float(score),
                metadata=ChunkMetadata(**chunk_data['metadata'])
            )
            results.append(result)
        
        return results
    
    def delete_documents(self, doc_ids: List[str]) -> None:
        """Delete documents from vector store (rebuild index)"""
        if not self.metadata:
            return
        
        # Filter out chunks from deleted documents
        filtered_metadata = {}
        filtered_chunks = []
        
        for chunk_id, chunk_data in self.metadata.items():
            if chunk_data['metadata']['doc_id'] not in doc_ids:
                filtered_metadata[str(len(filtered_chunks))] = chunk_data
                filtered_chunks.append(chunk_data)
        
        # Rebuild index
        self.metadata = filtered_metadata
        self.index = None
        
        if filtered_chunks:
            # Re-add remaining chunks
            chunks_for_reindex = []
            for chunk_data in filtered_chunks:
                chunks_for_reindex.append({
                    'content': chunk_data['content'],
                    'metadata': ChunkMetadata(**chunk_data['metadata'])
                })
            self.add_documents(chunks_for_reindex)
        else:
            self.doc_count = 0
            self._save_index()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics"""
        return {
            'total_chunks': self.index.ntotal if self.index else 0,
            'doc_count': len(set(chunk['metadata']['doc_id'] for chunk in self.metadata.values())),
            'index_size_mb': os.path.getsize(self.index_path) / (1024 * 1024) if os.path.exists(self.index_path) else 0
        }
    
    def _get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using OpenAI API"""
        response = self.client.embeddings.create(
            model=self.config.embedding_model,
            input=texts
        )
        return [embedding.embedding for embedding in response.data]
    
    def _load_index(self) -> None:
        """Load existing index and metadata"""
        try:
            if os.path.exists(self.index_path):
                self.index = faiss.read_index(self.index_path)
            
            if os.path.exists(self.metadata_path):
                with open(self.metadata_path, 'r') as f:
                    self.metadata = json.load(f)
                    
            self.doc_count = len(set(chunk['metadata']['doc_id'] for chunk in self.metadata.values()))
        except Exception as e:
            print(f"Error loading index: {e}")
            self.index = None
            self.metadata = {}
            self.doc_count = 0
    
    def _save_index(self) -> None:
        """Save index and metadata to disk"""
        try:
            if self.index is not None:
                faiss.write_index(self.index, self.index_path)
            
            with open(self.metadata_path, 'w') as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            print(f"Error saving index: {e}")