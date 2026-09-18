from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from researchvault.database.session import Base


class EvaluationDataset(Base):
    __tablename__ = "evaluation_datasets"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    test_cases = relationship("EvaluationTestCase", back_populates="dataset", cascade="all, delete-orphan")
    runs = relationship("EvaluationRun", back_populates="dataset", cascade="all, delete-orphan")


class EvaluationTestCase(Base):
    __tablename__ = "evaluation_test_cases"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_id = Column(String(36), ForeignKey("evaluation_datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    
    question = Column(Text, nullable=False)
    ground_truth_answer = Column(Text, nullable=False)
    relevant_doc_titles = Column(JSON, default=list)  # List of expected doc titles/ids
    relevant_passages = Column(JSON, default=list)  # Expected key facts / sentences
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    dataset = relationship("EvaluationDataset", back_populates="test_cases")


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_id = Column(String(36), ForeignKey("evaluation_datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    run_name = Column(String(255), nullable=False)
    llm_provider = Column(String(100), default="openai")
    embedding_provider = Column(String(100), default="sentence-transformers")
    reranker_used = Column(String(100), default="cross-encoder")
    
    # Aggregated Mathematical Metrics
    mean_precision_at_k = Column(Float, default=0.0)
    mean_recall_at_k = Column(Float, default=0.0)
    mean_mrr = Column(Float, default=0.0)  # Mean Reciprocal Rank
    mean_ndcg = Column(Float, default=0.0)  # Normalized Discounted Cumulative Gain
    mean_faithfulness = Column(Float, default=0.0)  # Faithfulness score 0.0 - 1.0
    mean_answer_relevance = Column(Float, default=0.0)
    mean_context_relevance = Column(Float, default=0.0)
    mean_citation_accuracy = Column(Float, default=0.0)
    
    total_test_cases = Column(Integer, default=0)
    status = Column(String(50), default="COMPLETED")
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    dataset = relationship("EvaluationDataset", back_populates="runs")
    results = relationship("EvaluationResult", back_populates="run", cascade="all, delete-orphan")


class EvaluationResult(Base):
    __tablename__ = "evaluation_results"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id = Column(String(36), ForeignKey("evaluation_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    test_case_id = Column(String(36), nullable=True)
    
    question = Column(Text, nullable=False)
    ground_truth = Column(Text, nullable=False)
    generated_answer = Column(Text, nullable=False)
    retrieved_contexts = Column(JSON, default=list)
    citations = Column(JSON, default=list)
    
    # Per-question metrics
    precision_at_k = Column(Float, default=0.0)
    recall_at_k = Column(Float, default=0.0)
    reciprocal_rank = Column(Float, default=0.0)
    ndcg_score = Column(Float, default=0.0)
    faithfulness_score = Column(Float, default=0.0)
    answer_relevance_score = Column(Float, default=0.0)
    context_relevance_score = Column(Float, default=0.0)
    citation_accuracy = Column(Float, default=0.0)
    
    latency_ms = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    run = relationship("EvaluationRun", back_populates="results")
