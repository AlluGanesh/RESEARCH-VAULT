from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, JSON
from researchvault.database.session import Base


class EntityNode(Base):
    __tablename__ = "entity_nodes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    name = Column(String(255), nullable=False, index=True)
    entity_type = Column(String(100), nullable=False, index=True)  # Author, Model, Dataset, Method, Concept, Organization
    description = Column(Text, nullable=True)
    properties = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class RelationEdge(Base):
    __tablename__ = "relation_edges"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_id = Column(String(36), ForeignKey("entity_nodes.id", ondelete="CASCADE"), nullable=False, index=True)
    target_id = Column(String(36), ForeignKey("entity_nodes.id", ondelete="CASCADE"), nullable=False, index=True)
    
    relation_type = Column(String(100), nullable=False, index=True)  # WROTE, PROPOSES, EVALUATES_ON, IMPROVES, EXTENDS, USES
    weight = Column(Integer, default=1)
    evidence_text = Column(Text, nullable=True)
    document_id = Column(String(36), nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
