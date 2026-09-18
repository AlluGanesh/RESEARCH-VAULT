from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class SectionBlock:
    title: str
    level: int  # 1 for #, 2 for ##, etc.
    content: str
    page_number: int = 1


@dataclass
class PageData:
    page_number: int
    text: str
    sections: List[SectionBlock] = field(default_factory=list)


@dataclass
class ExtractedDocument:
    title: str
    author: Optional[str] = None
    abstract: Optional[str] = None
    publication_date: Optional[str] = None
    doi_or_url: Optional[str] = None
    topics: List[str] = field(default_factory=list)
    pages: List[PageData] = field(default_factory=list)
    raw_text: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
