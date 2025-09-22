from core.agents.extractor_agent import get_extractor_agent
from core.agents.user_proxy_agent import get_user_proxy_agent
from core.utils.file_utils import save_report
from core.utils.text_extractor import extract_text
from core.utils.text_utils import clean_extracted_text
from datetime import datetime
import os

def run_extraction(file_path, llm_config, return_content=False):
    """
    Runs the document extraction workflow using AutoGen agents.

    Args:
        file_path (str): Path to the document (PDF or DOCX).
        llm_config (dict): LLM configuration for agent setup.
        return_content (bool): If True, return the cleaned report content.

    Returns:
        str or None: Cleaned report content if return_content is True.
    """
    extractor = get_extractor_agent(llm_config)
    user_proxy = get_user_proxy_agent(llm_config)

    print(f"Extracting text from: {file_path}")
    extracted_text = extract_text(file_path)

    chat_result = user_proxy.initiate_chat(
        extractor, message={"content": extracted_text}
    )

    for msg in reversed(chat_result.chat_history):
        if msg["role"] == "assistant":
            content = msg.get("content", "").strip()
            if content and content != "TERMINATE":
                cleaned_content = clean_extracted_text(content)
                report_data = {
                    "agent": extractor.name,
                    "timestamp": datetime.now().isoformat(),
                    "source_file": os.path.basename(file_path),
                    "report": content
                }
                path = save_report(report_data)
                print(f"\nExtracted report saved as: {path}")
                
                if return_content:
                    return cleaned_content  # For UI usage
                else:
                    return 

    print("No assistant message found to save.")
    return None
