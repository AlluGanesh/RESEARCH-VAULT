import re
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from researchvault.generation.llm_service import llm_service


@dataclass
class CitationItem:
    citation_number: int
    document_id: str
    chunk_id: Optional[str]
    document_title: str
    page_number: int
    section: str
    passage_text: str
    similarity_score: float
    rerank_score: float


class CitationEngine:
    SYSTEM_PROMPT = (
        "You are ResearchVault AI, a premier scientific and academic research intelligence assistant.\n"
        "Your task is to provide accurate, grounded answers to user questions using ONLY the provided numbered source passages.\n\n"
        "STRICT GROUNDING & CITATION RULES:\n"
        "1. Every factual statement, claim, or summary MUST include inline bracketed citation numbers, e.g., [1], [2], or [1, 3].\n"
        "2. ONLY cite numbered passages that are explicitly provided in the context. Never fabricate citation numbers.\n"
        "3. If the provided context does not contain enough information to answer the question, clearly state: 'Based on the retrieved documents, there is insufficient evidence to fully answer this question.'\n"
        "4. Distinguish between empirical evidence from the documents and logical inferences.\n"
        "5. Format your output with clear Markdown headings, bullet points, and technical clarity.\n"
    )

    def _extract_citations_from_text(
        self,
        answer_text: str,
        retrieved_chunks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        # Map citation_number -> chunk
        chunk_map = {c.get("citation_number"): c for c in retrieved_chunks if c.get("citation_number")}

        # Find all brackets like [1], [1, 2], [1-3]
        matches = re.findall(r'\[(\d+(?:,\s*\d+)*)\]', answer_text)
        cited_indices = set()
        for m in matches:
            for num_str in m.split(","):
                try:
                    cited_indices.add(int(num_str.strip()))
                except ValueError:
                    pass

        # Also fallback: if no inline citations were generated but chunks were retrieved, include the top referenced chunks
        if not cited_indices and retrieved_chunks:
            cited_indices = set(chunk_map.keys())

        citations = []
        for c_idx in sorted(cited_indices):
            if c_idx in chunk_map:
                chunk = chunk_map[c_idx]
                citations.append({
                    "citation_number": c_idx,
                    "document_id": chunk.get("document_id", ""),
                    "chunk_id": chunk.get("chunk_id"),
                    "document_title": chunk.get("document_title", "Document"),
                    "page_number": chunk.get("page_number", 1),
                    "section": chunk.get("section", "General"),
                    "passage_text": chunk.get("passage_text") or chunk.get("content", ""),
                    "similarity_score": float(chunk.get("score") or chunk.get("vector_score") or 0.0),
                    "rerank_score": float(chunk.get("rerank_score") or chunk.get("rrf_score") or 0.0)
                })

        return citations

    async def generate_grounded_answer(
        self,
        query: str,
        compressed_context: str,
        retrieved_chunks: List[Dict[str, Any]],
        llm_provider: Optional[str] = None
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Calls the LLM with grounded context and extracts verified citation objects.
        """
        user_prompt = (
            f"User Question: {query}\n\n"
            f"--- RETRIEVED RESEARCH CONTEXT ---\n"
            f"{compressed_context}\n"
            f"----------------------------------\n\n"
            f"Synthesize a thorough, factual response addressing the user's question, citing the numbered sources [N] for every claim."
        )

        answer_text = await llm_service.generate_text(
            prompt=user_prompt,
            system_prompt=self.SYSTEM_PROMPT,
            temperature=0.15,
            provider_override=llm_provider
        )

        citations = self._extract_citations_from_text(answer_text, retrieved_chunks)
        return answer_text, citations


# Global instance
citation_engine = CitationEngine()
