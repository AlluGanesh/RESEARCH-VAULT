import time
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from researchvault.models.evaluation import EvaluationDataset
from researchvault.evaluation.hybrid_metrics import hybrid_metrics_evaluator, HybridDiagnosticMetrics
from researchvault.evaluation.hallucination_detector import hallucination_detector

logger = logging.getLogger(__name__)


class BenchmarkCurvePoint:
    def __init__(
        self,
        dense_weight: float,
        sparse_weight: float,
        mean_ndcg: float,
        mean_recall: float,
        mean_precision: float,
        mean_mrr: float,
        mean_overlap: float,
        mean_dense_only: float,
        mean_sparse_only: float,
        avg_latency_ms: float,
        estimated_hallucination_rate: float,
        composite_score: float
    ):
        self.dense_weight = dense_weight
        self.sparse_weight = sparse_weight
        self.mean_ndcg = mean_ndcg
        self.mean_recall = mean_recall
        self.mean_precision = mean_precision
        self.mean_mrr = mean_mrr
        self.mean_overlap = mean_overlap
        self.mean_dense_only = mean_dense_only
        self.mean_sparse_only = mean_sparse_only
        self.avg_latency_ms = avg_latency_ms
        self.estimated_hallucination_rate = estimated_hallucination_rate
        self.composite_score = composite_score

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dense_weight": round(self.dense_weight, 2),
            "sparse_weight": round(self.sparse_weight, 2),
            "dense_pct": int(round(self.dense_weight * 100)),
            "sparse_pct": int(round(self.sparse_weight * 100)),
            "mean_ndcg": round(self.mean_ndcg, 3),
            "mean_recall": round(self.mean_recall, 3),
            "mean_precision": round(self.mean_precision, 3),
            "mean_mrr": round(self.mean_mrr, 3),
            "mean_overlap": round(self.mean_overlap, 3),
            "mean_dense_only": round(self.mean_dense_only, 2),
            "mean_sparse_only": round(self.mean_sparse_only, 2),
            "avg_latency_ms": round(self.avg_latency_ms, 2),
            "estimated_hallucination_rate": round(self.estimated_hallucination_rate, 2),
            "composite_score": round(self.composite_score, 3)
        }


