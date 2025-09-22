import traceback
from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from core.config.llm_config import get_llm_config
from core.workflows.document_pipeline import generate_report, save_all_report_formats
from core.workflows.document_extraction import save_uploaded_file, extract_and_clean_text, load_report_structure
from core.workflows.document_drafting import flatten_report_sections
from core.workflows.document_editor import extract_editor_response, save_updated_outputs, build_revision_prompt
from core.agents.editor_agent import get_editor_agent
from core.agents.user_proxy_agent import get_user_proxy_agent
import os
import json
import uuid
from typing import List

router = APIRouter()
load_dotenv()

class ChatRequest(BaseModel):
    """
    Pydantic model for chat requests to the `/chat/` endpoint.

    Attributes:
        document_content (str): Full document text the user wants to ask about or modify.
        question (str): The user's specific question, instruction, or correction request.
    """
    document_content: str
    question: str

class FeedbackPayload(BaseModel):
    """
    Pydantic model for feedback submitted via the `/feedback/` endpoint.

    Attributes:
        uuid (str): Unique identifier of the processed document.
        rating (int): User rating from 1 to 5 (validated with Pydantic).
        feedback_type (str, optional): Auto-assigned type ("up", "down", or "neutral").
        document_content (str): Content of the document the feedback refers to.
        template_name (str): Name of the template used to generate the report.
        timestamp (str): Time when the feedback was submitted.
    """
    uuid: str
    rating: int = Field(..., ge=1, le=5)
    feedback_type: str = None
    document_content: str
    template_name: str
    timestamp: str

@router.get("/templates/")
async def list_templates():
    """
    Lists all available JSON template files stored in the `templates` directory.

    Returns:
        dict: A dictionary containing either:
            - "available_templates": List of JSON template filenames
            - "error": Error message if directory listing fails
    """
    template_dir = "templates"
    try:
        files = os.listdir(template_dir)    # Get all files from the templates directory
        json_files = [f for f in files if f.endswith(".json")]  # Filter only .json template files
        return {"available_templates": json_files}
    except Exception as e:
        return {"error": str(e)}    # Return error instead of raising HTTPException for template listing


@router.post("/process/")
async def process_document(files: List[UploadFile] = File(...),
    template_name: str = Form("proposal_template.json")):
    """
        Accepts multiple PDF or DOCX files, extracts their content,
        generates a structured report using AutoGen agents, and returns
        download links for the report in DOCX and PDF formats.

        Args:
            files (List[UploadFile]): Uploaded files to process.

        Returns:
            JSONResponse: Includes message, structured report, flattened version, and paths to saved outputs.
    """
    template_dir = "templates"
    try:
        template_files = os.listdir(template_dir)
        json_files = [f for f in template_files if f.endswith(".json")]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list templates: {str(e)}")

    if template_name not in json_files:
        raise HTTPException(status_code=400, detail="Invalid template name")

    # 1. Save all uploaded files and extract their text
    extracted_texts = {}
    for file in files:
        file_path = save_uploaded_file(file)
        text = extract_and_clean_text(file_path)
        extracted_texts[file.filename] = text

    # 3. Load JSON-based report structure template
    sections = load_report_structure(f"templates/{template_name}")

    # 4. Run the AutoGen agents to generate content per section
    aggregated_report, full_report_text = generate_report(
        sections,
        extracted_texts,
        "multiple_files_combined.docx"
    )

    document_id = str(uuid.uuid4())

    # 5. Save the report in different formats
    output_paths = save_all_report_formats(
        aggregated_report,
        full_report_text,
        "multiple_files_combined.docx"
    )

    # 6. Flatten report for frontend
    flattened = flatten_report_sections(aggregated_report)

    return JSONResponse(content={
        "message": "Full report successfully generated",
        "uuid": document_id,
        "report_sections": aggregated_report,
        "flattened_sections": flattened,
        **output_paths
    })

@router.post("/chat/")
async def chat_about_document(data: ChatRequest):
    """
    Sends the document content and user instruction to the Editor AI agent for
    review, corrections, or improvements. Returns the AI-generated response
    and updated output files.

    Args:
        data (ChatRequest): Pydantic model containing:
            - document_content (str): Full document content for review
            - question (str): User's instruction or query for the document

    Returns:
        dict: Contains:
            - "answer" (str): AI editor's response
            - "uuid" (str): New unique document identifier
            - Paths to updated outputs

    Raises:
        HTTPException: If any error occurs during the chat process.
    """

    try:
        # 1. Initialize LLM configuration and agents
        llm_config = get_llm_config()
        editor_agent = get_editor_agent(llm_config)
        user_proxy = get_user_proxy_agent(llm_config)

        # 2. Construct a revision prompt combining doc content + user request
        full_prompt = build_revision_prompt(data.document_content, data.question)

        # 3. Initiate chat with the editor agent via user proxy
        chat_result = user_proxy.initiate_chat(
            editor_agent,
            message={"content": full_prompt},
            human_input_mode="NEVER"
        )

        # 4. Extract the editor's structured response from chat history
        response = extract_editor_response(chat_result.chat_history)

        # 5. Save updated content to output formats
        output_paths = save_updated_outputs(response)

        # 6. Generate new document UUID for tracking
        new_uuid = str(uuid.uuid4())

        return {
            "answer": response,
            "uuid": new_uuid,
            **output_paths
        }

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Chat failed: {e}")

@router.post("/feedback/")
async def save_feedback(feedback: FeedbackPayload):
    """
    Saves user feedback about generated reports to a JSON log file.
    Feedback includes ratings, document content, and template used.

    Args:
        feedback (FeedbackPayload): Contains:
            - uuid (str): Document UUID
            - rating (int): 1 to 5 star rating
            - document_content (str): Content of the reviewed document
            - template_name (str): Template used for report generation
            - timestamp (str): Time feedback was submitted

    Returns:
        dict: Success message on successful feedback save.

    Raises:
        HTTPException: If writing to the feedback file fails.
    """
    try:
        feedback_dir = "feedback_data"  # Ensure feedback directory exists
        os.makedirs(feedback_dir, exist_ok=True)

        feedback_file = os.path.join(feedback_dir, "feedback_log.json")

        new_entry = feedback.dict() # Convert Pydantic model to dictionary

        # Map numeric rating to feedback type
        rating = new_entry.get("rating", 3)
        if rating in [4, 5]:
            new_entry["feedback_type"] = "up"
        elif rating in [1, 2]:
            new_entry["feedback_type"] = "down"
        else:
            new_entry["feedback_type"] = "neutral"

        # Load existing feedback if file exists
        if os.path.exists(feedback_file):
            with open(feedback_file, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
        else:
            existing_data = []

        existing_data.append(new_entry) # Append new feedback entry

        # Save updated feedback log
        with open(feedback_file, "w", encoding="utf-8") as f:
            json.dump(existing_data, f, indent=2)

        return {"message": "Feedback recorded successfully."}

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to save feedback: {e}")
