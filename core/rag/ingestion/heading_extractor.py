import re
from typing import List, Dict, Any, Tuple
from docx import Document
from docx.shared import Pt
import fitz  # PyMuPDF

class HeadingExtractor:
    """Extract headings dynamically from documents"""
    
    def __init__(self):
        # Common heading patterns
        self.numbered_patterns = [
            r'^\d+\.\s+',           # 1. 2. 3.
            r'^\d+\.\d+\s+',        # 1.1 1.2 2.1
            r'^\d+\.\d+\.\d+\s+',   # 1.1.1 1.1.2
            r'^[A-Z]\.\s+',         # A. B. C.
            r'^[IVX]+\.\s+',        # I. II. III.
            r'^\([a-z]\)\s+',       # (a) (b) (c)
            r'^\(\d+\)\s+',         # (1) (2) (3)
        ]
        
        # Common heading keywords that indicate sections
        self.heading_keywords = [
            'introduction', 'overview', 'summary', 'background', 'purpose',
            'scope', 'objectives', 'methodology', 'approach', 'findings',
            'results', 'analysis', 'discussion', 'conclusion', 'recommendations',
            'risks', 'mitigation', 'timeline', 'budget', 'resources',
            'deliverables', 'assumptions', 'constraints', 'appendix'
        ]
    
    def extract_docx_headings(self, doc: Document) -> List[Dict[str, Any]]:
        """Extract headings from DOCX document"""
        headings = []
        current_content = ""
        current_heading = None
        section_counter = 0
        
        for paragraph in doc.paragraphs:
            # Check if paragraph is a heading based on style
            if self._is_docx_heading(paragraph):
                # Save previous section if exists
                if current_heading:
                    headings.append({
                        'heading': current_heading['text'],
                        'level': current_heading['level'],
                        'content': current_content.strip(),
                        'page_start': 1,  # DOCX doesn't have clear page breaks
                        'page_end': 1,
                        'section_id': f"sec_{section_counter:03d}"
                    })
                    section_counter += 1
                
                # Start new section
                level = self._get_docx_heading_level(paragraph)
                current_heading = {
                    'text': paragraph.text.strip(),
                    'level': level
                }
                current_content = ""
            else:
                # Add to current section content
                if paragraph.text.strip():
                    current_content += paragraph.text + "\n"
        
        # Add final section
        if current_heading:
            headings.append({
                'heading': current_heading['text'],
                'level': current_heading['level'],
                'content': current_content.strip(),
                'page_start': 1,
                'page_end': 1,
                'section_id': f"sec_{section_counter:03d}"
            })
        
        # If no headings found, create a default section
        if not headings and current_content.strip():
            headings.append({
                'heading': 'Document Content',
                'level': 1,
                'content': current_content.strip(),
                'page_start': 1,
                'page_end': 1,
                'section_id': 'sec_001'
            })
        
        return headings
    
    def extract_pdf_headings(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Extract headings from PDF document"""
        doc = fitz.open(pdf_path)
        headings = []
        current_content = ""
        current_heading = None
        section_counter = 0
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            blocks = page.get_text("dict")["blocks"]
            
            for block in blocks:
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            text = span["text"].strip()
                            if not text:
                                continue
                            
                            # Check if this looks like a heading
                            if self._is_pdf_heading(span, text):
                                # Save previous section
                                if current_heading:
                                    headings.append({
                                        'heading': current_heading['text'],
                                        'level': current_heading['level'],
                                        'content': current_content.strip(),
                                        'page_start': current_heading['page_start'],
                                        'page_end': page_num + 1,
                                        'section_id': f"sec_{section_counter:03d}"
                                    })
                                    section_counter += 1
                                
                                # Start new section
                                level = self._get_pdf_heading_level(span, text)
                                current_heading = {
                                    'text': text,
                                    'level': level,
                                    'page_start': page_num + 1
                                }
                                current_content = ""
                            else:
                                # Add to current section content
                                current_content += text + " "
        
        # Add final section
        if current_heading:
            headings.append({
                'heading': current_heading['text'],
                'level': current_heading['level'],
                'content': current_content.strip(),
                'page_start': current_heading['page_start'],
                'page_end': len(doc),
                'section_id': f"sec_{section_counter:03d}"
            })
        
        # If no headings found, create a default section
        if not headings and current_content.strip():
            headings.append({
                'heading': 'Document Content',
                'level': 1,
                'content': current_content.strip(),
                'page_start': 1,
                'page_end': len(doc),
                'section_id': 'sec_001'
            })
        
        doc.close()
        return headings
    
    def _is_docx_heading(self, paragraph) -> bool:
        """Check if DOCX paragraph is a heading"""
        # Check style name
        if paragraph.style.name.startswith('Heading'):
            return True
        
        # Check if text matches heading patterns
        text = paragraph.text.strip()
        if not text:
            return False
        
        # Check numbered patterns
        for pattern in self.numbered_patterns:
            if re.match(pattern, text):
                return True
        
        # Check if it's short and contains heading keywords
        if len(text) < 100 and any(keyword in text.lower() for keyword in self.heading_keywords):
            return True
        
        # Check formatting (bold, larger font)
        if paragraph.runs:
            first_run = paragraph.runs[0]
            if first_run.bold and len(text) < 100:
                return True
        
        return False
    
    def _is_pdf_heading(self, span: Dict, text: str) -> bool:
        """Check if PDF span is a heading"""
        if not text or len(text) > 200:
            return False
        
        font_size = span.get("size", 12)
        font_flags = span.get("flags", 0)
        
        # Check if font is larger than normal (assuming 12pt is normal)
        if font_size > 14:
            return True
        
        # Check if text is bold (font flags & 16 = bold)
        if font_flags & 16 and len(text) < 100:
            return True
        
        # Check numbered patterns
        for pattern in self.numbered_patterns:
            if re.match(pattern, text):
                return True
        
        # Check heading keywords
        if any(keyword in text.lower() for keyword in self.heading_keywords):
            return True
        
        return False
    
    def _get_docx_heading_level(self, paragraph) -> int:
        """Get heading level from DOCX paragraph"""
        style_name = paragraph.style.name
        
        # Extract level from style name
        if 'Heading' in style_name:
            match = re.search(r'Heading (\d+)', style_name)
            if match:
                return int(match.group(1))
        
        # Determine level from text pattern
        text = paragraph.text.strip()
        
        # Level 1: Simple numbers (1., 2., 3.)
        if re.match(r'^\d+\.\s+', text):
            return 1
        
        # Level 2: Decimal numbers (1.1, 1.2)
        if re.match(r'^\d+\.\d+\s+', text):
            return 2
        
        # Level 3: Triple decimal (1.1.1)
        if re.match(r'^\d+\.\d+\.\d+\s+', text):
            return 3
        
        return 1
    
    def _get_pdf_heading_level(self, span: Dict, text: str) -> int:
        """Get heading level from PDF span"""
        font_size = span.get("size", 12)
        
        # Determine level based on font size
        if font_size >= 18:
            return 1
        elif font_size >= 16:
            return 2
        elif font_size >= 14:
            return 3
        
        # Determine level from text pattern
        if re.match(r'^\d+\.\s+', text):
            return 1
        elif re.match(r'^\d+\.\d+\s+', text):
            return 2
        elif re.match(r'^\d+\.\d+\.\d+\s+', text):
            return 3
        
        return 1
    
    def map_headings_to_sections(self, headings: List[Dict], target_sections: List[str]) -> Dict[str, Dict]:
        """Map detected headings to target report sections"""
        mapping = {}
        
        # Create mapping rules
        section_mappings = {
            'executive_summary': ['executive summary', 'summary', 'overview', 'introduction'],
            'value_proposition': ['value proposition', 'benefits', 'advantages', 'value'],
            'scope_of_work': ['scope', 'work scope', 'project scope', 'deliverables'],
            'methodology': ['methodology', 'approach', 'method', 'process'],
            'risks': ['risks', 'risk assessment', 'challenges', 'issues'],
            'recommendations': ['recommendations', 'next steps', 'action items', 'conclusion']
        }
        
        for target_section in target_sections:
            best_match = None
            best_score = 0
            
            # Look for exact or close matches
            for heading in headings:
                heading_text = heading['heading'].lower()
                
                # Check if target section has mapping rules
                if target_section in section_mappings:
                    keywords = section_mappings[target_section]
                    for keyword in keywords:
                        if keyword in heading_text:
                            score = len(keyword) / len(heading_text)
                            if score > best_score:
                                best_match = heading
                                best_score = score
                
                # Direct match check
                if target_section.replace('_', ' ') in heading_text:
                    best_match = heading
                    break
            
            if best_match:
                mapping[target_section] = best_match
            else:
                # Fallback: use all content for summarization
                all_content = "\n\n".join([h['content'] for h in headings])
                mapping[target_section] = {
                    'heading': f"Summarized {target_section.replace('_', ' ').title()}",
                    'level': 1,
                    'content': all_content,
                    'page_start': 1,
                    'page_end': headings[-1]['page_end'] if headings else 1,
                    'section_id': f"summarized_{target_section}"
                }
        
        return mapping