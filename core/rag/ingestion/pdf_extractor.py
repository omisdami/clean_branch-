import os
import uuid
import fitz  # PyMuPDF
import pdfplumber
from typing import List, Dict, Any
from PIL import Image
import pytesseract
import io

from core.rag.schema import (
    DocumentSchema, DocumentMetadata, DocumentSection, 
    DocumentTable, DocumentFigure, DocumentImage
)
from core.rag.ingestion.base_extractor import BaseExtractor

class PdfExtractor(BaseExtractor):
    """PDF document extractor"""
    
    def extract(self, file_path: str) -> DocumentSchema:
        """Extract content from PDF file"""
        doc_id = str(uuid.uuid4())
        
        # Use PyMuPDF for text and images, pdfplumber for tables
        pdf_doc = fitz.open(file_path)
        
        # Extract metadata
        metadata = self._extract_metadata(pdf_doc, file_path, doc_id)
        
        # Extract content
        sections = []
        tables = []
        figures = []
        images = []
        
        current_section = None
        section_counter = 0
        
        # Process each page
        for page_num in range(len(pdf_doc)):
            page = pdf_doc[page_num]
            
            # Extract text
            text = page.get_text()
            
            # Simple section detection based on font size/style
            blocks = page.get_text("dict")["blocks"]
            
            for block in blocks:
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            text_content = span["text"].strip()
                            font_size = span["size"]
                            
                            # Heuristic: larger font = heading
                            if font_size > 14 and len(text_content) < 100:
                                if current_section:
                                    sections.append(current_section)
                                
                                section_counter += 1
                                current_section = DocumentSection(
                                    section_id=f"section_{section_counter}",
                                    title=text_content,
                                    content="",
                                    page_start=page_num + 1,
                                    page_end=page_num + 1
                                )
                            else:
                                if current_section:
                                    current_section.content += text_content + " "
                                    current_section.page_end = page_num + 1
                                else:
                                    # Create default section
                                    current_section = DocumentSection(
                                        section_id="section_1",
                                        title="Document Content",
                                        content=text_content + " ",
                                        page_start=page_num + 1,
                                        page_end=page_num + 1
                                    )
            
            # Extract tables using pdfplumber
            page_tables = self._extract_tables_from_page(file_path, page_num)
            tables.extend(page_tables)
            
            # Extract images
            page_images = self._extract_images_from_page(page, page_num, doc_id)
            images.extend(page_images)
        
        # Add final section
        if current_section:
            sections.append(current_section)
        
        pdf_doc.close()
        
        return DocumentSchema(
            metadata=metadata,
            sections=sections,
            tables=tables,
            figures=figures,
            images=images
        )
    
    def supports_filetype(self, filetype: str) -> bool:
        """Check if supports PDF files"""
        return filetype.lower() in ['.pdf', 'pdf']
    
    def _extract_metadata(self, pdf_doc, file_path: str, doc_id: str) -> DocumentMetadata:
        """Extract PDF metadata"""
        metadata_dict = pdf_doc.metadata
        
        return DocumentMetadata(
            title=metadata_dict.get('title', os.path.basename(file_path)),
            author=metadata_dict.get('author', ''),
            date=metadata_dict.get('creationDate', ''),
            source_path=file_path,
            doc_id=doc_id,
            filetype="pdf",
            pages=len(pdf_doc)
        )
    
    def _extract_tables_from_page(self, file_path: str, page_num: int) -> List[DocumentTable]:
        """Extract tables from a specific page using pdfplumber"""
        tables = []
        
        try:
            with pdfplumber.open(file_path) as pdf:
                if page_num < len(pdf.pages):
                    page = pdf.pages[page_num]
                    page_tables = page.extract_tables()
                    
                    for i, table_data in enumerate(page_tables):
                        if table_data and len(table_data) > 0:
                            headers = table_data[0] if table_data[0] else []
                            rows = table_data[1:] if len(table_data) > 1 else []
                            
                            table = DocumentTable(
                                table_id=f"table_p{page_num + 1}_{i + 1}",
                                headers=[str(h) if h else "" for h in headers],
                                rows=[[str(cell) if cell else "" for cell in row] for row in rows],
                                source_section="",
                                page=page_num + 1
                            )
                            tables.append(table)
        except Exception as e:
            print(f"Error extracting tables from page {page_num}: {e}")
        
        return tables
    
    def _extract_images_from_page(self, page, page_num: int, doc_id: str) -> List[DocumentImage]:
        """Extract images from a PDF page"""
        images = []
        
        try:
            image_list = page.get_images()
            
            for img_index, img in enumerate(image_list):
                xref = img[0]
                pix = fitz.Pixmap(page.parent, xref)
                
                if pix.n - pix.alpha < 4:  # GRAY or RGB
                    img_data = pix.tobytes("png")
                    
                    # OCR the image
                    ocr_text = ""
                    try:
                        pil_image = Image.open(io.BytesIO(img_data))
                        ocr_text = pytesseract.image_to_string(pil_image)
                    except Exception as e:
                        print(f"OCR failed for image: {e}")
                    
                    image = DocumentImage(
                        image_id=f"img_{doc_id}_p{page_num + 1}_{img_index + 1}",
                        filename=f"image_p{page_num + 1}_{img_index + 1}.png",
                        extracted_text=ocr_text.strip(),
                        source_section="",
                        page=page_num + 1
                    )
                    images.append(image)
                
                pix = None
        except Exception as e:
            print(f"Error extracting images from page {page_num}: {e}")
        
        return images