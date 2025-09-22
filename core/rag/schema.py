from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime

class DocumentMetadata(BaseModel):
    """Document metadata schema"""
    title: str = ""
    author: str = ""
    date: str = ""
    source_path: str = ""
    doc_id: str = ""
    filetype: str = ""
    pages: int = 0

class DocumentSection(BaseModel):
    """Document section schema"""
    section_id: str
    title: str
    content: str
    page_start: int
    page_end: int
    level: int = 1
    parent_section_id: Optional[str] = None

class DocumentFact(BaseModel):
    """Document fact schema"""
    fact_id: str
    content: str
    confidence: float
    source_section: str
    page: int

class DocumentRisk(BaseModel):
    """Document risk schema"""
    risk_id: str
    description: str
    severity: str  # low, medium, high, critical
    mitigation: Optional[str] = None
    source_section: str
    page: int

class DocumentList(BaseModel):
    """Document list schema"""
    list_id: str
    title: str
    items: List[str]
    list_type: str  # bullet, numbered, checklist
    source_section: str
    page: int

class DocumentComment(BaseModel):
    """Document comment schema"""
    comment_id: str
    content: str
    author: Optional[str] = None
    timestamp: Optional[str] = None
    source_section: str
    page: int

class DocumentTable(BaseModel):
    """Document table schema"""
    table_id: str
    title: Optional[str] = None
    headers: List[str]
    rows: List[List[str]]
    caption: Optional[str] = None
    source_section: str
    page: int

class DocumentFigure(BaseModel):
    """Document figure schema"""
    figure_id: str
    title: Optional[str] = None
    caption: Optional[str] = None
    figure_type: str  # chart, diagram, graph, etc.
    source_section: str
    page: int

class DocumentImage(BaseModel):
    """Document image schema"""
    image_id: str
    filename: str
    alt_text: Optional[str] = None
    extracted_text: Optional[str] = None  # OCR text
    source_section: str
    page: int

class DocumentSchema(BaseModel):
    """Complete document schema"""
    metadata: DocumentMetadata
    sections: List[DocumentSection] = []
    facts: List[DocumentFact] = []
    risks: List[DocumentRisk] = []
    lists: List[DocumentList] = []
    comments: List[DocumentComment] = []
    tables: List[DocumentTable] = []
    figures: List[DocumentFigure] = []
    images: List[DocumentImage] = []

class ChunkMetadata(BaseModel):
    """Chunk metadata for vector store"""
    doc_id: str
    chunk_id: str
    page_start: int
    page_end: int
    section_id: str
    heading_chain: List[str]
    chunk_type: str  # text, table, figure, image
    token_count: int

class RetrievalResult(BaseModel):
    """Retrieval result with metadata"""
    content: str
    score: float
    metadata: ChunkMetadata
    
class Citation(BaseModel):
    """Citation information"""
    doc_id: str
    page: int
    section: str
    chunk_id: str
    content_preview: str