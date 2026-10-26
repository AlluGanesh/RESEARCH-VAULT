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
        author: Optional[str] = None,
        dense_weight: Optional[float] = None,
        sparse_weight: Optional[float] = None,
        rrf_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Executes hybrid retrieval:
        1. Dense Vector search across Qdrant with all queries in expansion list.
        2. Sparse BM25 search across database chunks.
        3. Reciprocal Rank Fusion (RRF) with normalized weights:
           S(d) = w_d / (k + r_d(d)) + w_s / (k + r_s(d))
           where w_d + w_s = 1.0.
        """
        if not queries:
            return []

        # Calculate normalized weights
        w_d = dense_weight if dense_weight is not None else self.vector_weight
        w_s = sparse_weight if sparse_weight is not None else self.lexical_weight
        total_w = w_d + w_s
        if total_w > 0:
            norm_dense_w = w_d / total_w
            norm_sparse_w = w_s / total_w
        else:
            norm_dense_w = 0.5
            norm_sparse_w = 0.5

        k_const = rrf_k or self.rrf_k
        
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

        # 3. Weighted Reciprocal Rank Fusion (RRF)
        # S(d) = w_d / (k + r_d(d)) + w_s / (k + r_s(d))
        fused_scores: Dict[str, float] = {}
        fused_items: Dict[str, Dict[str, Any]] = {}

        # Process vector ranks (dense)
        for rank_idx, item in enumerate(sorted_vector_candidates):
            cid = item.get("chunk_id") or item.get("point_id")
            if not cid:
                continue
            rank = rank_idx + 1
            score_contrib = norm_dense_w / (k_const + rank)
            fused_scores[cid] = fused_scores.get(cid, 0.0) + score_contrib
            if cid not in fused_items:
                fused_items[cid] = dict(item)
            fused_items[cid]["vector_rank"] = rank
            fused_items[cid]["vector_score"] = item.get("score", 0.0)
            fused_items[cid]["has_dense"] = True

        # Process lexical ranks (sparse)
        for rank_idx, item in enumerate(lexical_candidates):
            cid = item.get("chunk_id")
            if not cid:
                continue
            rank = rank_idx + 1
            score_contrib = norm_sparse_w / (k_const + rank)
            fused_scores[cid] = fused_scores.get(cid, 0.0) + score_contrib
            if cid not in fused_items:
                fused_items[cid] = dict(item)
            fused_items[cid]["lexical_rank"] = rank
            fused_items[cid]["lexical_score"] = item.get("lexical_score", 0.0)
            fused_items[cid]["has_sparse"] = True

        # Build output list with weighted RRF score and diagnostic tags
        fused_results = []
        for cid, total_rrf in fused_scores.items():
            candidate = fused_items[cid]
            candidate["rrf_score"] = float(total_rrf)
            candidate["chunk_id"] = cid

            has_d = candidate.get("has_dense", False)
            has_s = candidate.get("has_sparse", False)
            if has_d and has_s:
                candidate["retrieval_source"] = "hybrid_overlap"
            elif has_d:
                candidate["retrieval_source"] = "dense_only"
            else:
                candidate["retrieval_source"] = "sparse_only"

            fused_results.append(candidate)

        # Sort descending by RRF score
        fused_results.sort(key=lambda x: x["rrf_score"], reverse=True)
        return fused_results[:top_k]

