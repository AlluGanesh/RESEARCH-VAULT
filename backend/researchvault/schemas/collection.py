from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime


class CollectionCreate(BaseModel):
    name: str
    description: Optional[str] = None
    color: Optional[str] = "#6366f1"


class CollectionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None


class CollectionResponse(BaseModel):
    id: str
    user_id: str
    name: str
    description: Optional[str] = None
    color: str
    document_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
