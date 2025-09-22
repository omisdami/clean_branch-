import json
from typing import Dict, Any, List
from core.utils.text_utils import normalize_title_for_lookup

def flatten_report_sections(structure: dict) -> dict:
    """
    Flattens a nested report structure (sections/subsections) into a single-level dictionary,
    including parent section titles for subsections.

    Args:
        structure (dict): The structured report with potential nested subsections.

    Returns:
        dict: A flat dictionary with each key pointing to a section or subsection containing
              title, content, and for subsections, the parent section title.
    """
    flat = {}
    for key, val in structure.items():
        if "subsections" in val:
            # This is a parent section with subsections
            parent_title = val.get("title", "")
            for sub_key, sub_val in val["subsections"].items():
                flat[sub_key] = {
                    "title": sub_val["title"],
                    "content": sub_val["content"],
                    "parent_title": parent_title  # Add parent section title here
                }
        else:
            # Regular section without subsections
            flat[key] = {
                "title": val["title"],
                "content": val["content"]
            }
    return flat

# Drafting Phase
def generate_section_text(title, instructions, relevant_data, section_writer_agent, user_proxy):
    """
    Generates draft text for a single section using the drafting agent.

    Args:
        title (str): Section title.
        instructions (dict): Drafting instructions including tone, format, and focus.
        relevant_data (dict): Structured content to guide drafting.
        section_writer_agent: AutoGen drafting agent.
        user_proxy: Proxy to facilitate chat with agent.

    Returns:
        str: Generated section content.
    """
    # Extract additional instruction keys with defaults if missing
    focus_points = instructions.get("details", {}).get("focus", [])
    avoid_points = instructions.get("details", {}).get("avoid", [])
    style_guidance = instructions.get("details", {}).get("style_guidance", "")

    # Format focus and avoid lists as bullet points text for the prompt
    focus_text = "\n".join(f"- {point}" for point in focus_points) if focus_points else "None"
    avoid_text = "\n".join(f"- {point}" for point in avoid_points) if avoid_points else "None"

    section_prompt = f"""
        You are assigned to write a section titled: **{title}**

        Instructions:
        - Objective: {instructions['objective']}
        - Tone: {instructions['tone']}
        - Length: {instructions['length']}
        - Format: {instructions['format']}

        Here is the structured information extracted for this section:
        {json.dumps(relevant_data, indent=2)}

        **Important:** Based only on this data, write a clean and professional section draft.
        Avoid commentary, apologies, or repetition. Return only the drafted section, no explanations.

        End your response with the word: TERMINATE
    """

    chat = user_proxy.initiate_chat(
        section_writer_agent,
        message={"content": section_prompt},
        human_input_mode="NEVER"
    )

    final_texts = [
        msg["content"].strip()
        for msg in chat.chat_history
        if msg.get("name") == "drafting_agent" and msg["content"].strip() != "TERMINATE"
    ]

    return final_texts[-1] if final_texts else "[No content generated]"


def prepare_batch_drafting_prompts(sections: dict, structured_data: dict) -> str:
    """
    Prepares a single batch prompt that contains instructions and data for all sections/subsections.

    Args:
        sections (dict): Report structure with section titles and instructions.
        structured_data (dict): Extracted structured content keyed by section title.

    Returns:
        str: Fully formatted batch prompt for the drafting agent.
    """

    prompt = """
        You are assigned to draft multiple sections of a report. For each section, follow the specified instructions strictly and use only the structured data provided.

        For every section:
        - Write **only** the draft content.
        - Do **not** include commentary, explanations, or apologies.
        - End each section with the marker: === END OF SECTION ===

    """

    for key, val in sections.items():
        if "subsections" in val:
            for sub_key, sub_val in val["subsections"].items():
                title = sub_val["title"]
                instructions = sub_val["instructions"]
                lookup_title = normalize_title_for_lookup(title)
                data = structured_data.get(lookup_title, {}) 

                section_block = f"""
                    SECTION: {title}
                    Objective: {instructions['objective']}
                    Tone: {instructions['tone']}
                    Length: {instructions['length']}
                    Format: {instructions['format']}

                    Structured Data:
                    {json.dumps(data, indent=2)}

                    === END OF SECTION ===

                """
                prompt += section_block

        else:
            title = val["title"]
            instructions = val["instructions"]
            lookup_title = normalize_title_for_lookup(title)
            data = structured_data.get(lookup_title, {})

            section_block = f"""
                SECTION: {title}
                Objective: {instructions['objective']}
                Tone: {instructions['tone']}
                Length: {instructions['length']}
                Format: {instructions['format']}

                Structured Data:
                {json.dumps(data, indent=2)}

                === END OF SECTION ===
            """
            prompt += section_block

    return prompt.strip()

def generate_batch_draft_texts(draft_inputs: list, drafting_agent, user_proxy) -> list:
    """
    Generates drafts for multiple sections in one batch using a combined prompt.

    Args:
        draft_inputs (list): List of section data dicts with title, instructions, and relevant data.
        drafting_agent: AutoGen drafting agent.
        user_proxy: Proxy agent to mediate chat.

    Returns:
        list: List of dicts with `title` and `content` for each generated section.
    """

    # Create a fake `sections` dict with the same structure expected by prepare_batch_drafting_prompts
    fake_sections = {}
    structured_data = {}

    for i, item in enumerate(draft_inputs):
        section_key = f"section_{i}"
        fake_sections[section_key] = {
            "title": item["title"],
            "instructions": item["instructions"]
        }
        lookup_title = normalize_title_for_lookup(item["title"])
        structured_data[lookup_title] = item["relevant_data"]

    batch_prompt = prepare_batch_drafting_prompts(fake_sections, structured_data)

    chat = user_proxy.initiate_chat(
        drafting_agent,
        message={"content": batch_prompt},
        human_input_mode="NEVER"
    )

    full_response = ""
    for msg in chat.chat_history:
        if msg.get("name") == "drafting_agent":
            full_response += msg["content"].strip() + "\n"

    sections = full_response.split("=== END OF SECTION ===")
    results = []

    titles = [item["title"] for item in draft_inputs]

    for i, chunk in enumerate(sections):
        cleaned = chunk.strip()
        if not cleaned or i >= len(titles):
            continue
        results.append({
            "title": titles[i],
            "content": cleaned
        })

    return results
