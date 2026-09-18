from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime
from researchvault.models.chat import MessageRole
from researchvault.schemas.document import ChunkResponse


class CitationResponse(BaseModel):
    id: Optional[str] = None
    citation_number: int
    document_id: str
    chunk_id: Optional[str] = None
    document_title: str
    page_number: int
    section: str
    passage_text: str
    similarity_score: float = 0.0
    rerank_score: float = 0.0

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: MessageRole
    content: str
    rewritten_query: Optional[str] = None
    expansion_queries: List[str] = []
    latency_ms: float = 0.0
    tokens_used: int = 0
    structured_data: Dict[str, Any] = {}
    citations: List[CitationResponse] = []
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    id: str
    user_id: str
    collection_id: Optional[str] = None
    title: str
    mode: str
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse] = []

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    conversation_id: Optional[str] = None
    collection_id: Optional[str] = None
    document_ids: Optional[List[str]] = None
    message: str
    mode: Optional[str] = "rag"  # rag, research, compare
    llm_provider: Optional[str] = None  # override config if provided
    top_k: Optional[int] = 10
    stream: Optional[bool] = False
