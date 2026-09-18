from datetime import datetime, timezone
import uuid
import enum
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from researchvault.database.session import Base


class DocumentStatus(str, enum.Enum):
    UPLOADED = "UPLOADED"
    EXTRACTING = "EXTRACTING"
    CHUNKING = "CHUNKING"
    EMBEDDING = "EMBEDDING"
    INDEXING = "INDEXING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    collection_id = Column(String(36), ForeignKey("collections.id", ondelete="SET NULL"), nullable=True, index=True)
    
    title = Column(String(500), nullable=False)
    original_filename = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)
    file_type = Column(String(50), nullable=False)  # pdf, docx, txt, md
    file_size_bytes = Column(Integer, default=0)
    
    # Metadata extracted
    author = Column(String(500), nullable=True)
    abstract = Column(Text, nullable=True)
    publication_date = Column(String(100), nullable=True)
    doi_or_url = Column(String(500), nullable=True)
    topics = Column(JSON, default=list)  # List of keywords/tags
    doc_metadata = Column(JSON, default=dict)
    
    # Ingestion stats
    page_count = Column(Integer, default=0)
    chunk_count = Column(Integer, default=0)
    token_count = Column(Integer, default=0)
    
    # Status & Error
    status = Column(Enum(DocumentStatus), default=DocumentStatus.UPLOADED, nullable=False, index=True)
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="documents")
    collection = relationship("Collection", back_populates="documents")
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")
