from datetime import datetime, timezone
import uuid
import enum
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Enum, JSON, Float, Boolean
from sqlalchemy.orm import relationship
from researchvault.database.session import Base


class MessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    collection_id = Column(String(36), ForeignKey("collections.id", ondelete="SET NULL"), nullable=True, index=True)
    
    title = Column(String(255), default="New Research Chat", nullable=False)
    mode = Column(String(50), default="rag")  # rag, research, compare
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")


class Message(Base):
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    role = Column(Enum(MessageRole), nullable=False)
    content = Column(Text, nullable=False)
    
    # Query transformation & execution traces if assistant message
    rewritten_query = Column(Text, nullable=True)
    expansion_queries = Column(JSON, default=list)
    latency_ms = Column(Float, default=0.0)
    tokens_used = Column(Integer, default=0)
    
    # Mode specific outputs (e.g. research report / comparison matrix)
    structured_data = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    citations = relationship("Citation", back_populates="message", cascade="all, delete-orphan")


class Citation(Base):
    __tablename__ = "citations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    message_id = Column(String(36), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_id = Column(String(36), ForeignKey("chunks.id", ondelete="SET NULL"), nullable=True)
    
    citation_number = Column(Integer, nullable=False)  # 1, 2, 3...
    document_title = Column(String(500), nullable=False)
    page_number = Column(Integer, default=1)
    section = Column(String(255), default="General")
    passage_text = Column(Text, nullable=False)
    similarity_score = Column(Float, default=0.0)
    rerank_score = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    message = relationship("Message", back_populates="citations")
