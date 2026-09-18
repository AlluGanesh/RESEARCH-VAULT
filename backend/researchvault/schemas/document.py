from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime
from researchvault.models.document import DocumentStatus


class ChunkResponse(BaseModel):
    id: str
    document_id: str
    chunk_index: int
    page_number: int
    section: str
    subsection: Optional[str] = None
    content: str
    context_header: Optional[str] = None
    token_count: int
    similarity_score: Optional[float] = None
    rerank_score: Optional[float] = None

    class Config:
        from_attributes = True


class DocumentResponse(BaseModel):
    id: str
    user_id: str
    collection_id: Optional[str] = None
    title: str
    original_filename: str
    file_type: str
    file_size_bytes: int
    author: Optional[str] = None
    abstract: Optional[str] = None
    publication_date: Optional[str] = None
    doi_or_url: Optional[str] = None
    topics: List[str] = []
    page_count: int = 0
    chunk_count: int = 0
    token_count: int = 0
    status: DocumentStatus
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentDetailResponse(DocumentResponse):
    chunks: List[ChunkResponse] = []


class DocumentProcessRequest(BaseModel):
    chunk_size: Optional[int] = 500
    chunk_overlap: Optional[int] = 100
