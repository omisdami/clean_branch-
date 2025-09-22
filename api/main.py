from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi import Form, HTTPException
import httpx

from api.endpoints import document
from api.endpoints import rag

app = FastAPI(title="AutoGen Document API")

app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")
app.mount("/static", StaticFiles(directory="static"), name="static")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(document.router, prefix="/documents")
app.include_router(rag.router, prefix="/rag")

# HTML template setup
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def serve_frontend(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/report-templates", response_class=HTMLResponse)
async def serve_report_template(request: Request):
    return templates.TemplateResponse("report_templates.html", {"request": request})

@app.get("/generate-report", response_class=HTMLResponse)
async def serve_new_report(request: Request):
    return templates.TemplateResponse("generate_report.html", {"request": request})

@app.post("/analyze", response_class=HTMLResponse)
async def analyze_form(
    request: Request,
    document_content: str = Form(...),
    question: str = Form(...)
):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://127.0.0.1:8000/documents/chat/",
                json={"document_content": document_content, "question": question}
            )
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.text)

            result = response.json()
            return templates.TemplateResponse("index.html", {
                "request": request,
                "answer": result["answer"],
                "document_content": document_content
            })

    except Exception as e:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "error": f"Failed to get chat response: {e}"
        })