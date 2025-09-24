import os
import json
import shutil
import tempfile
from typing import Dict, Any
from fastapi import UploadFile
from core.utils.text_utils import clean_extracted_text
from core.utils.text_extractor import extract_text
from core.rag.ingestion.heading_extractor import HeadingExtractor
from core.rag.ingestion.heading_extractor import HeadingExtractor

def generate_dynamic_report_structure(file_path: str) -> dict:
    """
    Generate report structure dynamically from document headings.
    Replaces static template loading.
    
    Args:
        file_path: Path to the document file
        
    Returns:
        Dynamic schema dict compatible with existing pipeline
    """
    heading_extractor = HeadingExtractor()
    
    # Extract sections from document
    sections = heading_extractor.extract_sections(file_path)
    
    if not sections:
        # Fallback: create a single section with full document content
        try:
            full_text = extract_and_clean_text(file_path)
            sections = {"Document Analysis": full_text}
        except Exception as e:
            print(f"Error extracting text: {e}")
            sections = {"Document Analysis": "Unable to extract document content"}
    
    # Generate schema from sections
    schema = heading_extractor.generate_section_schema(sections)
    
    print(f"[Dynamic Schema] Generated {len(schema)} sections: {list(schema.keys())}")
    
    return schema

def generate_dynamic_report_structure(file_path: str) -> dict:
    """
    Generate report structure dynamically from document headings.
    Replaces static template loading.
    
    Args:
        file_path: Path to the document file
        
    Returns:
        Dynamic schema dict compatible with existing pipeline
    """
    heading_extractor = HeadingExtractor()
    
    # Extract sections from document
    sections = heading_extractor.extract_sections(file_path)
    
    if not sections:
        # Fallback: create a single section with full document content
        try:
            full_text = extract_and_clean_text(file_path)
            sections = {"Document Analysis": full_text}
        except Exception as e:
            print(f"Error extracting text: {e}")
            sections = {"Document Analysis": "Unable to extract document content"}
    
    # Generate schema from sections
    schema = heading_extractor.generate_section_schema(sections)
    
    print(f"[Dynamic Schema] Generated {len(schema)} sections: {list(schema.keys())}")
    
    return schema

## File & Input Utilities
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
    
    def _is_docx_heading(self, paragraph) -> bool:
        """Check if DOCX paragraph is a heading"""
        # Check if it's a built-in heading style
        if paragraph.style.name.startswith('Heading'):
            return True
        
        # Check if it's bold and short (likely a heading)
        if paragraph.runs:
            first_run = paragraph.runs[0]
            text = paragraph.text.strip()
            if (first_run.bold and 
                len(text) < 100 and 
                not text.endswith('.') and
                len(text.split()) <= 10):
                return True
        
        # Check for numbering patterns
        text = paragraph.text.strip()
        if re.match(r'^\d+\.?\s+[A-Z]', text):  # "1. Title" or "1 Title"
            return True
        if re.match(r'^\d+\.\d+\.?\s+[A-Z]', text):  # "1.1 Title"
            return True
        if re.match(r'^[A-Z]\.?\s+[A-Z]', text):  # "A. Title"
            return True
        
        return False
    
    def _is_pdf_heading(self, span: dict, text: str) -> bool:
        """Check if PDF span is a heading"""
        # Check font size (headings are usually larger)
        font_size = span.get('size', 12)
        if font_size > 14:
            return True
        
        # Check if bold and short
        font_flags = span.get('flags', 0)
        is_bold = bool(font_flags & 2**4)  # Bold flag
        
        if (is_bold and 
            len(text) < 100 and 
            not text.endswith('.') and
            len(text.split()) <= 10):
            return True
        
        # Check for numbering patterns
        if re.match(r'^\d+\.?\s+[A-Z]', text):  # "1. Title"
            return True
        if re.match(r'^\d+\.\d+\.?\s+[A-Z]', text):  # "1.1 Title"
            return True
        if re.match(r'^[A-Z]\.?\s+[A-Z]', text):  # "A. Title"
            return True
        
        return False
    
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
def save_uploaded_file(file: UploadFile) -> str:
    """
    Saves the uploaded file to a temporary file path and returns the path.

    Args:
        file (UploadFile): The file uploaded via FastAPI endpoint.

    Returns:
        str: Path to the saved temporary file.

    Raises:
        ValueError: If the file type is not supported (PDF or DOCX).
    """
    _, ext = os.path.splitext(file.filename)
    if ext.lower() not in [".pdf", ".docx"]:
        raise ValueError("Unsupported file type")

    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp_file:
        shutil.copyfileobj(file.file, tmp_file)
        return tmp_file.name

def extract_and_clean_text(file_path: str) -> str:
    """
    Extracts raw text from a PDF or DOCX file and cleans it.

    1. Detects file type (PDF or DOCX).
    2. Extracts text, with OCR fallback for image-only PDFs.
    3. Cleans and normalizes the extracted text for further processing.

    Args:
        file_path (str): Path to the input document.

    Returns:
        str: Cleaned text extracted from the file.
    """
    raw_text = extract_text(file_path)

    if not raw_text.strip():
        # Return placeholder or raise warning if extraction fails
        return "[No extractable text found in the document.]"

    return clean_extracted_text(raw_text)

