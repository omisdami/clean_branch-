import math
from typing import List, Dict, Any, Optional
from rank_bm25 import BM25Okapi
from collections import defaultdict

from core.rag.vectorstore.base_vectorstore import BaseVectorStore
from core.rag.schema import RetrievalResult

class HybridRetriever:
    """Hybrid retrieval combining BM25 and vector search"""
    
    def __init__(self, vector_store: BaseVectorStore, alpha: float = 0.5):
        self.vector_store = vector_store
        self.alpha = alpha  # Weight for vector search (1-alpha for BM25)
        self.bm25_index = None
        self.bm25_docs = []
        self.bm25_metadata = []
        
        self._build_bm25_index()
    
    def retrieve(self, query: str, k: int = 10, doc_ids: Optional[List[str]] = None) -> List[RetrievalResult]:
        """Perform hybrid retrieval"""
        # Vector search
        vector_results = self.vector_store.similarity_search(query, k=k*2, doc_ids=doc_ids)
        
        # BM25 search
        bm25_results = self._bm25_search(query, k=k*2, doc_ids=doc_ids)
        
        # Combine and re-rank
        combined_results = self._combine_results(vector_results, bm25_results)
        
        # Apply MMR for diversity
        final_results = self._apply_mmr(combined_results, query, k)
        
        return final_results
    
    def _build_bm25_index(self):
        """Build BM25 index from vector store metadata"""
        try:
            # Get all documents from vector store
            stats = self.vector_store.get_stats()
            if stats['total_chunks'] == 0:
                return
            
            # For FAISS store, we need to access metadata directly
            if hasattr(self.vector_store, 'metadata'):
                self.bm25_docs = []
                self.bm25_metadata = []
                
                for chunk_data in self.vector_store.metadata.values():
                    content = chunk_data['content']
                    # Tokenize for BM25
                    tokens = content.lower().split()
                    self.bm25_docs.append(tokens)
                    self.bm25_metadata.append(chunk_data)
                
                if self.bm25_docs:
                    self.bm25_index = BM25Okapi(self.bm25_docs)
        except Exception as e:
            print(f"Error building BM25 index: {e}")
            self.bm25_index = None
    
    def _bm25_search(self, query: str, k: int, doc_ids: Optional[List[str]] = None) -> List[RetrievalResult]:
        """Perform BM25 search"""
        if not self.bm25_index or not self.bm25_docs:
            return []
        
        query_tokens = query.lower().split()
        scores = self.bm25_index.get_scores(query_tokens)
        
        # Get top-k results
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
        
        results = []
        for idx in top_indices:
            if scores[idx] <= 0:
                continue
                
            chunk_data = self.bm25_metadata[idx]
            
            # Filter by doc_ids if specified
            if doc_ids and chunk_data['metadata']['doc_id'] not in doc_ids:
                continue
            
            result = RetrievalResult(
                content=chunk_data['content'],
                score=float(scores[idx]),
                metadata=chunk_data['metadata']
            )
            results.append(result)
        
        return results
    
    def _combine_results(self, vector_results: List[RetrievalResult], bm25_results: List[RetrievalResult]) -> List[RetrievalResult]:
        """Combine vector and BM25 results with weighted scoring"""
        # Normalize scores
        vector_results = self._normalize_scores(vector_results)
        bm25_results = self._normalize_scores(bm25_results)
        
        # Combine by chunk_id
        combined_scores = defaultdict(lambda: {'vector': 0, 'bm25': 0, 'result': None})
        
        for result in vector_results:
            chunk_id = result.metadata.chunk_id
            combined_scores[chunk_id]['vector'] = result.score
            combined_scores[chunk_id]['result'] = result
        
        for result in bm25_results:
            chunk_id = result.metadata.chunk_id
            combined_scores[chunk_id]['bm25'] = result.score
            if combined_scores[chunk_id]['result'] is None:
                combined_scores[chunk_id]['result'] = result
        
        # Calculate hybrid scores
        final_results = []
        for chunk_id, scores in combined_scores.items():
            hybrid_score = (self.alpha * scores['vector'] + 
                          (1 - self.alpha) * scores['bm25'])
            
            result = scores['result']
            result.score = hybrid_score
            final_results.append(result)
        
        # Sort by hybrid score
        final_results.sort(key=lambda x: x.score, reverse=True)
        return final_results
    
    def _normalize_scores(self, results: List[RetrievalResult]) -> List[RetrievalResult]:
        """Normalize scores to 0-1 range"""
        if not results:
            return results
        
        scores = [r.score for r in results]
        min_score = min(scores)
        max_score = max(scores)
        
        if max_score == min_score:
            for result in results:
                result.score = 1.0
        else:
            for result in results:
                result.score = (result.score - min_score) / (max_score - min_score)
        
        return results
    
    def _apply_mmr(self, results: List[RetrievalResult], query: str, k: int, lambda_param: float = 0.7) -> List[RetrievalResult]:
        """Apply Maximal Marginal Relevance for diversity"""
        if len(results) <= k:
            return results
        
        selected = []
        remaining = results.copy()
        
        # Select first result (highest score)
        if remaining:
            selected.append(remaining.pop(0))
        
        # Select remaining results using MMR
        while len(selected) < k and remaining:
            mmr_scores = []
            
            for candidate in remaining:
                # Relevance score
                relevance = candidate.score
                
                # Diversity score (minimum similarity to selected)
                max_similarity = 0
                for selected_result in selected:
                    similarity = self._calculate_similarity(candidate.content, selected_result.content)
                    max_similarity = max(max_similarity, similarity)
                
                # MMR score
                mmr_score = lambda_param * relevance - (1 - lambda_param) * max_similarity
                mmr_scores.append((mmr_score, candidate))
            
            # Select best MMR score
            mmr_scores.sort(key=lambda x: x[0], reverse=True)
            best_candidate = mmr_scores[0][1]
            selected.append(best_candidate)
            remaining.remove(best_candidate)
        
        return selected
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple similarity between two texts"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def update_index(self):
        """Update BM25 index when vector store changes"""
        self._build_bm25_index()