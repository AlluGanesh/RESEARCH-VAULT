from typing import Optional, List, Dict, Any
from pydantic import BaseModel
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
