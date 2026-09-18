from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class NodeSchema(BaseModel):
    id: str
    name: str
    entity_type: str  # Author, Model, Dataset, Method, Concept
    description: Optional[str] = None
    properties: Dict[str, Any] = {}


class EdgeSchema(BaseModel):
    id: str
    source_id: str
    target_id: str
    relation_type: str
    weight: int = 1
    evidence_text: Optional[str] = None
    document_id: Optional[str] = None


class KnowledgeGraphResponse(BaseModel):
    nodes: List[NodeSchema] = []
    edges: List[EdgeSchema] = []
