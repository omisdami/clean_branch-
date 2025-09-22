import tiktoken
from typing import List, Dict, Any
from core.rag.schema import DocumentSchema, DocumentSection, ChunkMetadata

class TextChunker:
    """Hierarchical text chunker with heading awareness"""
    
    def __init__(self, max_tokens: int = 1600, overlap_tokens: int = 160, model: str = "gpt-4"):
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens
        self.encoding = tiktoken.encoding_for_model(model)
    
    def chunk_document(self, document: DocumentSchema) -> List[Dict[str, Any]]:
        """Chunk document into overlapping segments with metadata"""
        chunks = []
        
        for section in document.sections:
            section_chunks = self._chunk_section(section, document.metadata.doc_id)
            chunks.extend(section_chunks)
        
        # Add special chunks for tables, figures, images
        chunks.extend(self._create_table_chunks(document))
        chunks.extend(self._create_figure_chunks(document))
        chunks.extend(self._create_image_chunks(document))
        
        return chunks
    
    def _chunk_section(self, section: DocumentSection, doc_id: str) -> List[Dict[str, Any]]:
        """Chunk a single section"""
        chunks = []
        
        if not section.content.strip():
            return chunks
        
        # Tokenize the content
        tokens = self.encoding.encode(section.content)
        
        if len(tokens) <= self.max_tokens:
            # Section fits in one chunk
            chunk = {
                'content': section.content,
                'metadata': ChunkMetadata(
                    doc_id=doc_id,
                    chunk_id=f"{section.section_id}_chunk_1",
                    page_start=section.page_start,
                    page_end=section.page_end,
                    section_id=section.section_id,
                    heading_chain=[section.title],
                    chunk_type="text",
                    token_count=len(tokens)
                )
            }
            chunks.append(chunk)
        else:
            # Split into multiple chunks with overlap
            chunk_num = 1
            start_idx = 0
            
            while start_idx < len(tokens):
                end_idx = min(start_idx + self.max_tokens, len(tokens))
                chunk_tokens = tokens[start_idx:end_idx]
                chunk_content = self.encoding.decode(chunk_tokens)
                
                chunk = {
                    'content': chunk_content,
                    'metadata': ChunkMetadata(
                        doc_id=doc_id,
                        chunk_id=f"{section.section_id}_chunk_{chunk_num}",
                        page_start=section.page_start,
                        page_end=section.page_end,
                        section_id=section.section_id,
                        heading_chain=[section.title],
                        chunk_type="text",
                        token_count=len(chunk_tokens)
                    )
                }
                chunks.append(chunk)
                
                # Move start position with overlap
                start_idx = end_idx - self.overlap_tokens
                chunk_num += 1
        
        return chunks
    
    def _create_table_chunks(self, document: DocumentSchema) -> List[Dict[str, Any]]:
        """Create chunks for tables"""
        chunks = []
        
        for table in document.tables:
            # Convert table to markdown format
            content = self._table_to_markdown(table)
            
            chunk = {
                'content': content,
                'metadata': ChunkMetadata(
                    doc_id=document.metadata.doc_id,
                    chunk_id=f"{table.table_id}_chunk",
                    page_start=table.page,
                    page_end=table.page,
                    section_id=table.source_section or "tables",
                    heading_chain=[table.title or f"Table {table.table_id}"],
                    chunk_type="table",
                    token_count=len(self.encoding.encode(content))
                )
            }
            chunks.append(chunk)
        
        return chunks
    
    def _create_figure_chunks(self, document: DocumentSchema) -> List[Dict[str, Any]]:
        """Create chunks for figures"""
        chunks = []
        
        for figure in document.figures:
            content = f"Figure: {figure.title or figure.figure_id}\n"
            if figure.caption:
                content += f"Caption: {figure.caption}\n"
            content += f"Type: {figure.figure_type}"
            
            chunk = {
                'content': content,
                'metadata': ChunkMetadata(
                    doc_id=document.metadata.doc_id,
                    chunk_id=f"{figure.figure_id}_chunk",
                    page_start=figure.page,
                    page_end=figure.page,
                    section_id=figure.source_section or "figures",
                    heading_chain=[figure.title or f"Figure {figure.figure_id}"],
                    chunk_type="figure",
                    token_count=len(self.encoding.encode(content))
                )
            }
            chunks.append(chunk)
        
        return chunks
    
    def _create_image_chunks(self, document: DocumentSchema) -> List[Dict[str, Any]]:
        """Create chunks for images with OCR text"""
        chunks = []
        
        for image in document.images:
            content = f"Image: {image.filename}\n"
            if image.alt_text:
                content += f"Alt text: {image.alt_text}\n"
            if image.extracted_text:
                content += f"Extracted text: {image.extracted_text}"
            
            chunk = {
                'content': content,
                'metadata': ChunkMetadata(
                    doc_id=document.metadata.doc_id,
                    chunk_id=f"{image.image_id}_chunk",
                    page_start=image.page,
                    page_end=image.page,
                    section_id=image.source_section or "images",
                    heading_chain=[f"Image {image.image_id}"],
                    chunk_type="image",
                    token_count=len(self.encoding.encode(content))
                )
            }
            chunks.append(chunk)
        
        return chunks
    
    def _table_to_markdown(self, table) -> str:
        """Convert table to markdown format"""
        if not table.headers and not table.rows:
            return f"Table {table.table_id}: No data"
        
        content = f"Table: {table.title or table.table_id}\n\n"
        
        if table.headers:
            content += "| " + " | ".join(table.headers) + " |\n"
            content += "| " + " | ".join(["---"] * len(table.headers)) + " |\n"
        
        for row in table.rows:
            content += "| " + " | ".join(row) + " |\n"
        
        return content