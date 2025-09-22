from typing import Optional
from core.rag.vectorstore.base_vectorstore import BaseVectorStore
from core.rag.vectorstore.faiss_store import FAISSVectorStore
from core.config.rag_config import get_rag_config

class VectorStoreFactory:
    """Factory for creating vector stores"""
    
    _stores = {
        'faiss': FAISSVectorStore,
    }
    
    @classmethod
    def create_vectorstore(cls, store_type: str = None) -> BaseVectorStore:
        """Create vector store instance"""
        config = get_rag_config()
        store_type = store_type or config.vector_store
        
        if store_type not in cls._stores:
            raise ValueError(f"Unsupported vector store type: {store_type}")
        
        return cls._stores[store_type]()
    
    @classmethod
    def register_store(cls, store_type: str, store_class: type):
        """Register new vector store type"""
        cls._stores[store_type.lower()] = store_class