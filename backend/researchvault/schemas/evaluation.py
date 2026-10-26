from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class TestCaseCreate(BaseModel):
    question: str
    ground_truth_answer: str
    relevant_doc_titles: List[str] = []
    relevant_passages: List[str] = []


class TestCaseResponse(TestCaseCreate):
    id: str
    dataset_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class DatasetCreate(BaseModel):
    name: str
    description: Optional[str] = None
    test_cases: List[TestCaseCreate] = []


class DatasetResponse(BaseModel):
    id: str
    user_id: str
    name: str
    description: Optional[str] = None
    test_case_count: int = 0
    created_at: datetime
    test_cases: List[TestCaseResponse] = []

    class Config:
        from_attributes = True


class RunEvaluationRequest(BaseModel):
    dataset_id: str
    run_name: Optional[str] = None
    llm_provider: Optional[str] = None
    top_k: Optional[int] = 5


class EvaluationResultResponse(BaseModel):
    id: str
    test_case_id: Optional[str] = None
    question: str
    ground_truth: str
    generated_answer: str
    precision_at_k: float
    recall_at_k: float
    reciprocal_rank: float
    ndcg_score: float
    faithfulness_score: float
    answer_relevance_score: float
    context_relevance_score: float
    citation_accuracy: float
    latency_ms: float

    class Config:
        from_attributes = True


class EvaluationRunResponse(BaseModel):
    id: str
    dataset_id: str
    run_name: str
    llm_provider: str
    embedding_provider: str
    reranker_used: str
    mean_precision_at_k: float
    mean_recall_at_k: float
    mean_mrr: float
    mean_ndcg: float
    mean_faithfulness: float
    mean_answer_relevance: float
    mean_context_relevance: float
    mean_citation_accuracy: float
    total_test_cases: int
    status: str
    created_at: datetime
    results: List[EvaluationResultResponse] = []

    class Config:
        from_attributes = True


# ============================================================================
# Hallucination Detection Schemas
# ============================================================================

class HallucinationDetectionRequest(BaseModel):
    answer_text: str = Field(..., description="The AI generated answer to verify at claim level")
    context_passages: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Retrieved evidence chunks. If empty and query provided, retriever retrieves active docs."
    )
    query: Optional[str] = Field(default=None, description="Original query if retrieving fresh evidence")
    llm_provider: Optional[str] = Field(default=None, description="LLM provider override for judge")


class ClaimVerificationItem(BaseModel):
    claim_id: str
    claim_text: str
    original_sentence: str
    cited_indices: List[int] = []
    verdict: str  # SUPPORTED, CONTRADICTED, UNVERIFIABLE
    confidence: float
    evidence_snippet: Optional[str] = None
    matched_doc_title: Optional[str] = None
    matched_chunk_id: Optional[str] = None
    citation_valid: bool = False
    explanation: Optional[str] = None


class HallucinationReportResponse(BaseModel):
    total_claims: int
    supported_count: int
    contradicted_count: int
    unverifiable_count: int
    hallucination_rate: float
    claim_support_rate: float
    contradiction_rate: float
    unverifiable_rate: float
    citation_valid_count: int
    total_citations_checked: int
    citation_accuracy: float
    verified_claims: List[ClaimVerificationItem] = []
    execution_time_ms: float


class HumanBenchmarkCaseItem(BaseModel):
    id: str
    claim: str
    gold_verdict: str
    predicted_verdict: str
    confidence: float
    is_match: bool


class HumanBenchmarkReportResponse(BaseModel):
    total_benchmark_cases: int
    correct_matches: int
    benchmark_accuracy: float
    test_cases: List[HumanBenchmarkCaseItem] = []


# ============================================================================
# Hybrid Retrieval Benchmark & Optimizer Schemas
# ============================================================================

class HybridSimulateRequest(BaseModel):
    query: str
    dense_weight: float = Field(default=0.6, ge=0.0, le=1.0)
    sparse_weight: float = Field(default=0.4, ge=0.0, le=1.0)
    k: int = Field(default=10, ge=1, le=50)


class HybridCandidateItem(BaseModel):
    chunk_id: Optional[str] = None
    document_title: Optional[str] = None
    retrieval_source: str  # dense_only, sparse_only, hybrid_overlap
    rrf_score: float
    vector_score: Optional[float] = None
    lexical_score: Optional[float] = None
    passage_preview: str


class HybridSimulateResponse(BaseModel):
    query: str
    dense_weight: float
    sparse_weight: float
    k: int
    total_retrieved: int
    overlap_count: int
    overlap_ratio: float
    dense_only_count: int
    sparse_only_count: int
    latency_ms: float
    candidates: List[HybridCandidateItem] = []


class HybridBenchmarkRequest(BaseModel):
    dataset_id: str
    k: Optional[int] = 10
    ratios: Optional[List[float]] = None  # e.g. [0.0, 0.2, 0.4, 0.5, 0.6, 0.8, 1.0]


class BenchmarkCurvePointResponse(BaseModel):
    dense_weight: float
    sparse_weight: float
    dense_pct: int
    sparse_pct: int
    mean_ndcg: float
    mean_recall: float
    mean_precision: float
    mean_mrr: float
    mean_overlap: float
    mean_dense_only: float
    mean_sparse_only: float
    avg_latency_ms: float
    estimated_hallucination_rate: float
    composite_score: float


class OptimalRecommendationResponse(BaseModel):
    dense_weight: float
    sparse_weight: float
    dense_pct: int
    sparse_pct: int
    peak_ndcg: float
    peak_recall: float
    composite_score: float
    estimated_hallucination_rate: float
    ndcg_lift_over_dense_pct: float
    ndcg_lift_over_bm25_pct: float
    rationale: str


class HybridBenchmarkResponse(BaseModel):
    dataset_id: str
    dataset_name: str
    k: int
    total_test_cases: int
    benchmark_curves: List[BenchmarkCurvePointResponse] = []
    optimal_recommendation: OptimalRecommendationResponse
    execution_time_ms: float


class OptimizeRatioRequest(BaseModel):
    dataset_id: str
    k: Optional[int] = 10
