import os
from typing import Optional
from core.rag.ingestion.base_extractor import BaseExtractor
from core.rag.ingestion.docx_extractor import DocxExtractor
from core.rag.ingestion.pdf_extractor import PdfExtractor

class ExtractorFactory:
    """Factory for creating document extractors"""
    
    _extractors = {
        'docx': DocxExtractor,
        'pdf': PdfExtractor
    }
    
    @classmethod
    def get_extractor(cls, file_path: str) -> Optional[BaseExtractor]:
        """Get appropriate extractor for file"""
        _, ext = os.path.splitext(file_path)
        ext = ext.lower().lstrip('.')
        
        if ext in cls._extractors:
            return cls._extractors[ext]()
        
        return None
    
    @classmethod
    def register_extractor(cls, filetype: str, extractor_class: type):
        """Register new extractor for filetype"""
        cls._extractors[filetype.lower()] = extractor_class
    
    @classmethod
    def supported_filetypes(cls) -> list:
        """Get list of supported filetypes"""
        return list(cls._extractors.keys())