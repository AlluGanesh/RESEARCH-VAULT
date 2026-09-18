import logging
from typing import List, Dict, Any, Optional
from researchvault.core.config import settings

logger = logging.getLogger(__name__)


class RerankerService:
    def __init__(
        self,
        reranker_type: Optional[str] = None,
        model_name: Optional[str] = None
    ):
        self.reranker_type = reranker_type or settings.RERANKER_TYPE
        self.model_name = model_name or settings.RERANKER_MODEL
        self._cross_encoder = None

    def _load_cross_encoder(self):
        if self._cross_encoder is None and self.reranker_type == "cross-encoder":
            try:
                from sentence_transformers import CrossEncoder
                self._cross_encoder = CrossEncoder(self.model_name)
                logger.info(f"Loaded CrossEncoder model: {self.model_name}")
            except Exception as e:
                logger.warning(f"CrossEncoder unavailable: {e}. Using heuristic scoring.")

    def _heuristic_rerank(self, query: str, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Fast token overlap & exact phrase matching heuristic fallback.
        """
        q_words = set(query.lower().split())
        scored = []
        for c in candidates:
            text = (c.get("content", "") + " " + c.get("context_header", "")).lower()
            overlap = sum(1 for w in q_words if w in text)
            exact_match_bonus = 2.0 if query.lower() in text else 0.0
            rrf_base = c.get("rrf_score", 0.0) * 10.0
            score = (overlap / (len(q_words) + 1e-5)) * 3.0 + exact_match_bonus + rrf_base
            item = dict(c)
            item["rerank_score"] = float(score)
            scored.append(item)
        
        scored.sort(key=lambda x: x["rerank_score"], reverse=True)
        return scored

    def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: int = 7
    ) -> List[Dict[str, Any]]:
        if not candidates:
            return []

        if len(candidates) <= top_k and self.reranker_type == "heuristic":
            return candidates

        self._load_cross_encoder()

        if self._cross_encoder is not None:
            try:
                # Prepare query-document pairs
                pairs = [[query, f"{c.get('context_header', '')}\n{c.get('content', '')}"] for c in candidates]
                scores = self._cross_encoder.predict(pairs)

                scored_candidates = []
                for candidate, score in zip(candidates, scores):
                    item = dict(candidate)
                    item["rerank_score"] = float(score)
                    scored_candidates.append(item)

                # Sort descending
                scored_candidates.sort(key=lambda x: x["rerank_score"], reverse=True)
                return scored_candidates[:top_k]
            except Exception as e:
                logger.warning(f"CrossEncoder prediction error: {e}. Falling back to heuristic reranking.")

        # Heuristic fallback
        reranked = self._heuristic_rerank(query, candidates)
        return reranked[:top_k]


# Default global instance
reranker_service = RerankerService()