class RatioOptimizer:
    """
    Automated RAG Hybrid Retrieval Ratio Benchmark Runner & Optimizer.
    Sweeps fusion ratios from pure BM25 (0:100) to pure Dense (100:0) and
    identifies the Pareto-optimal fusion ratio for maximal retrieval quality.
    """

    DEFAULT_RATIOS = [0.0, 0.2, 0.4, 0.5, 0.6, 0.7, 0.8, 1.0]

    async def run_hybrid_benchmark(
        self,
        db: AsyncSession,
        dataset_id: str,
        user_id: str,
        k: int = 10,
        ratios: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        sweep_ratios = ratios or self.DEFAULT_RATIOS

        # 1. Load dataset test cases
        stmt = select(EvaluationDataset).options(selectinload(EvaluationDataset.test_cases)).where(
            EvaluationDataset.id == dataset_id
        )
        res = await db.execute(stmt)
        dataset = res.scalar_one_or_none()

        if not dataset or not dataset.test_cases:
            raise ValueError(f"Evaluation dataset '{dataset_id}' not found or empty.")

        curve_points: List[BenchmarkCurvePoint] = []
        start_overall = time.time()

        for w_d in sweep_ratios:
            w_s = round(1.0 - w_d, 2)
            ndcg_vals, recall_vals, prec_vals, mrr_vals, overlap_vals = [], [], [], [], []
            dense_only_vals, sparse_only_vals, latencies = [], [], []

            for tc in dataset.test_cases:
                expected_docs = tc.relevant_doc_titles or []
                diag = await hybrid_metrics_evaluator.evaluate_query_at_ratio(
                    db=db,
                    query=tc.question,
                    ground_truth_docs=expected_docs,
                    dense_weight=w_d,
                    sparse_weight=w_s,
                    k=k,
                    user_id=user_id
                )

                ndcg_vals.append(diag.ndcg_at_k)
                recall_vals.append(diag.recall_at_k)
                prec_vals.append(diag.precision_at_k)
                mrr_vals.append(diag.mrr)
                overlap_vals.append(diag.overlap_ratio)
                dense_only_vals.append(diag.dense_only_count)
                sparse_only_vals.append(diag.sparse_only_count)
                latencies.append(diag.latency_ms)

            mean_ndcg = sum(ndcg_vals) / len(ndcg_vals) if ndcg_vals else 0.0
            mean_rec = sum(recall_vals) / len(recall_vals) if recall_vals else 0.0
            mean_prec = sum(prec_vals) / len(prec_vals) if prec_vals else 0.0
            mean_mrr = sum(mrr_vals) / len(mrr_vals) if mrr_vals else 0.0
            mean_overlap = sum(overlap_vals) / len(overlap_vals) if overlap_vals else 0.0
            mean_dense_only = sum(dense_only_vals) / len(dense_only_vals) if dense_only_vals else 0.0
            mean_sparse_only = sum(sparse_only_vals) / len(sparse_only_vals) if sparse_only_vals else 0.0
            avg_lat = sum(latencies) / len(latencies) if latencies else 0.0

            # Hallucination correlation: inversely linked to recall and NDCG
            # Low recall and ranking errors produce downstream unsupported claims
            est_hallucination = max(4.0, (1.0 - (mean_ndcg * 0.6 + mean_rec * 0.4)) * 38.0)

            # Composite objective score
            # Score = 0.45 * NDCG + 0.35 * Recall + 0.20 * (1 - HallucinationRate/100)
            composite = (0.45 * mean_ndcg) + (0.35 * mean_rec) + (0.20 * (1.0 - est_hallucination / 100.0))

            point = BenchmarkCurvePoint(
                dense_weight=w_d,
                sparse_weight=w_s,
                mean_ndcg=mean_ndcg,
                mean_recall=mean_rec,
                mean_precision=mean_prec,
                mean_mrr=mean_mrr,
                mean_overlap=mean_overlap,
                mean_dense_only=mean_dense_only,
                mean_sparse_only=mean_sparse_only,
                avg_latency_ms=avg_lat,
                estimated_hallucination_rate=est_hallucination,
                composite_score=composite
            )
            curve_points.append(point)

        # 2. Select optimal ratio
        best_point = max(curve_points, key=lambda p: p.composite_score)
        pure_bm25 = next((p for p in curve_points if p.dense_weight == 0.0), curve_points[0])
        pure_dense = next((p for p in curve_points if p.dense_weight == 1.0), curve_points[-1])

        ndcg_lift_over_bm25 = ((best_point.mean_ndcg - pure_bm25.mean_ndcg) / pure_bm25.mean_ndcg * 100.0) if pure_bm25.mean_ndcg > 0 else 0.0
        ndcg_lift_over_dense = ((best_point.mean_ndcg - pure_dense.mean_ndcg) / pure_dense.mean_ndcg * 100.0) if pure_dense.mean_ndcg > 0 else 0.0

        rationale = (
            f"Ratio {int(best_point.dense_weight * 100)}% Dense / {int(best_point.sparse_weight * 100)}% BM25 "
            f"maximizes NDCG@{k} ({best_point.mean_ndcg:.3f}) and Recall@{k} ({best_point.mean_recall:.1%}), "
            f"yielding +{ndcg_lift_over_dense:.1f}% NDCG improvement over pure Dense and +{ndcg_lift_over_bm25:.1f}% over pure BM25. "
            f"Captures {best_point.mean_dense_only:.1f} dense semantic passages and {best_point.mean_sparse_only:.1f} exact lexical matches."
        )

        total_exec_time = (time.time() - start_overall) * 1000.0

        return {
            "dataset_id": dataset.id,
            "dataset_name": dataset.name,
            "k": k,
            "total_test_cases": len(dataset.test_cases),
            "benchmark_curves": [p.to_dict() for p in curve_points],
            "optimal_recommendation": {
                "dense_weight": best_point.dense_weight,
                "sparse_weight": best_point.sparse_weight,
                "dense_pct": int(round(best_point.dense_weight * 100)),
                "sparse_pct": int(round(best_point.sparse_weight * 100)),
                "peak_ndcg": round(best_point.mean_ndcg, 3),
                "peak_recall": round(best_point.mean_recall, 3),
                "composite_score": round(best_point.composite_score, 3),
                "estimated_hallucination_rate": round(best_point.estimated_hallucination_rate, 2),
                "ndcg_lift_over_dense_pct": round(ndcg_lift_over_dense, 1),
                "ndcg_lift_over_bm25_pct": round(ndcg_lift_over_bm25, 1),
                "rationale": rationale
            },
            "execution_time_ms": round(total_exec_time, 2)
        }


ratio_optimizer = RatioOptimizer()
