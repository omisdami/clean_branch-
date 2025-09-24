import os
import json
import shutil
import tempfile
from typing import Dict, Any
from fastapi import UploadFile
from core.utils.text_utils import clean_extracted_text
from core.utils.text_extractor import extract_text
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

## File & Input Utilities
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