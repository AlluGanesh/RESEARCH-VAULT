from typing import List
import docx
from researchvault.ingestion.extractors.base import ExtractedDocument, PageData, SectionBlock


class DocxExtractor:
    @staticmethod
    def extract(file_path: str, filename: str) -> ExtractedDocument:
        doc = docx.Document(file_path)
        title = filename.rsplit(".", 1)[0].replace("_", " ").replace("-", " ")
        author = None
        
        # Read core properties
        core_props = doc.core_properties
        if core_props.title and len(core_props.title.strip()) > 2:
            title = core_props.title.strip()
        if core_props.author:
            author = core_props.author.strip()

        sections: List[SectionBlock] = []
        current_section = "Introduction"
        current_content = []
        full_paragraphs = []

        for p in doc.paragraphs:
            text = p.text.strip()
            if not text:
                continue
            full_paragraphs.append(text)
            
            # Check if paragraph is heading style
            if p.style and p.style.name and p.style.name.startswith("Heading"):
                if current_content:
                    sections.append(SectionBlock(
                        title=current_section,
                        level=1,
                        content="\n".join(current_content),
                        page_number=1
                    ))
                    current_content = []
                current_section = text
            else:
                current_content.append(text)

        if current_content:
            sections.append(SectionBlock(
                title=current_section,
                level=1,
                content="\n".join(current_content),
                page_number=1
            ))

        # Docx does not have explicit physical page breaks reliably without rendering, treat ~600 words per page
        full_text = "\n\n".join(full_paragraphs)
        words = full_text.split()
        words_per_page = 500
        pages: List[PageData] = []
        
        if not words:
            pages.append(PageData(page_number=1, text="", sections=sections))
        else:
            total_pages = max(1, (len(words) + words_per_page - 1) // words_per_page)
            for p_idx in range(total_pages):
                page_words = words[p_idx * words_per_page : (p_idx + 1) * words_per_page]
                pages.append(PageData(
                    page_number=p_idx + 1,
                    text=" ".join(page_words),
                    sections=sections if p_idx == 0 else []
                ))

        return ExtractedDocument(
            title=title,
            author=author or "Unknown Author",
            pages=pages,
            raw_text=full_text,
            metadata={"paragraph_count": len(doc.paragraphs)}
        )
