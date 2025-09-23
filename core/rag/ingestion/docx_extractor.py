import os
import uuid
from typing import List, Dict, Any
from docx import Document
from docx.table import Table
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.text.paragraph import Paragraph
from docx.shared import Inches

from core.rag.ingestion.heading_extractor import HeadingExtractor
from core.rag.schema import (
    DocumentSchema, DocumentMetadata, DocumentSection, 
    DocumentTable, DocumentList, DocumentImage
)
from core.rag.ingestion.base_extractor import BaseExtractor

class DocxExtractor(BaseExtractor):
    """DOCX document extractor"""
    
    def __init__(self):
        self.heading_extractor = HeadingExtractor()
    
    def extract(self, file_path: str) -> DocumentSchema:
        """Extract content from DOCX file"""
        doc = Document(file_path)
        doc_id = str(uuid.uuid4())
        
        # Extract metadata
        metadata = self._extract_metadata(doc, file_path, doc_id)
        
        # Extract headings dynamically
        detected_headings = self.heading_extractor.extract_docx_headings(doc)
        
        # Convert to DocumentSection objects
        sections = []
        for i, heading_data in enumerate(detected_headings):
            section = DocumentSection(
                section_id=heading_data['section_id'],
                title=heading_data['heading'],
                content=heading_data['content'],
                page_start=heading_data['page_start'],
                page_end=heading_data['page_end'],
                level=heading_data['level']
            )
            sections.append(section)
        
        # Extract tables and other content
        tables = []
        lists = []
        images = []

        for element in doc.element.body:
            if isinstance(element, CT_Tbl):
                table = Table(element, doc)
                extracted_table = self._extract_table(table, len(tables) + 1)
                tables.append(extracted_table)

        # Extract images (simplified - DOCX image extraction is complex)
        images = self._extract_images(doc, doc_id)
        
        return DocumentSchema(
            metadata=metadata,
            sections=sections,
            tables=tables,
            lists=lists,
            images=images
        )
    
    def supports_filetype(self, filetype: str) -> bool:
        """Check if supports DOCX files"""
        return filetype.lower() in ['.docx', 'docx']
    
    def _extract_metadata(self, doc: Document, file_path: str, doc_id: str) -> DocumentMetadata:
        """Extract document metadata"""
        core_props = doc.core_properties
        
        return DocumentMetadata(
            title=core_props.title or os.path.basename(file_path),
            author=core_props.author or "",
            date=core_props.created.isoformat() if core_props.created else "",
            source_path=file_path,
            doc_id=doc_id,
            filetype="docx",
            pages=1  # DOCX doesn't have clear page concept
        )
    
    def _extract_table(self, table: Table, table_num: int) -> DocumentTable:
        """Extract table data"""
        headers = []
        rows = []
        
        if table.rows:
            # First row as headers
            headers = [cell.text.strip() for cell in table.rows[0].cells]
            
            # Remaining rows as data
            for row in table.rows[1:]:
                row_data = [cell.text.strip() for cell in row.cells]
                rows.append(row_data)
        
        return DocumentTable(
            table_id=f"table_{table_num}",
            headers=headers,
            rows=rows,
            source_section="",
            page=1
        )
    
    def _extract_images(self, doc: Document, doc_id: str) -> List[DocumentImage]:
        """Extract images from DOCX (simplified implementation)"""
        images = []
        # Note: Full DOCX image extraction requires more complex implementation
        # This is a placeholder for the structure
        return images