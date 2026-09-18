from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from researchvault.database.session import Base


class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    
    chunk_index = Column(Integer, nullable=False, index=True)
    page_number = Column(Integer, default=1, nullable=False, index=True)
    section = Column(String(255), default="General", nullable=False)
    subsection = Column(String(255), nullable=True)
    paragraph_index = Column(Integer, default=0)
    
    # Text content & contextual header
    content = Column(Text, nullable=False)
    context_header = Column(Text, nullable=True)  # e.g., "[Doc: Title | Section: 2.1 | Page: 4]"
    token_count = Column(Integer, default=0)
    
    # Qdrant Vector Point ID
    qdrant_point_id = Column(String(64), nullable=True, index=True)
    
    # Additional chunk-level metadata
    chunk_metadata = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    document = relationship("Document", back_populates="chunks")
