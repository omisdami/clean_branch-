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
    
    def extract_sections(self, file_path: str) -> Dict[str, str]:
        """
        Extract sections from document with heading as key and content as value.
        This is the main method for dynamic document processing.
        
        Args:
            file_path: Path to document file
            
        Returns:
            Dict mapping section headings to their content
        """
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        
        if ext == '.docx':
            return self._extract_docx_sections(file_path)
        elif ext == '.pdf':
            return self._extract_pdf_sections(file_path)
        else:
            # Fallback: treat as plain text
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return {"Document Content": content}
            except:
                return {"Document Content": "Unable to extract content"}
    
    def _extract_docx_sections(self, file_path: str) -> Dict[str, str]:
        """Extract sections from DOCX file"""
        try:
            from docx import Document
            doc = Document(file_path)
            
            sections = {}
            current_heading = None
            current_content = []
            
            for paragraph in doc.paragraphs:
                text = paragraph.text.strip()
                if not text:
                    continue
                
                # Check if this paragraph is a heading
                if self._is_docx_heading(paragraph):
                    # Save previous section if exists
                    if current_heading and current_content:
                        sections[current_heading] = '\n'.join(current_content).strip()
                    
                    # Start new section
                    current_heading = text
                    current_content = []
                else:
                    # Add to current section content
                    if current_heading:
                        current_content.append(text)
                    else:
                        # Content before first heading
                        if "Introduction" not in sections:
                            sections["Introduction"] = ""
                        sections["Introduction"] += text + "\n"
            
            # Save final section
            if current_heading and current_content:
                sections[current_heading] = '\n'.join(current_content).strip()
            
            # Fallback if no sections found
            if not sections:
                full_text = '\n'.join([p.text for p in doc.paragraphs if p.text.strip()])
                sections["Document Content"] = full_text
            
            return sections
            
        except Exception as e:
            print(f"Error extracting DOCX sections: {e}")
            return {"Document Content": "Error extracting content"}
    
    def _extract_pdf_sections(self, file_path: str) -> Dict[str, str]:
        """Extract sections from PDF file"""
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(file_path)
            
            sections = {}
            current_heading = None
            current_content = []
            
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
                                    if current_heading and current_content:
                                        sections[current_heading] = ' '.join(current_content).strip()
                                    
                                    # Start new section
                                    current_heading = text
                                    current_content = []
                                else:
                                    # Add to current section content
                                    if current_heading:
                                        current_content.append(text)
                                    else:
                                        # Content before first heading
                                        if "Introduction" not in sections:
                                            sections["Introduction"] = ""
                                        sections["Introduction"] += text + " "
            
            # Save final section
            if current_heading and current_content:
                sections[current_heading] = ' '.join(current_content).strip()
            
            # Fallback if no sections found
            if not sections:
                full_text = ""
                for page_num in range(len(doc)):
                    page = doc[page_num]
                    full_text += page.get_text() + "\n"
                sections["Document Content"] = full_text.strip()
            
            doc.close()
            return sections
            
        except Exception as e:
            print(f"Error extracting PDF sections: {e}")
            return {"Document Content": "Error extracting content"}
    
    def generate_section_schema(self, sections: Dict[str, str]) -> Dict[str, Any]:
        """
        Generate a dynamic schema from extracted sections.
        Each section gets default instructions for processing.
        
        Args:
            sections: Dict of section_name -> content
            
        Returns:
            Schema dict compatible with existing pipeline
        """
        schema = {}
        
        for section_name, content in sections.items():
            # Clean section name for use as key
            section_key = section_name.lower().replace(' ', '_').replace('.', '').replace(':', '')
            
            # Determine appropriate instructions based on section name
            instructions = self._get_section_instructions(section_name)
            
            schema[section_key] = {
                "title": section_name,
                "source": "dynamic",  # Indicates this was auto-detected
                "instructions": instructions,
                "content": ""  # Will be filled by drafting agent
            }
        
        return schema
    
    def _get_section_instructions(self, section_name: str) -> Dict[str, str]:
        """Get appropriate instructions based on section name"""
        section_lower = section_name.lower()
        
        # Executive summary type sections
        if any(word in section_lower for word in ['summary', 'executive', 'overview', 'introduction']):
            return {
                "objective": "Provide a clear and concise summary of this section, highlighting the key points and main ideas.",
                "tone": "Professional and informative",
                "length": "2-3 paragraphs, 150-200 words",
                "format": "Paragraph form with clear, flowing sentences"
            }
        
        # Scope/methodology sections
        elif any(word in section_lower for word in ['scope', 'methodology', 'approach', 'method']):
            return {
                "objective": "Clearly outline the scope, methodology, or approach described in this section with specific details and steps.",
                "tone": "Technical and precise",
                "length": "2-4 paragraphs, 200-300 words",
                "format": "Structured paragraphs with numbered or bulleted sub-points where appropriate"
            }
        
        # Risk/challenge sections
        elif any(word in section_lower for word in ['risk', 'challenge', 'issue', 'problem']):
            return {
                "objective": "Identify and explain the risks, challenges, or issues presented, along with any mitigation strategies mentioned.",
                "tone": "Analytical and solution-focused",
                "length": "2-3 paragraphs, 150-250 words",
                "format": "Clear identification of issues followed by proposed solutions or mitigations"
            }
        
        # Findings/results sections
        elif any(word in section_lower for word in ['finding', 'result', 'conclusion', 'outcome']):
            return {
                "objective": "Present the key findings, results, or conclusions from this section with supporting details and evidence.",
                "tone": "Factual and evidence-based",
                "length": "2-4 paragraphs, 200-300 words",
                "format": "Structured presentation of findings with supporting data or examples"
            }
        
        # Recommendation sections
        elif any(word in section_lower for word in ['recommendation', 'suggestion', 'next steps', 'action']):
            return {
                "objective": "Clearly present the recommendations, suggestions, or next steps outlined in this section.",
                "tone": "Actionable and directive",
                "length": "2-3 paragraphs, 150-250 words",
                "format": "Clear, actionable recommendations with rationale and expected outcomes"
            }
        
        # Default instructions for any other section
        else:
            return {
                "objective": f"Summarize and present the key information from the '{section_name}' section in a clear and organized manner.",
                "tone": "Professional and informative",
                "length": "2-3 paragraphs, 150-250 words",
                "format": "Well-structured paragraphs that clearly convey the main points and important details"
            }
    
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