def load_report_structure(json_path: str) -> dict:
    """
    Loads the JSON-based report structure used for guiding extraction.

    Args:
        json_path (str): Path to the JSON template file.

    Returns:
        dict: Dictionary representation of the JSON structure.
    """
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)

## Extraction Phase
def extract_structured_data_dynamic(extracted_text: str, detected_headings: list, target_sections: list, extractor_agent, user_proxy):
    """
    Uses an extractor agent to map detected headings to target sections dynamically.
    
    Args:
        extracted_text (str): Cleaned raw text from the document.
        detected_headings (list): List of detected headings from document.
        target_sections (list): List of target section names for report.
        extractor_agent: AutoGen extractor agent responsible for parsing.
        user_proxy: Proxy agent to handle chat.

    Returns:
        dict: Dictionary mapping target sections to best matching content.
    """
    if not detected_headings or not target_sections:
        return {}

    # Create mapping using heading extractor
    heading_extractor = HeadingExtractor()
    section_mapping = heading_extractor.map_headings_to_sections(detected_headings, target_sections)
    
    # Prepare content for each target section
    structured_data = {}
    
    for target_section in target_sections:
        if target_section in section_mapping:
            mapped_heading = section_mapping[target_section]
            content = mapped_heading['content']
            
            # Use extractor agent to structure the content
            extraction_prompt = f"""
            You are extracting structured information for the section: "{target_section.replace('_', ' ').title()}"
            
            From the detected heading: "{mapped_heading['heading']}"
            
            Content:
            {content}
            
            Extract key facts and structure them as:
            {{
                "Company Name": "Value if found",
                "Key Fact 1": "Value",
                "Key Fact 2": "Value",
                ...
            }}
            
            Only include facts present in the content. End with TERMINATE.
            """
            
            chat = user_proxy.initiate_chat(
                extractor_agent,
                message={"content": extraction_prompt},
                human_input_mode="NEVER"
            )
            
            # Extract response
            final_texts = [
                msg["content"].strip()
                for msg in chat.chat_history
                if msg.get("name") == "extractor_agent" and msg["content"].strip() != "TERMINATE"
            ]
            
            if final_texts:
                try:
                    from ast import literal_eval
                    cleaned_output = final_texts[-1].split("TERMINATE")[0].strip()
                    section_data = literal_eval(cleaned_output)
                    structured_data[target_section.replace('_', ' ').title()] = section_data
                except Exception as e:
                    print(f"Error parsing data for {target_section}: {e}")
                    structured_data[target_section.replace('_', ' ').title()] = {"content": content}
    
    return structured_data

def extract_structured_data(extracted_text: str, sections: dict, extractor_agent, user_proxy, section_filter: list[str] = None):
    """
    Legacy function - maintained for backward compatibility.
    Uses an extractor agent to map extracted text into structured section-wise data.
    """
    section_titles = []
    for key, section in sections.items():
        if "subsections" in section:
            for _, sub in section["subsections"].items():
                if not section_filter or sub["title"] in section_filter:
                    section_titles.append(sub["title"])
        else:
            if not section_filter or section["title"] in section_filter:
                section_titles.append(section["title"])

    if not section_titles:
        return {}

    section_list = "\n".join([f"- {title}" for title in section_titles])

    extraction_prompt = f"""
        You are a skilled **Document Extractor Agent**.

        You are provided with a document and a list of section titles.

        Your task is to extract relevant information from the document and organize it by section title, following these rules:

        1. Always provide a dictionary for **every section title**, even if the document does not have a literal matching heading.
        2. If the section does not explicitly exist in the document, **infer its content** using the most relevant facts that fulfill its intent.  
        - Example: "Why Company A" can be inferred from company overview, differentiators, proven impact, or any content that explains why the company is a strong partner.
        3. Structure the output as JSON-style, like:
            {{
                "Section Title 1": {{
                    "Company Name": "Value",
                    "Key Fact": "Value",
                    ...
                }},
                ...
            }}
        4. Always include `"Company Name"` in every section.
        5. Only include facts from the document (no outside knowledge).
        6. End your message with **TERMINATE**.

        Section Titles:
        {section_list}

        --- START DOCUMENT ---
        {extracted_text}
        --- END DOCUMENT ---
    """

    chat = user_proxy.initiate_chat(
        extractor_agent,
        message={"content": extraction_prompt},
        human_input_mode="NEVER"
    )

    final_texts = [
        msg["content"].strip()
        for msg in chat.chat_history
        if msg.get("name") == "extractor_agent" and msg["content"].strip() != "TERMINATE"
    ]
    final_output = final_texts[-1] if final_texts else "{}"
    
    try:
        from ast import literal_eval
        cleaned_output = final_output.split("TERMINATE")[0].strip()
        structured_data = literal_eval(cleaned_output)
    except Exception as e:
        structured_data = {}
        print("Error parsing extracted data:", e)

    return structured_data