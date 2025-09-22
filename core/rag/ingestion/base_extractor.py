from abc import ABC, abstractmethod
from typing import Dict, Any
from core.rag.schema import DocumentSchema

class BaseExtractor(ABC):
    """Base class for document extractors"""
    
    @abstractmethod
    def extract(self, file_path: str) -> DocumentSchema:
        """Extract content from document and return structured schema"""
        pass
    
    @abstractmethod
    def supports_filetype(self, filetype: str) -> bool:
        """Check if extractor supports given filetype"""
        pass