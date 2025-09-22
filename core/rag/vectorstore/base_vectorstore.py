from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from core.rag.schema import RetrievalResult

class BaseVectorStore(ABC):
    """Base class for vector stores"""
    
    @abstractmethod
    def add_documents(self, chunks: List[Dict[str, Any]]) -> None:
        """Add document chunks to the vector store"""
        pass
    
    @abstractmethod
    def similarity_search(self, query: str, k: int = 10, doc_ids: Optional[List[str]] = None) -> List[RetrievalResult]:
        """Perform similarity search"""
        pass
    
    @abstractmethod
    def delete_documents(self, doc_ids: List[str]) -> None:
        """Delete documents from vector store"""
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics"""
        pass