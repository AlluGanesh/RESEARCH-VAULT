import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from researchvault.ingestion.extractors.base import ExtractedDocument, PageData, SectionBlock


@dataclass
class ProcessedChunk:
    chunk_index: int
    page_number: int
    section: str
    subsection: Optional[str]
    paragraph_index: int
    content: str
    context_header: str
    token_count: int
    chunk_metadata: Dict[str, Any]


class StructureAwareChunker:
    def __init__(
        self,
        target_chunk_size: int = 500,
        chunk_overlap: int = 100,
        min_chunk_size: int = 50
    ):
        self.target_chunk_size = target_chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size

    def estimate_tokens(self, text: str) -> int:
        # Fast accurate token estimation: approx 1 token = 0.75 words, or len(text.split()) * 1.3
        words = text.split()
        return int(len(words) * 1.3)

    def _split_into_sentences(self, text: str) -> List[str]:
        # Regex for sentence splitting preserving quotes and abbreviations
        sentence_endings = re.compile(r'(?<=[.!?])\s+(?=[A-Z0-9"\'])')
        sentences = sentence_endings.split(text)
        return [s.strip() for s in sentences if s.strip()]

    def chunk_document(
        self,
        doc: ExtractedDocument,
        document_id: str
    ) -> List[ProcessedChunk]:
        processed_chunks: List[ProcessedChunk] = []
        global_chunk_idx = 0

        for page in doc.pages:
            page_num = page.page_number
            sections = page.sections

            if not sections:
                # If no explicit sections on this page, treat page text as general section
                sections = [SectionBlock(title="General", level=1, content=page.text, page_number=page_num)]

            for s_idx, section in enumerate(sections):
                section_title = section.title or "General"
                section_content = section.content.strip()
                if not section_content:
                    continue

                paragraphs = [p.strip() for p in section_content.split("\n\n") if p.strip()]
                if not paragraphs:
                    paragraphs = [section_content]

                current_chunk_sentences = []
                current_tokens = 0
                para_idx = 0

                for para in paragraphs:
                    sentences = self._split_into_sentences(para)
                    if not sentences:
                        sentences = [para]

                    for sent in sentences:
                        sent_tokens = max(1, self.estimate_tokens(sent))
                        
                        if current_tokens + sent_tokens > self.target_chunk_size and current_chunk_sentences:
                            # Flush current chunk
                            chunk_text = " ".join(current_chunk_sentences).strip()
                            if self.estimate_tokens(chunk_text) >= self.min_chunk_size:
                                context_hdr = f"[Document: {doc.title} | Author: {doc.author or 'Unknown'} | Section: {section_title} | Page: {page_num}]"
                                
                                processed_chunks.append(ProcessedChunk(
                                    chunk_index=global_chunk_idx,
                                    page_number=page_num,
                                    section=section_title,
                                    subsection=None,
                                    paragraph_index=para_idx,
                                    content=chunk_text,
                                    context_header=context_hdr,
                                    token_count=self.estimate_tokens(chunk_text),
                                    chunk_metadata={
                                        "document_id": document_id,
                                        "document_title": doc.title,
                                        "author": doc.author or "Unknown",
                                        "page_number": page_num,
                                        "section": section_title,
                                        "chunk_index": global_chunk_idx
                                    }
                                ))
                                global_chunk_idx += 1

                            # Sliding window overlap
                            overlap_sentences = []
                            overlap_tokens = 0
                            for prev_sent in reversed(current_chunk_sentences):
                                prev_tok = max(1, self.estimate_tokens(prev_sent))
                                if overlap_tokens + prev_tok <= self.chunk_overlap:
                                    overlap_sentences.insert(0, prev_sent)
                                    overlap_tokens += prev_tok
                                else:
                                    break
                            
                            current_chunk_sentences = overlap_sentences
                            current_tokens = overlap_tokens

                        current_chunk_sentences.append(sent)
                        current_tokens += sent_tokens

                    para_idx += 1

                # Flush any remaining sentences in section
                if current_chunk_sentences:
                    chunk_text = " ".join(current_chunk_sentences).strip()
                    if self.estimate_tokens(chunk_text) >= 10 or not processed_chunks:
                        context_hdr = f"[Document: {doc.title} | Author: {doc.author or 'Unknown'} | Section: {section_title} | Page: {page_num}]"
                        processed_chunks.append(ProcessedChunk(
                            chunk_index=global_chunk_idx,
                            page_number=page_num,
                            section=section_title,
                            subsection=None,
                            paragraph_index=para_idx,
                            content=chunk_text,
                            context_header=context_hdr,
                            token_count=self.estimate_tokens(chunk_text),
                            chunk_metadata={
                                "document_id": document_id,
                                "document_title": doc.title,
                                "author": doc.author or "Unknown",
                                "page_number": page_num,
                                "section": section_title,
                                "chunk_index": global_chunk_idx
                            }
                        ))
                        global_chunk_idx += 1

        return processed_chunks
