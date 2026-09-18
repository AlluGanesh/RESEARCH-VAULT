import re
import os
from typing import Optional, List
from pypdf import PdfReader
from researchvault.ingestion.extractors.base import ExtractedDocument, PageData, SectionBlock


class PDFExtractor:
    @staticmethod
    def extract(file_path: str, filename: str) -> ExtractedDocument:
        reader = PdfReader(file_path)
        pages_data: List[PageData] = []
        full_text_list = []
        
        # Heuristic patterns for section headers in academic/technical papers
        section_pattern = re.compile(
            r'^(?:\d+\.?\s+|[I|V|X]+\.\s+|[A-Z]\.\s+)?(Abstract|Introduction|Related\s+Work|Background|Methodology|Method|Proposed\s+Method|System\s+Architecture|Architecture|Experiments|Experimental\s+Setup|Results|Evaluation|Discussion|Conclusion|Conclusions|Future\s+Work|References|Ablation\s+Studies|Implementation\s+Details)(?:[:\.\s]|$)',
            re.IGNORECASE
        )
        
        title = filename.rsplit(".", 1)[0].replace("_", " ").replace("-", " ")
        author = None
        abstract_text = None
        
        # Read document metadata if available
        if reader.metadata:
            if reader.metadata.title:
                clean_t = reader.metadata.title.strip()
                if len(clean_t) > 3:
                    title = clean_t
            if reader.metadata.author:
                author = reader.metadata.author.strip()

        for idx, page in enumerate(reader.pages):
            page_num = idx + 1
            text = page.extract_text() or ""
            text = text.replace("\x00", "")  # strip null bytes
            full_text_list.append(text)
            
            # Detect sections in page
            lines = text.split("\n")
            current_section_title = "General" if page_num > 1 else "Introduction"
            current_section_lines = []
            sections: List[SectionBlock] = []
            
            for line in lines:
                clean_line = line.strip()
                if not clean_line:
                    continue
                
                # Check for section match
                match = section_pattern.match(clean_line)
                if match and len(clean_line) < 80:
                    # Save previous section if it had content
                    if current_section_lines:
                        sections.append(SectionBlock(
                            title=current_section_title,
                            level=1,
                            content="\n".join(current_section_lines),
                            page_number=page_num
                        ))
                        current_section_lines = []
                    current_section_title = clean_line
                else:
                    current_section_lines.append(clean_line)
                    
                    # Try to capture abstract from page 1
                    if page_num == 1 and not abstract_text and "abstract" in current_section_title.lower():
                        if len(current_section_lines) > 2:
                            abstract_text = " ".join(current_section_lines[:10])

            if current_section_lines:
                sections.append(SectionBlock(
                    title=current_section_title,
                    level=1,
                    content="\n".join(current_section_lines),
                    page_number=page_num
                ))

            pages_data.append(PageData(
                page_number=page_num,
                text=text,
                sections=sections
            ))

        full_raw_text = "\n\n--- Page Break ---\n\n".join(full_text_list)
        
        # Fallback for title extraction if title is still just the filename
        if pages_data and len(pages_data[0].text) > 0:
            first_lines = [l.strip() for l in pages_data[0].text.split("\n") if len(l.strip()) > 5]
            if first_lines and len(first_lines[0]) < 150:
                # Often the first prominent line of page 1 is the paper title
                first_line = first_lines[0]
                if not any(kw in first_line.lower() for kw in ["arxiv", "ieee", "acm", "proceedings", "conference", "http", "doi"]):
                    title = first_line

        return ExtractedDocument(
            title=title,
            author=author or "Unknown Author",
            abstract=abstract_text[:1000] if abstract_text else None,
            pages=pages_data,
            raw_text=full_raw_text,
            metadata={"total_pages": len(pages_data)}
        )
