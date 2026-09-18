from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime


class QueryTraceResponse(BaseModel):
    id: str
    user_id: str
    conversation_id: Optional[str] = None
    raw_query: str
    rewritten_query: Optional[str] = None
    expansion_queries: List[str] = []
    extracted_keywords: List[str] = []
    applied_filters: Dict[str, Any] = {}
    
    vector_candidates_count: int = 0
    lexical_candidates_count: int = 0
    rrf_candidates: List[Dict[str, Any]] = []
    reranked_candidates: List[Dict[str, Any]] = []
    compressed_context: Optional[str] = None
    
    llm_prompt: Optional[str] = None
    llm_response: Optional[str] = None
    citations_count: int = 0
    
    query_transform_ms: float = 0.0
    retrieval_ms: float = 0.0
    rerank_ms: float = 0.0
    compression_ms: float = 0.0
    generation_ms: float = 0.0
    total_latency_ms: float = 0.0
    
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    status: str = "SUCCESS"
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ObservabilityStatsResponse(BaseModel):
    total_documents: int
    total_chunks: int
    total_embeddings: int
    total_queries: int
    avg_retrieval_latency_ms: float
    avg_generation_latency_ms: float
    avg_total_latency_ms: float
    total_tokens_consumed: int
    failed_queries_count: int
    latest_traces: List[QueryTraceResponse] = []
