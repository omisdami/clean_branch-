import os
from typing import Optional
from pydantic import BaseSettings

class RAGConfig(BaseSettings):
    """Configuration for RAG system"""
    
    # OpenAI Configuration
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    
    # Embedding Configuration
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")
    
    # Vector Store Configuration
    vector_store: str = os.getenv("VECTOR_STORE", "faiss")
    
    # Chunking Configuration
    max_chunk_tokens: int = int(os.getenv("MAX_CHUNK_TOKENS", "1600"))
    chunk_overlap_tokens: int = int(os.getenv("CHUNK_OVERLAP_TOKENS", "160"))
    
    # Retrieval Configuration
    top_k: int = int(os.getenv("TOP_K", "10"))
    use_reranker: bool = os.getenv("USE_RERANKER", "false").lower() == "true"
    reranker_model: str = os.getenv("RERANKER_MODEL", "bge-reranker-large")
    
    # Directory Configuration
    data_dir: str = os.getenv("DATA_DIR", "data")
    structured_dir: str = os.getenv("STRUCTURED_DIR", "data/structured")
    index_dir: str = os.getenv("INDEX_DIR", "data/index")
    
    # OCR Configuration
    tesseract_cmd: str = os.getenv("TESSERACT_CMD", "tesseract")
    
    class Config:
        env_file = ".env"

def get_rag_config() -> RAGConfig:
    """Get RAG configuration instance"""
    return RAGConfig()