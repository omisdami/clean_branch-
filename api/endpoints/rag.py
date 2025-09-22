import os
import tempfile
import shutil
from typing import List, Optional
from fastapi import APIRouter, File, UploadFile, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from core.rag.pipeline import RAGPipeline

router = APIRouter()

# Initialize RAG pipeline
rag_pipeline = RAGPipeline()

class AskRequest(BaseModel):
    """Request model for ask endpoint"""
    query: str
    doc_ids: Optional[List[str]] = None
    audience: Optional[str] = "general"

class ReportRequest(BaseModel):
    """Request model for report generation"""
    query: Optional[str] = ""
    doc_ids: Optional[List[str]] = None
    style: str = "professional"
    length: str = "medium"
    sections: Optional[List[str]] = None

@router.post("/ingest")
async def ingest_document(file: UploadFile = File(...)):
    """
    Ingest a document into the RAG system.
    
    Accepts PDF or DOCX files, extracts content, chunks it, and indexes it.
    Returns document metadata and ingestion statistics.
    """
    try:
        # Validate file type
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in ['.pdf', '.docx']:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type: {file_ext}. Only PDF and DOCX are supported."
            )
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
            shutil.copyfileobj(file.file, tmp_file)
            tmp_path = tmp_file.name
        
        try:
            # Ingest document
            result = rag_pipeline.ingest_document(tmp_path)
            
            return JSONResponse(content={
                "message": "Document ingested successfully",
                "doc_id": result["doc_id"],
                "title": result["title"],
                "pages": result["pages"],
                "chunk_count": result["chunk_count"],
                "ingestion_time": result["ingestion_time"]
            })
            
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

@router.post("/ask")
async def ask_question(request: AskRequest):
    """
    Ask a question and get a grounded answer with citations.
    
    Performs hybrid retrieval and generates an answer based on indexed documents.
    """
    try:
        if not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        result = rag_pipeline.ask_question(
            query=request.query,
            doc_ids=request.doc_ids
        )
        
        return JSONResponse(content={
            "query": request.query,
            "answer": result["answer"],
            "confidence": result["confidence"],
            "citations": [citation.dict() for citation in result["citations"]],
            "total_sources": len(set(c.doc_id for c in result["citations"]))
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Question answering failed: {str(e)}")

@router.post("/report")
async def generate_report(request: ReportRequest):
    """
    Generate a structured multi-section report with citations.
    
    Creates a comprehensive report with executive summary, key findings,
    risks & mitigations, and recommendations.
    """
    try:
        result = rag_pipeline.generate_report(
            query=request.query,
            doc_ids=request.doc_ids,
            style=request.style,
            length=request.length,
            sections=request.sections
        )
        
        return JSONResponse(content={
            "query": result["query"],
            "sections": result["sections"],
            "citations": [citation.dict() for citation in result["citations"]],
            "metadata": result["metadata"]
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")

@router.get("/status")
async def get_status():
    """
    Get system status and statistics.
    
    Returns information about indexed documents, vector store status,
    and system configuration.
    """
    try:
        status = rag_pipeline.get_status()
        return JSONResponse(content=status)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")

@router.delete("/documents")
async def delete_documents(doc_ids: List[str] = Query(...)):
    """
    Delete documents from the RAG system.
    
    Removes documents from vector store and deletes structured files.
    """
    try:
        if not doc_ids:
            raise HTTPException(status_code=400, detail="No document IDs provided")
        
        result = rag_pipeline.delete_documents(doc_ids)
        
        return JSONResponse(content={
            "message": f"Deleted {len(result['deleted_doc_ids'])} documents",
            "deleted_doc_ids": result["deleted_doc_ids"],
            "deleted_files": result["deleted_files"],
            "timestamp": result["timestamp"]
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document deletion failed: {str(e)}")