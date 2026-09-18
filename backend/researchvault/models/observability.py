from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from researchvault.database.session import Base


class QueryTrace(Base):
    __tablename__ = "query_traces"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    conversation_id = Column(String(36), nullable=True, index=True)
    
    # Query lifecycle
    raw_query = Column(Text, nullable=False)
    rewritten_query = Column(Text, nullable=True)
    expansion_queries = Column(JSON, default=list)
    extracted_keywords = Column(JSON, default=list)
    applied_filters = Column(JSON, default=dict)
    
    # Stages detail
    vector_candidates_count = Column(Integer, default=0)
    lexical_candidates_count = Column(Integer, default=0)
    rrf_candidates = Column(JSON, default=list)  # Top RRF chunks with scores
    reranked_candidates = Column(JSON, default=list)  # Top reranked chunks with scores
    compressed_context = Column(Text, nullable=True)
    
    # LLM Interaction
    llm_prompt = Column(Text, nullable=True)
    llm_response = Column(Text, nullable=True)
    citations_count = Column(Integer, default=0)
    
    # Performance & Observability
    query_transform_ms = Column(Float, default=0.0)
    retrieval_ms = Column(Float, default=0.0)
    rerank_ms = Column(Float, default=0.0)
    compression_ms = Column(Float, default=0.0)
    generation_ms = Column(Float, default=0.0)
    total_latency_ms = Column(Float, default=0.0)
    
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    
    status = Column(String(50), default="SUCCESS")  # SUCCESS, FAILED
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    # Relationships
    user = relationship("User", back_populates="query_traces")
