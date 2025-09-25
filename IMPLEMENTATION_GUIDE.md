# RAG System Implementation Guide

## Overview
This guide provides comprehensive instructions for implementing and using the upgraded RAG (Retrieval-Augmented Generation) system. The system has been transformed from a simple document processing tool into a full-featured RAG pipeline with advanced retrieval, chunking, generation capabilities, universal document structure support, and dynamic heading detection.

## System Architecture

### Core Components

1. **Ingestion Pipeline** (`core/rag/ingestion/`)
   - Document extractors for PDF and DOCX files
   - Dynamic heading detection for any document structure
   - Universal schema conversion
   - Table, image, and text extraction with OCR support

2. **Chunking System** (`core/rag/chunking/`)
   - Hierarchical, heading-aware text chunking
   - Configurable token limits with overlap
   - Special handling for tables, figures, and images

3. **Vector Store** (`core/rag/vectorstore/`)
   - FAISS-based vector storage with extensible architecture
   - Embedding generation using OpenAI's text-embedding-3-large
   - Metadata preservation for citations

4. **Retrieval System** (`core/rag/retrieval/`)
   - Hybrid retrieval combining BM25 keyword search and vector similarity
   - Maximal Marginal Relevance (MMR) for result diversity
   - Configurable re-ranking capabilities

5. **Generation System** (`core/rag/generation/`)
   - Structured report generation with multiple sections
   - Direct question answering with confidence scoring
   - Citation tracking and numeric fidelity preservation

## Installation and Setup

### 1. Environment Setup

```bash
# Install new dependencies
pip install -r requirements.txt

# For macOS users - install LibreOffice for PDF conversion (recommended)
brew install --cask libreoffice

# For Linux users
sudo apt-get install libreoffice

# Copy environment configuration
cp .env.example .env

# Edit .env with your OpenAI API key
OPENAI_API_KEY=your_api_key_here
```

### 2. Directory Structure
The system will automatically create these directories:
- `data/structured/` - Stores extracted document schemas
- `data/index/` - Vector store indices and metadata
- `outputs/` - Generated reports and documents

### 3. Configuration
Key configuration options in `.env`:

```bash
# For macOS users - install LibreOffice for PDF conversion (recommended)
brew install --cask libreoffice

# For Linux users
sudo apt-get install libreoffice

# Embedding model (OpenAI)
EMBEDDING_MODEL=text-embedding-3-large

# Vector store type
VECTOR_STORE=faiss

# Chunking parameters
MAX_CHUNK_TOKENS=1600
CHUNK_OVERLAP_TOKENS=160

# Retrieval parameters
TOP_K=10
USE_RERANKER=false
```

## API Endpoints

### 1. Document Ingestion
**POST** `/rag/ingest`

Upload and process documents into the RAG system.

```bash
curl -X POST "http://localhost:8000/rag/ingest" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@document.pdf"
```

**Response:**
```json
{
  "message": "Document ingested successfully",
  "doc_id": "uuid-string",
  "title": "Document Title",
  "pages": 25,
  "chunk_count": 45,
  "ingestion_time": "2025-01-06T10:30:00"
}
```

### 2. Question Answering
**POST** `/rag/ask`

Ask questions about ingested documents.

```bash
curl -X POST "http://localhost:8000/rag/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the main risks mentioned in the document?",
    "doc_ids": ["uuid-string"],
    "audience": "technical"
  }'
```

**Response:**
```json
{
  "query": "What are the main risks mentioned?",
  "answer": "Based on the documents, the main risks include...",
  "confidence": "high",
  "citations": [
    {
      "doc_id": "uuid-string",
      "page": 15,
      "section": "Risk Assessment",
      "chunk_id": "section_3_chunk_2",
      "content_preview": "The primary risks identified..."
    }
  ],
  "total_sources": 3
}
```

### 3. Report Generation
**POST** `/rag/report`

Generate structured reports from ingested documents.

```bash
curl -X POST "http://localhost:8000/rag/report" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Provide analysis of financial performance",
    "doc_ids": ["uuid-string"],
    "style": "professional",
    "length": "medium",
    "sections": ["Executive Summary", "Key Findings", "Recommendations"]
  }'
```

