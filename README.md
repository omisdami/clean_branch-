# Automated Document Preparation System

## Project Description
This project focuses on automating document preparation by combining reference documents, user inputs, and iterative human instructions.

The system:
- Parses and extracts relevant data from reference documents (PDF, DOCX).
- Generates draft reports based on predefined JSON templates.
- Incorporates user inputs and feedback to iteratively improve document content.
- Enables end-to-end automated drafting of professional documents like technical reports or proposals.

---

## Installation Instructions

1. **Clone the repository**  
   ```bash
   git clone <your-repo-url>
   cd <repo-folder>
   ```

2. **Create and activate a virtual environment**  
   ```bash
   conda create -n auto-report-gen python=3.11.4
   conda activate auto-report-gen
   ```

3. **Install required libraries**  
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up your API key in a `.env` file**  
   ```env
   OPENAI_API_KEY=your_api_key_here
   ```

---


## Usage Guide

1. **Activate the virtual environment**  
   ```bash
   conda activate auto-report-gen
   ```

2. **Run the application**  
   ```bash
   python run.py
   ```

3. **Typical workflow**
   - Upload your reference materials.  
     *(Sample documents: `company_overview.pdf` and `SOW.docx`)*  
   - Click **Generate Report**.  
   - The system **extracts, maps, and generates** a draft report.  
   - **Review the generated content**:  
     - If satisfied, **download as PDF or DOCX**.  
     - If not, **suggest changes for revision**.  
   - *(Optional)* **Rate the generated content**.

---

## Dependencies

- **Python 3.11.4**
- **Virtual environment** (Conda)
- **Libraries** (from `requirements.txt`), including:
  - `pyautogen`  
  - `ag2[openai]`  
  - `python-dotenv`  
  - `python-docx`  
  - `fpdf`  
  - `PyMuPDF`  
  - `python-multipart`  
  - `jinja2`  
  - `httpx`  
  - `fastapi`  
  - `uvicorn`  
  - `pytesseract`  
  - `Pillow`  
  - `pdfplumber`  
  - `tqdm`  
  - `docx2pdf`