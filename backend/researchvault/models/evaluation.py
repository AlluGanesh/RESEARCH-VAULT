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


class HybridBenchmarkRun(Base):
    __tablename__ = "hybrid_benchmark_runs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_id = Column(String(36), ForeignKey("evaluation_datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    dataset_name = Column(String(255), nullable=False)
    k = Column(Integer, default=10)
    total_test_cases = Column(Integer, default=0)

    # JSON representation of curve points
    benchmark_curves = Column(JSON, default=list)

    # Optimal ratio findings
    optimal_dense_weight = Column(Float, default=0.6)
    optimal_sparse_weight = Column(Float, default=0.4)
    peak_ndcg = Column(Float, default=0.0)
    peak_recall = Column(Float, default=0.0)
    composite_score = Column(Float, default=0.0)
    estimated_hallucination_rate = Column(Float, default=0.0)
    rationale = Column(Text, nullable=True)

    execution_time_ms = Column(Float, default=0.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class HallucinationAuditLog(Base):
    __tablename__ = "hallucination_audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    query = Column(Text, nullable=True)
    answer_text = Column(Text, nullable=False)
    total_claims = Column(Integer, default=0)
    supported_count = Column(Integer, default=0)
    contradicted_count = Column(Integer, default=0)
    unverifiable_count = Column(Integer, default=0)

    hallucination_rate = Column(Float, default=0.0)
    claim_support_rate = Column(Float, default=0.0)
    contradiction_rate = Column(Float, default=0.0)
    unverifiable_rate = Column(Float, default=0.0)
    citation_accuracy = Column(Float, default=0.0)

    verified_claims = Column(JSON, default=list)
    execution_time_ms = Column(Float, default=0.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

