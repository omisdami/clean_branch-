import os
from datetime import datetime
from typing import List, Dict
from core.utils.file_utils import write_to_docx
from docx2pdf import convert

def build_revision_prompt(document: str, question: str) -> str:
    """
    Creates a prompt for the editor agent to revise the document based on a user's request.

    Args:
        document (str): The original document text.
        question (str): The user's instruction or revision request.

    Returns:
        str: A structured prompt containing the document and the question.
    """

    return f"""
        You are a document revision assistant. Your task is to revise the existing document content according to the user's request.

        Instructions:
        - Apply only the requested change. Do not modify unrelated content.
        - Return the **entire updated document** after applying the correction, but exclude any prompt markers like '--- DOCUMENT START ---' and '--- DOCUMENT END ---'.
        - Preserve the original document structure and formatting.
        - Do not explain your changes — only return the updated document as plain text.

        --- DOCUMENT START ---
        {document}
        --- DOCUMENT END ---

        User's question:
        {question}

        Return only the updated structured document.
        End your response with: TERMINATE
        """.strip()

def extract_editor_response(chat_history: list) -> str:
    """
    Extracts the revision content from the editor agent's response in the chat history.

    Args:
        chat_history (List[Dict]): List of messages exchanged between agents.

    Returns:
        str: The revised document content, excluding the 'TERMINATE' command.
    """
    
    for msg in chat_history:
        if msg.get("name") == "editor_agent" and msg["content"].strip() != "TERMINATE":
            return msg["content"].strip()
    return ""

def save_updated_outputs(content: str) -> dict:
    """
    Saves the revised content to both DOCX and PDF formats.

    Args:
        content (str): The updated document content.

    Returns:
        Dict[str, str]: File paths for the saved DOCX and PDF versions.
    """
    
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    base_name = f"updated_report_{timestamp}"
    output_dir = "outputs"
    os.makedirs(output_dir, exist_ok=True)

    docx_path = os.path.join(output_dir, f"{base_name}.docx")
    pdf_path = os.path.join(output_dir, f"{base_name}.pdf")

    section_outputs = {"chat_response": {"title": "", "content": content}}

    write_to_docx(section_outputs, filename=docx_path, mode="final")
    print(f"[DEBUG] DOCX saved to: {docx_path}")

    convert(docx_path, pdf_path)

    return {
        "docx_path": docx_path,
        "pdf_path": pdf_path
    }
