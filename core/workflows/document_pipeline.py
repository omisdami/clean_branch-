from core.config.llm_config import get_llm_config
from core.agents.extractor_agent import get_extractor_agent
from core.agents.drafting_agent import get_drafting_agent
from core.agents.user_proxy_agent import get_user_proxy_agent
from core.utils.text_utils import get_company_name
from core.workflows.document_extraction import extract_structured_data
from core.workflows.document_drafting import generate_batch_draft_texts
from core.utils.file_utils import write_to_docx, save_report
from core.utils.text_utils import normalize_title_for_lookup
import os
from typing import Tuple, Dict
from datetime import datetime
from docx2pdf import convert

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

    convert(docx_path, pdf_path)

    return {
        "json_path": json_path,
        "docx_path": docx_path,
        "pdf_path": pdf_path
    }