import os
from docx import Document
import fitz
from PIL import Image
import pytesseract
import io

def extract_text_from_pdf(path: str) -> str:
    """
    Extracts text from PDF.
    1. Extracts selectable text directly using PyMuPDF.
    2. Falls back to OCR for image-only pages using pytesseract.
    """
    doc = fitz.open(path)
    text = ""

    for page in doc:
        # Try direct text extraction first
        page_text = page.get_text("text").strip()
        if page_text:
            text += page_text + "\n"
        else:
            # Fallback: OCR for scanned pages
            pix = page.get_pixmap()
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            ocr_text = pytesseract.image_to_string(img)
            text += ocr_text.strip() + "\n"

    return text.strip()

def extract_text_from_docx(path):
    """
    Extracts text from a Word document (.docx) using python-docx.
    """
    doc = Document(path)
    return "\n".join([para.text for para in doc.paragraphs])

def extract_text(path):
    """
    Determines file type and extracts text from PDF or DOCX.
    """
    ext = os.path.splitext(path)[-1].lower()
    
    if ext == ".pdf":
        return extract_text_from_pdf(path)
    elif ext == ".docx":
        return extract_text_from_docx(path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")