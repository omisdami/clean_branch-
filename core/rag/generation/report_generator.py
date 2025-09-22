from typing import List, Dict, Any, Optional
from openai import OpenAI
from core.rag.schema import RetrievalResult, Citation
from core.config.rag_config import get_rag_config

class ReportGenerator:
    """Generate structured reports from retrieved content"""
    
    def __init__(self):
        self.config = get_rag_config()
        self.client = OpenAI(api_key=self.config.openai_api_key)
    
    def generate_report(self, 
                       query: str,
                       retrieved_docs: List[RetrievalResult],
                       style: str = "professional",
                       length: str = "medium",
                       sections: Optional[List[str]] = None) -> Dict[str, Any]:
        """Generate structured report"""
        
        if not sections:
            sections = [
                "Executive Summary",
                "Key Findings", 
                "Risks & Mitigations",
                "Recommendations"
            ]
        
        # Generate each section
        report_sections = {}
        all_citations = []
        
        for section_name in sections:
            section_content, section_citations = self._generate_section(
                section_name, query, retrieved_docs, style, length
            )
            report_sections[section_name] = section_content
            all_citations.extend(section_citations)
        
        return {
            "query": query,
            "sections": report_sections,
            "citations": all_citations,
            "metadata": {
                "style": style,
                "length": length,
                "total_sources": len(set(c.doc_id for c in all_citations))
            }
        }
    
    def generate_answer(self, query: str, retrieved_docs: List[RetrievalResult]) -> Dict[str, Any]:
        """Generate direct answer to query"""
        
        if not retrieved_docs:
            return {
                "answer": "Not enough evidence found to answer the query.",
                "confidence": "low",
                "citations": []
            }
        
        # Prepare context
        context = self._prepare_context(retrieved_docs)
        
        # Generate answer
        prompt = f"""Based on the following context, provide a comprehensive answer to the query.
        
Query: {query}

Context:
{context}

Instructions:
- Provide a direct, factual answer based only on the provided context
- Include specific numbers, dates, and details when available
- If sources conflict, mention both perspectives
- Maintain numeric fidelity (include units)
- If confidence is low, state "Not enough evidence"

Answer:"""

        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        
        answer = response.choices[0].message.content
        citations = self._extract_citations(retrieved_docs)
        
        # Assess confidence
        confidence = self._assess_confidence(retrieved_docs, answer)
        
        return {
            "answer": answer,
            "confidence": confidence,
            "citations": citations
        }
    
    def _generate_section(self, 
                         section_name: str,
                         query: str, 
                         retrieved_docs: List[RetrievalResult],
                         style: str,
                         length: str) -> tuple:
        """Generate a specific report section"""
        
        context = self._prepare_context(retrieved_docs)
        
        # Section-specific prompts
        section_prompts = {
            "Executive Summary": f"""Write a {length} executive summary (150-200 words) that:
            - Provides high-level overview of key findings
            - Uses {style} tone
            - Focuses on business impact and implications""",
            
            "Key Findings": f"""List the key findings in bullet format:
            - Extract 5-8 most important facts
            - Include specific numbers and metrics
            - Use {style} tone""",
            
            "Risks & Mitigations": f"""Identify risks and mitigation strategies:
            - List potential risks mentioned in the context
            - Suggest practical mitigation approaches
            - Use {style} tone""",
            
            "Recommendations": f"""Provide actionable recommendations:
            - List 3-5 specific next steps
            - Base on evidence from context
            - Use {style} tone"""
        }
        
        section_prompt = section_prompts.get(section_name, 
            f"Write a {section_name} section based on the context using {style} tone.")
        
        prompt = f"""Based on the following context, {section_prompt}

Query: {query}

Context:
{context}

{section_name}:"""

        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        
        content = response.choices[0].message.content
        citations = self._extract_citations(retrieved_docs)
        
        return content, citations
    
    def _prepare_context(self, retrieved_docs: List[RetrievalResult]) -> str:
        """Prepare context from retrieved documents"""
        context_parts = []
        
        for i, doc in enumerate(retrieved_docs[:10]):  # Limit context size
            context_part = f"""[Source {i+1}]
Document: {doc.metadata.doc_id}
Page: {doc.metadata.page_start}
Section: {', '.join(doc.metadata.heading_chain)}
Content: {doc.content}
---"""
            context_parts.append(context_part)
        
        return "\n\n".join(context_parts)
    
    def _extract_citations(self, retrieved_docs: List[RetrievalResult]) -> List[Citation]:
        """Extract citations from retrieved documents"""
        citations = []
        
        for doc in retrieved_docs:
            citation = Citation(
                doc_id=doc.metadata.doc_id,
                page=doc.metadata.page_start,
                section=', '.join(doc.metadata.heading_chain),
                chunk_id=doc.metadata.chunk_id,
                content_preview=doc.content[:200] + "..." if len(doc.content) > 200 else doc.content
            )
            citations.append(citation)
        
        return citations
    
    def _assess_confidence(self, retrieved_docs: List[RetrievalResult], answer: str) -> str:
        """Assess confidence in the generated answer"""
        if not retrieved_docs:
            return "low"
        
        # Simple heuristics for confidence
        avg_score = sum(doc.score for doc in retrieved_docs) / len(retrieved_docs)
        
        if avg_score > 0.8 and len(retrieved_docs) >= 3:
            return "high"
        elif avg_score > 0.6 and len(retrieved_docs) >= 2:
            return "medium"
        else:
            return "low"