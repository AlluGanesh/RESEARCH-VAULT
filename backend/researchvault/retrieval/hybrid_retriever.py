import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from researchvault.core.config import settings
from researchvault.embeddings.embedding_service import embedding_service
from researchvault.retrieval.vector_store import vector_store
from researchvault.retrieval.lexical_search import BM25LexicalRetriever

logger = logging.getLogger(__name__)


class HybridRetriever:
    def __init__(
        self,
        rrf_k: int = None,
        vector_weight: float = 1.0,
        lexical_weight: float = 0.8
    ):
        self.rrf_k = rrf_k or settings.RRF_K_CONSTANT
        self.vector_weight = vector_weight
        self.lexical_weight = lexical_weight
        self.lexical_retriever = BM25LexicalRetriever()

    async def retrieve(
        self,
        db: AsyncSession,
        queries: List[str],  # Can be multi-query expansion list
        top_k: int = 25,
        user_id: Optional[str] = None,
        collection_id: Optional[str] = None,
        document_ids: Optional[List[str]] = None,
        author: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Executes hybrid retrieval:
        1. Dense Vector search across Qdrant with all queries in expansion list.
        2. Sparse BM25 search across database chunks.
        3. Reciprocal Rank Fusion (RRF) deduplication & unified ranking.
        """
        if not queries:
            return []

        primary_query = queries[0]
        
        # 1. Vector Search (multi-query)
        vector_results_by_chunk: Dict[str, Dict[str, Any]] = {}
        for q in queries:
            try:
                q_vec = embedding_service.generate_embedding(q)
                v_res = vector_store.search(
                    query_vector=q_vec,
                    top_k=top_k,
                    user_id=user_id,
                    collection_id=collection_id,
                    document_ids=document_ids,
                    author=author
                )
                for item in v_res:
                    cid = item.get("chunk_id") or item.get("point_id")
                    if not cid:
                        continue
                    if cid not in vector_results_by_chunk or item["score"] > vector_results_by_chunk[cid]["score"]:
                        vector_results_by_chunk[cid] = item
            except Exception as e:
                logger.error(f"Vector search failed for query '{q}': {e}")

        # Sorted vector candidates
        sorted_vector_candidates = sorted(
            vector_results_by_chunk.values(),
            key=lambda x: x["score"],
            reverse=True
        )

        # 2. Lexical Search
        lexical_candidates = []
        try:
            lexical_candidates = await self.lexical_retriever.search(
                db=db,
                query=" ".join(queries),
                top_k=top_k,
                user_id=user_id,
                collection_id=collection_id,
                document_ids=document_ids
            )
        except Exception as e:
            logger.error(f"Lexical search failed: {e}")

        # 3. Reciprocal Rank Fusion (RRF)
        # RRF_Score(d) = sum( w / (k + rank) )
        fused_scores: Dict[str, float] = {}
        fused_items: Dict[str, Dict[str, Any]] = {}

        # Process vector ranks
        for rank_idx, item in enumerate(sorted_vector_candidates):
            cid = item.get("chunk_id") or item.get("point_id")
            if not cid:
                continue
            rank = rank_idx + 1
            score_contrib = self.vector_weight / (self.rrf_k + rank)
            fused_scores[cid] = fused_scores.get(cid, 0.0) + score_contrib
            if cid not in fused_items:
                fused_items[cid] = dict(item)
            fused_items[cid]["vector_rank"] = rank
            fused_items[cid]["vector_score"] = item.get("score", 0.0)

        # Process lexical ranks
        for rank_idx, item in enumerate(lexical_candidates):
            cid = item.get("chunk_id")
            if not cid:
                continue
            rank = rank_idx + 1
            score_contrib = self.lexical_weight / (self.rrf_k + rank)
            fused_scores[cid] = fused_scores.get(cid, 0.0) + score_contrib
            if cid not in fused_items:
                fused_items[cid] = dict(item)
            fused_items[cid]["lexical_rank"] = rank
            fused_items[cid]["lexical_score"] = item.get("lexical_score", 0.0)

        # Build output list with RRF score
        fused_results = []
        for cid, total_rrf in fused_scores.items():
            candidate = fused_items[cid]
            candidate["rrf_score"] = float(total_rrf)
            # Ensure chunk_id is present
            candidate["chunk_id"] = cid
            fused_results.append(candidate)

        # Sort descending by RRF score
        fused_results.sort(key=lambda x: x["rrf_score"], reverse=True)
        return fused_results[:top_k]
