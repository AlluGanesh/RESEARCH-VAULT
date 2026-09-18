import re
import math
from typing import List, Dict, Any, Optional
from collections import Counter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from researchvault.models.chunk import Chunk
from researchvault.models.document import Document


class BM25LexicalRetriever:
    """
    BM25 Lexical Keyword Retriever across document chunks in the database.
    Computes BM25 Okapi relevance score with k1=1.5, b=0.75.
    """
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b

    def _tokenize(self, text: str) -> List[str]:
        # Lowercase, clean alphanumeric tokens
        tokens = re.findall(r'\b[a-zA-Z0-9_\-]{2,}\b', text.lower())
        stopwords = {
            "the", "and", "is", "in", "to", "of", "a", "an", "that", "this", "for", "with",
            "as", "on", "by", "at", "from", "it", "are", "be", "was", "were", "or", "which"
        }
        return [t for t in tokens if t not in stopwords]

    async def search(
        self,
        db: AsyncSession,
        query: str,
        top_k: int = 20,
        user_id: Optional[str] = None,
        collection_id: Optional[str] = None,
        document_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        # Build DB query joining Chunk and Document
        stmt = select(Chunk, Document).join(Document, Chunk.document_id == Document.id)
        
        if user_id:
            stmt = stmt.where(Document.user_id == user_id)
        if collection_id:
            stmt = stmt.where(Document.collection_id == collection_id)
        if document_ids and len(document_ids) > 0:
            stmt = stmt.where(Document.id.in_(document_ids))

        result = await db.execute(stmt)
        rows = result.all()
        
        if not rows:
            return []

        # Corpus statistics for BM25
        doc_count = len(rows)
        chunk_token_lists = []
        doc_freqs = Counter()
        total_length = 0

        for chunk, doc in rows:
            # Combine content and context_header for matching
            full_text = f"{chunk.context_header or ''} {chunk.content}"
            tokens = self._tokenize(full_text)
            chunk_token_lists.append((chunk, doc, tokens))
            total_length += len(tokens)
            unique_tokens = set(tokens)
            for ut in unique_tokens:
                doc_freqs[ut] += 1

        avg_doc_len = (total_length / doc_count) if doc_count > 0 else 1.0

        # Score each chunk
        scored_chunks = []
        for chunk, doc, tokens in chunk_token_lists:
            doc_len = len(tokens)
            term_counts = Counter(tokens)
            score = 0.0

            for q_term in query_tokens:
                if q_term in term_counts:
                    tf = term_counts[q_term]
                    df = doc_freqs.get(q_term, 0)
                    # IDF formula with smoothing
                    idf = math.log((doc_count - df + 0.5) / (df + 0.5) + 1.0)
                    # BM25 TF formula
                    numerator = tf * (self.k1 + 1)
                    denominator = tf + self.k1 * (1 - self.b + self.b * (doc_len / avg_doc_len))
                    score += idf * (numerator / denominator)

            if score > 0:
                scored_chunks.append({
                    "chunk_id": chunk.id,
                    "document_id": doc.id,
                    "document_title": doc.title,
                    "author": doc.author or "Unknown",
                    "collection_id": doc.collection_id,
                    "page_number": chunk.page_number,
                    "section": chunk.section,
                    "subsection": chunk.subsection,
                    "chunk_index": chunk.chunk_index,
                    "content": chunk.content,
                    "context_header": chunk.context_header,
                    "token_count": chunk.token_count,
                    "lexical_score": float(score)
                })

        # Sort descending by score
        scored_chunks.sort(key=lambda x: x["lexical_score"], reverse=True)
        return scored_chunks[:top_k]
