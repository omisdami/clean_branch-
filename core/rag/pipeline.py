import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

from core.rag.ingestion.extractor_factory import ExtractorFactory
from core.rag.chunking.text_chunker import TextChunker
from core.rag.vectorstore.vectorstore_factory import VectorStoreFactory
from core.rag.retrieval.hybrid_retriever import HybridRetriever
from core.rag.generation.report_generator import ReportGenerator
from core.rag.schema import DocumentSchema
from core.config.rag_config import get_rag_config

class RAGPipeline:
    """Main RAG pipeline orchestrator"""
    
    def __init__(self):
        self.config = get_rag_config()
        
        # Initialize components
        self.chunker = TextChunker(
            max_tokens=self.config.max_chunk_tokens,
            overlap_tokens=self.config.chunk_overlap_tokens
        )
        self.vector_store = VectorStoreFactory.create_vectorstore()
        self.retriever = HybridRetriever(self.vector_store)
        self.generator = ReportGenerator()
        
        # Ensure directories exist
        os.makedirs(self.config.data_dir, exist_ok=True)
        os.makedirs(self.config.structured_dir, exist_ok=True)
        os.makedirs(self.config.index_dir, exist_ok=True)
    
    def ingest_document(self, file_path: str) -> Dict[str, Any]:
        """Ingest a document through the full pipeline"""
        
        # Step 1: Extract content
        extractor = ExtractorFactory.get_extractor(file_path)
        if not extractor:
            raise ValueError(f"No extractor available for file: {file_path}")
        
        document = extractor.extract(file_path)
        
        # Step 2: Save structured document
        structured_path = os.path.join(
            self.config.structured_dir, 
            f"{document.metadata.doc_id}.json"
        )
        with open(structured_path, 'w') as f:
            json.dump(document.dict(), f, indent=2)
        
        # Step 3: Chunk document
        chunks = self.chunker.chunk_document(document)
        
        # Step 4: Add to vector store
        self.vector_store.add_documents(chunks)
        
        # Step 5: Update retriever index
        self.retriever.update_index()
        
        return {
            "doc_id": document.metadata.doc_id,
            "title": document.metadata.title,
            "pages": document.metadata.pages,
            "chunk_count": len(chunks),
            "structured_path": structured_path,
            "ingestion_time": datetime.now().isoformat()
        }
    
    def ask_question(self, 
                    query: str, 
                    doc_ids: Optional[List[str]] = None,
                    k: int = None) -> Dict[str, Any]:
        """Ask a question and get grounded answer"""
        
        k = k or self.config.top_k
        
        # Retrieve relevant documents
        retrieved_docs = self.retriever.retrieve(query, k=k, doc_ids=doc_ids)
        
        # Generate answer
        result = self.generator.generate_answer(query, retrieved_docs)
        
        return result
    
    def generate_report(self,
                       query: str = "",
                       doc_ids: Optional[List[str]] = None,
                       style: str = "professional",
                       length: str = "medium",
                       sections: Optional[List[str]] = None) -> Dict[str, Any]:
        """Generate structured report"""
        
        # If no query provided, use generic report query
        if not query:
            query = "Provide a comprehensive analysis of the key information, findings, and recommendations from the documents."
        
        # Retrieve relevant documents
        retrieved_docs = self.retriever.retrieve(query, k=20, doc_ids=doc_ids)
        
        # Generate report
        report = self.generator.generate_report(
            query, retrieved_docs, style, length, sections
        )
        
        return report
    
    def get_status(self) -> Dict[str, Any]:
        """Get system status"""
        
        vector_stats = self.vector_store.get_stats()
        
        # Count structured documents
        structured_files = 0
        if os.path.exists(self.config.structured_dir):
            structured_files = len([f for f in os.listdir(self.config.structured_dir) if f.endswith('.json')])
        
        return {
            "status": "operational",
            "vector_store": {
                "type": self.config.vector_store,
                "total_chunks": vector_stats.get('total_chunks', 0),
                "doc_count": vector_stats.get('doc_count', 0),
                "index_size_mb": vector_stats.get('index_size_mb', 0)
            },
            "structured_documents": structured_files,
            "config": {
                "embedding_model": self.config.embedding_model,
                "max_chunk_tokens": self.config.max_chunk_tokens,
                "chunk_overlap_tokens": self.config.chunk_overlap_tokens,
                "top_k": self.config.top_k
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def delete_documents(self, doc_ids: List[str]) -> Dict[str, Any]:
        """Delete documents from the system"""
        
        # Remove from vector store
        self.vector_store.delete_documents(doc_ids)
        
        # Remove structured files
        deleted_files = []
        for doc_id in doc_ids:
            structured_path = os.path.join(self.config.structured_dir, f"{doc_id}.json")
            if os.path.exists(structured_path):
                os.remove(structured_path)
                deleted_files.append(structured_path)
        
        # Update retriever
        self.retriever.update_index()
        
        return {
            "deleted_doc_ids": doc_ids,
            "deleted_files": deleted_files,
            "timestamp": datetime.now().isoformat()
        }