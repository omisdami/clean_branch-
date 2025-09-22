import re
from typing import Optional, Tuple
import json

def clean_extracted_text(text):
    """
    Cleans and normalizes extracted document text:
    - Fixes common unicode issues (smart quotes, dashes, ellipses)
    - Removes excess newlines and merges broken lines
    - Normalizes spaces for consistent formatting

    Args:
        text (str): Raw text extracted from document.

    Returns:
        str: Cleaned and normalized text.
    """
    # Fix common unicode punctuation
    replacements = {
        "\u2019": "'",
        "\u2018": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2013": "-",
        "\u2014": "--",
        "\u2026": "...",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)

    # Normalize line breaks
    text = re.sub(r"\n{2,}", "\n", text)  # Multiple newlines → single
    text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)  # Single line breaks → space

    # Normalize whitespace
    text = re.sub(r"[ \t]+", " ", text).strip()

    return text

def get_company_name(structured_data: dict) -> Optional[str]:
    """
    Extracts the first available company name from the structured data.

    This function searches through all top-level sections in the structured_data dictionary
    and returns the value of the first "Company Name" key it encounters. Each section is 
    expected to be a dictionary containing optional metadata, including "Company Name".

    Args:
        structured_data (dict): A dictionary representing structured sections of a document.

    Returns:
        Optional[str]: The first company name found, or None if not present in any section.
    """
    for section in structured_data.values():
        if isinstance(section, dict):
            company_name = section.get("Company Name")
            if company_name:
                return company_name
    return None

def normalize_title_for_lookup(title: str) -> str:
    """
    Normalizes section titles for structured_data lookup.
    Ensures renamed 'Why Company A' sections still map to original key.
    """
    lower_title = title.lower().strip()

    # Normalize any "Why <something>" to original key
    if lower_title.startswith("why "):
        return "Why Company A"

    return title