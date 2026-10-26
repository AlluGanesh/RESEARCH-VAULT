import math
import time
from typing import List, Dict, Any, Optional, Set
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from researchvault.retrieval.hybrid_retriever import HybridRetriever
from researchvault.evaluation.metrics import RAGEvaluator

logger = logging.getLogger(__name__)


class HybridDiagnosticMetrics:
    def __init__(
        self,
        dense_weight: float,
        sparse_weight: float,
        k: int,
        precision_at_k: float,
        recall_at_k: float,
        mrr: float,
        ndcg_at_k: float,
        total_retrieved: int,
        overlap_count: int,
        overlap_ratio: float,
        dense_only_count: int,
        dense_only_relevant: int,
        sparse_only_count: int,
        sparse_only_relevant: int,
        latency_ms: float,
        retrieved_candidates: List[Dict[str, Any]]
    ):
        self.dense_weight = dense_weight
        self.sparse_weight = sparse_weight
        self.k = k
        self.precision_at_k = precision_at_k
        self.recall_at_k = recall_at_k
        self.mrr = mrr
        self.ndcg_at_k = ndcg_at_k
        self.total_retrieved = total_retrieved
        self.overlap_count = overlap_count
        self.overlap_ratio = overlap_ratio
        self.dense_only_count = dense_only_count
        self.dense_only_relevant = dense_only_relevant
        self.sparse_only_count = sparse_only_count
        self.sparse_only_relevant = sparse_only_relevant
        self.latency_ms = latency_ms
        self.retrieved_candidates = retrieved_candidates

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dense_weight": round(self.dense_weight, 2),
            "sparse_weight": round(self.sparse_weight, 2),
            "k": self.k,
            "precision_at_k": round(self.precision_at_k, 3),
            "recall_at_k": round(self.recall_at_k, 3),
            "mrr": round(self.mrr, 3),
            "ndcg_at_k": round(self.ndcg_at_k, 3),
            "total_retrieved": self.total_retrieved,
            "overlap_count": self.overlap_count,
            "overlap_ratio": round(self.overlap_ratio, 3),
            "dense_only_count": self.dense_only_count,
            "dense_only_relevant": self.dense_only_relevant,
            "sparse_only_count": self.sparse_only_count,
            "sparse_only_relevant": self.sparse_only_relevant,
            "latency_ms": round(self.latency_ms, 2),
            "candidates_sample": [
                {
                    "chunk_id": c.get("chunk_id"),
                    "document_title": c.get("document_title"),
                    "retrieval_source": c.get("retrieval_source"),
                    "rrf_score": round(c.get("rrf_score", 0.0), 5),
                    "vector_score": round(c.get("vector_score", 0.0), 3) if c.get("vector_score") else None,
                    "lexical_score": round(c.get("lexical_score", 0.0), 3) if c.get("lexical_score") else None,
                    "passage_preview": (c.get("passage_text") or c.get("content", ""))[:120] + "..."
                }
                for c in self.retrieved_candidates[:self.k]
            ]
        }


class HybridMetricsEvaluator:
    """
    Evaluates retrieval performance and diagnostic interactions between
    Dense Semantic Search and Sparse BM25 Lexical Matching.
    """

    def __init__(self):
        self.retriever = HybridRetriever()

    async def evaluate_query_at_ratio(
        self,
        db: AsyncSession,
        query: str,
        ground_truth_docs: List[str],
        dense_weight: float = 0.6,
        sparse_weight: float = 0.4,
        k: int = 10,
        user_id: Optional[str] = None,
        collection_id: Optional[str] = None
    ) -> HybridDiagnosticMetrics:
        start_t = time.time()

        candidates = await self.retriever.retrieve(
            db=db,
            queries=[query],
            top_k=k,
            user_id=user_id,
            collection_id=collection_id,
            dense_weight=dense_weight,
            sparse_weight=sparse_weight
        )

        latency = (time.time() - start_t) * 1000.0
        retrieved_titles = [c.get("document_title", "") for c in candidates]

        # Standard Information Retrieval metrics
        p_at_k = RAGEvaluator.precision_at_k(retrieved_titles, ground_truth_docs, k=k)
        r_at_k = RAGEvaluator.recall_at_k(retrieved_titles, ground_truth_docs, k=k)
        mrr = RAGEvaluator.reciprocal_rank(retrieved_titles, ground_truth_docs)
        ndcg = RAGEvaluator.ndcg_at_k(retrieved_titles, ground_truth_docs, k=k)

        # Dissect contributions
        overlap_count = sum(1 for c in candidates if c.get("retrieval_source") == "hybrid_overlap")
        dense_only = [c for c in candidates if c.get("retrieval_source") == "dense_only"]
        sparse_only = [c for c in candidates if c.get("retrieval_source") == "sparse_only"]

        gt_lower = set(d.lower().strip() for d in ground_truth_docs)

        dense_only_relevant = sum(
            1 for c in dense_only
            if any(rel in (c.get("document_title") or "").lower() for rel in gt_lower)
        )
        sparse_only_relevant = sum(
            1 for c in sparse_only
            if any(rel in (c.get("document_title") or "").lower() for rel in gt_lower)
        )

        total_k = len(candidates)
        overlap_ratio = (overlap_count / total_k) if total_k > 0 else 0.0

        return HybridDiagnosticMetrics(
            dense_weight=dense_weight,
            sparse_weight=sparse_weight,
            k=k,
            precision_at_k=p_at_k,
            recall_at_k=r_at_k,
            mrr=mrr,
            ndcg_at_k=ndcg,
            total_retrieved=total_k,
            overlap_count=overlap_count,
            overlap_ratio=overlap_ratio,
            dense_only_count=len(dense_only),
            dense_only_relevant=dense_only_relevant,
            sparse_only_count=len(sparse_only),
            sparse_only_relevant=sparse_only_relevant,
            latency_ms=latency,
            retrieved_candidates=candidates
        )


hybrid_metrics_evaluator = HybridMetricsEvaluator()
