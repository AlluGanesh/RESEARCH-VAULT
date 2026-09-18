from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from researchvault.schemas.chat import CitationResponse


class ComparisonRow(BaseModel):
    document_id: str
    document_title: str
    methodology: str
    architecture_or_approach: str
    datasets_used: str
    key_results: str
    limitations: str
    citation_numbers: List[int] = []


class CompareRequest(BaseModel):
    document_ids: List[str]
    question: Optional[str] = "Compare the methodologies, datasets, key results, and limitations of these documents."


class CompareResponse(BaseModel):
    question: str
    documents_compared_count: int
    summary_analysis: str
    matrix_rows: List[ComparisonRow] = []
    markdown_table: str
    citations: List[CitationResponse] = []
    latency_ms: float = 0.0