**Response:**
```json
{
  "query": "Provide analysis of financial performance",
  "sections": {
    "Executive Summary": "The financial analysis reveals...",
    "Key Findings": "• Revenue increased by 15%\n• Costs reduced by 8%...",
    "Recommendations": "1. Continue cost optimization\n2. Expand market presence..."
  },
  "citations": [...],
  "metadata": {
    "style": "professional",
    "length": "medium",
    "total_sources": 5
  }
}
```

### 4. System Status
**GET** `/rag/status`

Check system health and statistics.

```bash
curl "http://localhost:8000/rag/status"
```

**Response:**
```json
{
  "status": "operational",
  "vector_store": {
    "type": "faiss",
    "total_chunks": 1250,
    "doc_count": 15,
    "index_size_mb": 45.2
  },
  "structured_documents": 15,
  "config": {
    "embedding_model": "text-embedding-3-large",
    "max_chunk_tokens": 1600,
    "chunk_overlap_tokens": 160,
    "top_k": 10
  }
}
```

### 5. Document Deletion
**DELETE** `/rag/documents?doc_ids=uuid1&doc_ids=uuid2`

Remove documents from the system.

```bash
curl -X DELETE "http://localhost:8000/rag/documents?doc_ids=uuid-string"
```

## Usage Examples

### Basic Workflow

1. **Ingest Documents**
```python
import requests

# Upload a document
with open('report.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/rag/ingest',
        files={'file': f}
    )
doc_info = response.json()
doc_id = doc_info['doc_id']
```

2. **Ask Questions**
```python
# Ask a specific question
response = requests.post(
    'http://localhost:8000/rag/ask',
    json={
        'query': 'What is the projected revenue for next quarter?',
        'doc_ids': [doc_id]
    }
)
answer = response.json()
print(f"Answer: {answer['answer']}")
print(f"Confidence: {answer['confidence']}")
```

3. **Generate Reports**
```python
# Generate a comprehensive report
response = requests.post(
    'http://localhost:8000/rag/report',
    json={
        'query': 'Analyze the business performance and provide recommendations',
        'doc_ids': [doc_id],
        'style': 'executive',
        'sections': ['Executive Summary', 'Key Findings', 'Risks & Mitigations', 'Recommendations']
    }
)
report = response.json()
```

## Advanced Features

### Dynamic Heading Detection
The system automatically detects headings in any document:

```python
from core.rag.ingestion.heading_extractor import HeadingExtractor

extractor = HeadingExtractor()

# Extract headings from DOCX
from docx import Document
doc = Document('document.docx')
headings = extractor.extract_docx_headings(doc)

# Extract headings from PDF
headings = extractor.extract_pdf_headings('document.pdf')

# Map to target sections
target_sections = ['executive_summary', 'scope_of_work', 'risks']
mapping = extractor.map_headings_to_sections(headings, target_sections)
```

### Cross-Platform PDF Conversion
Check available conversion methods:

```python
from core.utils.pdf_converter import get_conversion_info

info = get_conversion_info()
print(f"Platform: {info['platform']}")
print(f"Available converters: {info['available_converters']}")
```

### Dynamic Heading Detection
The system automatically detects headings in any document:

```python
from core.rag.ingestion.heading_extractor import HeadingExtractor

extractor = HeadingExtractor()

# Extract headings from DOCX
from docx import Document
doc = Document('document.docx')
headings = extractor.extract_docx_headings(doc)

# Extract headings from PDF
headings = extractor.extract_pdf_headings('document.pdf')

# Map to target sections
target_sections = ['executive_summary', 'scope_of_work', 'risks']
mapping = extractor.map_headings_to_sections(headings, target_sections)
```

### Cross-Platform PDF Conversion
Check available conversion methods:

```python
from core.utils.pdf_converter import get_conversion_info

info = get_conversion_info()
print(f"Platform: {info['platform']}")
print(f"Available converters: {info['available_converters']}")
```

### Custom Extractors
Add support for new document types:

```python
from core.rag.ingestion.base_extractor import BaseExtractor
from core.rag.ingestion.extractor_factory import ExtractorFactory

class CustomExtractor(BaseExtractor):
    def extract(self, file_path: str) -> DocumentSchema:
        # Implementation
        pass
    
    def supports_filetype(self, filetype: str) -> bool:
        return filetype.lower() == 'custom'

# Register the extractor
ExtractorFactory.register_extractor('custom', CustomExtractor)
```

