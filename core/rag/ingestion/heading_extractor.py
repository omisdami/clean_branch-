from core.config.llm_config import get_llm_config
from core.agents.extractor_agent import get_extractor_agent
from core.agents.drafting_agent import get_drafting_agent
from core.agents.user_proxy_agent import get_user_proxy_agent
from core.utils.text_utils import get_company_name
from core.workflows.document_extraction import extract_structured_data
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
    
from core.workflows.document_drafting import generate_batch_draft_texts
from core.utils.file_utils import write_to_docx, save_report
from core.utils.text_utils import normalize_title_for_lookup
from core.utils.file_utils import safe_docx_to_pdf_conversion
import os
from typing import Tuple, Dict
from datetime import datetime

## Report Generation
def generate_report(sections: dict, extracted_text: dict[str, str], filename: str) -> Tuple[dict, str]:
    """
    Generates a structured and complete draft report based on extracted document text and section instructions.

    Args:
        sections (dict): Report structure including section/subsection titles and instructions.
        extracted_text (dict[str, str] | str): Cleaned text content extracted from uploaded document(s).
        filename (str): Name of the original file (can be used for reference or logging).

    Returns:
        Tuple[dict, str]: 
            - A structured dictionary representing the drafted report content section-by-section.
            - The full report as a concatenated string, ready for export or formatting.
    """

    # Load model configuration and initialize AutoGen agents
    llm_config = get_llm_config()
    extractor_agent = get_extractor_agent(llm_config)
    section_writer_agent = get_drafting_agent(llm_config)
    user_proxy = get_user_proxy_agent(llm_config)

    # --- Step 1: Per-file structured data extraction ---
    structured_cache = {}
    for file_name, text in extracted_text.items():
        # Extract for all sections, but limited to those referencing this file
        file_specific_sections = {}
        for key, sec in sections.items():
            if sec.get("source") == file_name:
                file_specific_sections[key] = sec
            elif "subsections" in sec:
                filtered_subs = {
                    sub_key: sub
                    for sub_key, sub in sec["subsections"].items()
                    if sub.get("source") == file_name
                }
                if filtered_subs:
                    file_specific_sections[key] = {
                        **sec,
                        "subsections": filtered_subs
                    }

        if file_specific_sections:
            print(f"[Extraction] Extracting structured data for file: {file_name}")
            print(file_specific_sections)
            structured_cache[file_name] = extract_structured_data(text, file_specific_sections, extractor_agent, user_proxy)
        else:
            print(f"[Extraction] No sections reference file: {file_name}. Skipping extraction.")

    # --- Step 2: Merge cache for company name detection ---
    merged_structured_data = {}
    for cache in structured_cache.values():
        for section_title, content in cache.items():
            merged_structured_data.setdefault(section_title, {}).update(content)

    company_name = get_company_name(merged_structured_data)
    if company_name and "why_company_a" in sections:
        sections["why_company_a"]["title"] = f"Why {company_name}"

    # --- Step 3: Prepare draft inputs ---
    draft_inputs = []
    key_mapping = {}

    # Build the input list for each section/subsection for batch drafting
    for section_key, section_data in sections.items():
        # Handle sections WITH subsections
        if "subsections" in section_data:
            for sub_key, sub_data in section_data["subsections"].items():

                display_title = sub_data["title"]
                lookup_title = normalize_title_for_lookup(display_title)

                # Choose source and fallback
                source_file = sub_data.get("source", section_data.get("source"))
                relevant_data = {}
                if source_file and source_file in structured_cache:
                    relevant_data = structured_cache[source_file].get(lookup_title, {})
                    print(f"[Subsection] Using cached extraction for '{display_title}' "
                            f"(lookup='{lookup_title}') from file '{source_file}'.")
                else:
                    relevant_data = merged_structured_data.get(lookup_title, {})
                    print(f"[Subsection] Using MERGED fallback for '{display_title}' "
                            f"(lookup='{lookup_title}').")
                
                if not relevant_data:
                    print(f"[Subsection] No extracted content found for '{display_title}'.")

                draft_inputs.append({
                    "title": display_title,
                    "instructions": sub_data["instructions"],
                    "relevant_data": relevant_data
                })
                key_mapping[display_title] = (section_key, sub_key)
        
        # Handle top-level sections WITHOUT subsections
        else:
            display_title = section_data["title"]
            lookup_title = normalize_title_for_lookup(display_title)
            
            source_file = section_data.get("source")
            if source_file and source_file in structured_cache:
                relevant_data = structured_cache[source_file].get(lookup_title, {})
                print(f"[Section] Using cached extraction for '{display_title}' "
                        f"(lookup='{lookup_title}') from file '{source_file}'.")
            else:
                relevant_data = merged_structured_data.get(lookup_title, {})
                print(f"[Section] Using MERGED fallback for '{display_title}' "
                    f"(lookup='{lookup_title}').")

            if not relevant_data:
                print(f"[Section] No extracted content found for '{display_title}'.")

            draft_inputs.append({
                "title": display_title,
                "instructions": section_data["instructions"],
                "relevant_data": relevant_data
            })
            key_mapping[display_title] = (section_key, None)

    # --- Step 4: Drafting phase ---
    drafted_outputs = generate_batch_draft_texts(draft_inputs, section_writer_agent, user_proxy)

    aggregated_report = {} # Final structured report dictionary
    full_report_text = "" # Full report as plain concatenated text

    # --- Step 5: Reconstruct report structure ---
    for draft in drafted_outputs:
        title = draft["title"]
        content = draft["content"]
        section_key, sub_key = key_mapping[title]

        if sub_key is not None:
            if section_key not in aggregated_report:
                aggregated_report[section_key] = {
                    "title": sections[section_key]["title"],
                    "subsections": {}
                }
            aggregated_report[section_key]["subsections"][sub_key] = {
                "title": title,
                "content": content
            }
        else:
            aggregated_report[section_key] = {
                "title": title,
                "content": content
            }

        full_report_text += content + "\n\n"

    return aggregated_report, full_report_text

def save_all_report_formats(aggregated_report: dict, full_report_text: str, filename: str) -> Dict[str, str]:
    """
    Saves the complete report into three formats: JSON, DOCX, and PDF.

    Args:
        aggregated_report (dict): Final structured report sections, ready for export.
        full_report_text (str): Flattened or full-body string version of the report used for PDF.
        filename (str): Original filename (used for naming output files).

    Returns:
        Dict[str, str]: A dictionary containing file paths for the saved JSON, DOCX, and PDF versions.
    """

    output_dir = "outputs"
    os.makedirs(output_dir, exist_ok=True)
   
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Save as JSON using a custom report-saving utility
    json_path = save_report({
        "agent": "extractor_agent",
        "timestamp": datetime.now().isoformat(),
        "source_file": filename,
        "report_sections": aggregated_report
    })

    # Define paths for DOCX and PDF outputs
    docx_path = os.path.join(output_dir, f"docx_report_{timestamp}.docx")
    pdf_path = os.path.join(output_dir, f"pdf_report_{timestamp}.pdf")

    # Save the DOCX version of the report
    write_to_docx(aggregated_report, filename=docx_path)

    # Use safe PDF conversion
    pdf_success = safe_docx_to_pdf_conversion(docx_path, pdf_path)
    if not pdf_success:
        print(f"Warning: PDF conversion failed. DOCX available at {docx_path}")
        # Return path anyway - frontend can handle missing PDF

    return {
        "json_path": json_path,
        "docx_path": docx_path,
        "pdf_path": pdf_path
    }