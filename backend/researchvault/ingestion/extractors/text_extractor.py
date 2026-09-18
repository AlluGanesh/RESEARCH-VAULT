import re
from typing import List
from researchvault.ingestion.extractors.base import ExtractedDocument, PageData, SectionBlock


class TextExtractor:
    @staticmethod
    def extract(file_path: str, filename: str) -> ExtractedDocument:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            raw_text = f.read()

        title = filename.rsplit(".", 1)[0].replace("_", " ").replace("-", " ")
        lines = raw_text.split("\n")
        
        # Check first markdown heading # Title
        for line in lines[:10]:
            if line.strip().startswith("# "):
                title = line.strip("# ").strip()
                break

        sections: List[SectionBlock] = []
        current_section = "Introduction"
        current_level = 1
        current_content = []

        for line in lines:
            stripped = line.strip()
            # Markdown heading check
            if stripped.startswith("#"):
                match = re.match(r'^(#{1,6})\s+(.+)$', stripped)
                if match:
                    if current_content:
                        sections.append(SectionBlock(
                            title=current_section,
                            level=current_level,
                            content="\n".join(current_content),
                            page_number=1
                        ))
                        current_content = []
                    current_level = len(match.group(1))
                    current_section = match.group(2)
                    continue
            current_content.append(line)

        if current_content:
            sections.append(SectionBlock(
                title=current_section,
                level=current_level,
                content="\n".join(current_content),
                page_number=1
            ))

        # Approximate pages (~500 words/page)
        words = raw_text.split()
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
            pages=pages,
            raw_text=raw_text,
            metadata={"character_count": len(raw_text)}
        )