### Custom Vector Stores
Implement alternative vector stores:

```python
from core.rag.vectorstore.base_vectorstore import BaseVectorStore
from core.rag.vectorstore.vectorstore_factory import VectorStoreFactory

class ChromaVectorStore(BaseVectorStore):
    # Implementation
    pass

# Register the store
VectorStoreFactory.register_store('chroma', ChromaVectorStore)
```

## Testing

Run the test suite:

```bash
# Run all tests
python -m pytest tests/

# Run specific test categories
python -m pytest tests/test_ingestion.py
python -m pytest tests/test_chunking.py
python -m pytest tests/test_retrieval.py
```

## Performance Optimization

### Chunking Optimization
- Adjust `MAX_CHUNK_TOKENS` based on your use case
- Increase `CHUNK_OVERLAP_TOKENS` for better context preservation
- Use smaller chunks for precise retrieval, larger for comprehensive context

### Retrieval Tuning
- Increase `TOP_K` for more comprehensive retrieval
- Enable re-ranking for improved relevance
- Adjust hybrid retrieval weights in `HybridRetriever`

### Vector Store Scaling
- For large document collections, consider distributed vector stores
- Monitor index size and query performance
- Implement periodic index optimization

## Troubleshooting

### Common Issues

1. **PDF Conversion Fails on macOS**
   - Install LibreOffice: `brew install --cask libreoffice`
   - Alternative: Install Pandoc: `brew install pandoc`
   - System continues without PDF if conversion fails

2. **Document Structure Not Recognized**
   - System now detects headings dynamically
   - Check detected headings in response: `doc_info['detected_headings']`
   - Verify heading patterns match expected formats

1. **PDF Conversion Fails on macOS**
   - Install LibreOffice: `brew install --cask libreoffice`
   - Alternative: Install Pandoc: `brew install pandoc`
   - System continues without PDF if conversion fails

2. **Document Structure Not Recognized**
   - System now detects headings dynamically
   - Check detected headings in response: `doc_info['detected_headings']`
   - Verify heading patterns match expected formats

1. **Out of Memory Errors**
   - Reduce `MAX_CHUNK_TOKENS`
   - Process documents in smaller batches
   - Increase system memory or use distributed processing

2. **Poor Retrieval Quality**
   - Check embedding model compatibility
   - Verify document preprocessing quality
   - Adjust retrieval parameters

3. **Slow Performance**
   - Enable GPU acceleration for FAISS
   - Optimize chunk sizes
   - Consider caching frequently accessed embeddings

### Debugging

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Check system status:
```bash
curl "http://localhost:8000/rag/status"
```

## Migration from Legacy System

The enhanced RAG system maintains backward compatibility with existing endpoints while adding new capabilities:

1. **Existing `/documents/process/` endpoint** - Still functional
2. **New `/rag/ingest` endpoint** - Enhanced with RAG capabilities
3. **Dynamic heading detection** - Works with any document structure
3. **Dynamic heading detection** - Works with any document structure
3. **Document templates** - Can be converted to RAG queries
4. **Generated reports** - Now include citations and confidence scores
5. **Cross-platform support** - Reliable PDF conversion on all platforms
5. **Cross-platform support** - Reliable PDF conversion on all platforms

## Security Considerations

1. **API Key Management** - Store OpenAI API keys securely
2. **File Upload Validation** - System validates file types and sizes
3. **Data Privacy** - Documents are processed locally, only embeddings sent to OpenAI
4. **Access Control** - Implement authentication for production deployments

## Monitoring and Maintenance

### Health Checks
- Monitor `/rag/status` endpoint
- Track vector store size and performance
- Monitor embedding API usage and costs

### Regular Maintenance
- Clean up old document indices
- Update embedding models as needed
- Backup vector store indices
- Monitor disk space usage

## Support and Extensions

The RAG system is designed for extensibility:
- Add new document extractors
- Implement custom vector stores
- Create specialized report generators
- Integrate with external knowledge bases

For additional support or custom implementations, refer to the codebase documentation and test examples.