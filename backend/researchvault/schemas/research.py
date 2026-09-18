from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from researchvault.schemas.chat import CitationResponse


class ResearchPlanStep(BaseModel):
    step_number: int
    sub_question: str
    rationale: str
    retrieved_chunks_count: int = 0
    status: str = "COMPLETED"  # PENDING, IN_PROGRESS, COMPLETED


class ContradictionItem(BaseModel):
    topic: str
    perspective_a: str
    perspective_a_source: str
    perspective_b: str
    perspective_b_source: str
    analysis: str


class ResearchRequest(BaseModel):
    query: str
    collection_id: Optional[str] = None
    document_ids: Optional[List[str]] = None
    depth: Optional[str] = "comprehensive"  # quick, standard, comprehensive


class ResearchResponse(BaseModel):
    query: str
    plan_steps: List[ResearchPlanStep] = []
    executive_summary: str
    key_findings: List[str] = []
    cross_document_synthesis: str
    contradictions: List[ContradictionItem] = []
    research_gaps: List[str] = []
    markdown_report: str
    citations: List[CitationResponse] = []
    latency_ms: float = 0.0
    total_tokens: int = 0
