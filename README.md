# Automated Document Preparation System

**🚀 Now Enhanced with Full RAG (Retrieval-Augmented Generation) Capabilities!**

## Project Description
This project is a comprehensive RAG system that combines advanced document processing, semantic search, and AI-powered generation capabilities.

The system:
- **Ingests and processes** documents (PDF, DOCX) with advanced extraction including tables, images, and OCR
- **Chunks and indexes** content using hierarchical, heading-aware segmentation
- **Performs hybrid retrieval** combining BM25 keyword search and vector similarity
- **Generates grounded answers** to natural language questions with full citations
- **Creates structured reports** with executive summaries, key findings, and recommendations
- **Maintains source transparency** with comprehensive citation tracking

## 🆕 New RAG Features

### Question Answering
Ask natural language questions about your documents:
```bash
curl -X POST "http://localhost:8000/rag/ask" \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the main risks mentioned in the financial report?"}'
```

### Intelligent Report Generation
Generate comprehensive reports with citations:
```bash
curl -X POST "http://localhost:8000/rag/report" \
  -H "Content-Type: application/json" \
  -d '{
    "style": "executive",
    "sections": ["Executive Summary", "Key Findings", "Recommendations"]
  }'
```

### Document Ingestion
Process documents into the RAG system:
```bash
curl -X POST "http://localhost:8000/rag/ingest" \
  -F "file=@document.pdf"
```

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
   
   # RAG Configuration
   EMBEDDING_MODEL=text-embedding-3-large
   VECTOR_STORE=faiss
   MAX_CHUNK_TOKENS=1600
   CHUNK_OVERLAP_TOKENS=160
   TOP_K=10
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

3. **RAG System Workflow**
   
   **Option A: Use the Web Interface**
   - Navigate to `http://localhost:8000`
   - Upload documents and generate reports using the UI
   
   **Option B: Use the RAG API**
   
   a) **Ingest Documents**
   ```bash
   curl -X POST "http://localhost:8000/rag/ingest" \
     -F "file=@your_document.pdf"
   ```
   
   b) **Ask Questions**
   ```bash
   curl -X POST "http://localhost:8000/rag/ask" \
     -H "Content-Type: application/json" \
     -d '{"query": "What is the projected revenue growth?"}'
   ```
   
   c) **Generate Reports**
   ```bash
   curl -X POST "http://localhost:8000/rag/report" \
     -H "Content-Type: application/json" \
     -d '{
       "style": "professional",
       "sections": ["Executive Summary", "Key Findings", "Risks & Mitigations", "Recommendations"]
     }'
   ```
   
   d) **Check System Status**
   ```bash
   curl "http://localhost:8000/rag/status"
   ```

## 🔧 API Endpoints

### RAG System Endpoints
- `POST /rag/ingest` - Upload and process documents
- `POST /rag/ask` - Ask questions about documents  
- `POST /rag/report` - Generate structured reports
- `GET /rag/status` - System health and statistics
- `DELETE /rag/documents` - Remove documents

### Legacy Endpoints (Still Available)
- `POST /documents/process/` - Original document processing
- `POST /documents/chat/` - Document revision chat
- `POST /documents/feedback/` - User feedback collection

---

## Dependencies

- **Python 3.11.4**
- **Virtual environment** (Conda)
- **Core Libraries**:
  - `fastapi` - Web framework
  - `openai` - AI model access
  - `faiss-cpu` - Vector similarity search
  - `rank-bm25` - Keyword search
  - `tiktoken` - Token counting
  - `python-docx` - DOCX processing
  - `PyMuPDF` - PDF processing
  - `pdfplumber` - PDF table extraction
  - `pytesseract` - OCR capabilities
  - And more (see `requirements.txt`)

## 📊 System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Document      │    │    Chunking      │    │  Vector Store   │
│   Ingestion     │───▶│   & Indexing     │───▶│   (FAISS)       │
│  (PDF/DOCX)     │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Generated     │    │    Hybrid        │    │   Retrieval     │
│   Response      │◀───│   Retrieval      │◀───│   (BM25 +       │
│                 │    │  (Vector + BM25) │    │   Vector)       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Run all tests
python -m pytest tests/

# Run specific test categories
python -m pytest tests/test_ingestion.py    # Document extraction
python -m pytest tests/test_chunking.py     # Text chunking
python -m pytest tests/test_retrieval.py    # Search and retrieval
```

## 📚 Documentation

- **[Implementation Guide](IMPLEMENTATION_GUIDE.md)** - Comprehensive setup and usage guide
- **[Changelog](CHANGELOG.md)** - Detailed list of all changes and improvements
- **[API Documentation](http://localhost:8000/docs)** - Interactive API docs (when running)

## 🚀 Key Benefits

### Enhanced Capabilities
- **Semantic Search**: Find information by meaning, not just keywords
- **Question Answering**: Get direct answers to specific questions
- **Multi-Document Analysis**: Analyze across multiple documents simultaneously
- **Citation Tracking**: Full transparency of information sources

### Improved Accuracy
- **Grounded Responses**: All answers backed by source documents
- **Confidence Scoring**: Quality assessment of generated content
- **Numeric Fidelity**: Preserves exact numbers and units
- **Conflict Detection**: Identifies contradictory information

### Better Performance
- **Hybrid Retrieval**: Combines keyword and semantic search
- **Efficient Indexing**: Fast similarity search with FAISS
- **Smart Chunking**: Hierarchical, heading-aware text segmentation
- **Result Diversity**: MMR prevents redundant results

## 🔧 Configuration

Key configuration options in `.env`:

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_api_key_here
EMBEDDING_MODEL=text-embedding-3-large

# Vector Store
VECTOR_STORE=faiss

# Chunking Parameters
MAX_CHUNK_TOKENS=1600
CHUNK_OVERLAP_TOKENS=160

# Retrieval Parameters
TOP_K=10
USE_RERANKER=false
```

## 🛠️ Extending the System

The RAG system is designed for extensibility:

### Add New Document Types
```python
from core.rag.ingestion.base_extractor import BaseExtractor
from core.rag.ingestion.extractor_factory import ExtractorFactory

class CustomExtractor(BaseExtractor):
    def extract(self, file_path: str) -> DocumentSchema:
        # Your implementation
        pass

ExtractorFactory.register_extractor('custom', CustomExtractor)
```

### Add New Vector Stores
```python
from core.rag.vectorstore.base_vectorstore import BaseVectorStore
from core.rag.vectorstore.vectorstore_factory import VectorStoreFactory

class ChromaVectorStore(BaseVectorStore):
    # Your implementation
    pass

VectorStoreFactory.register_store('chroma', ChromaVectorStore)
```

## 📈 Monitoring

Check system health and performance:

```bash
curl "http://localhost:8000/rag/status"
```

Response includes:
- Vector store statistics
- Document count and index size
- Configuration settings
- System health status

---

## 🎯 Migration from Legacy System

The new RAG system maintains backward compatibility:
- Existing endpoints continue to work
- Gradual migration to new features
- Enhanced capabilities with same ease of use
- Comprehensive documentation for smooth transition