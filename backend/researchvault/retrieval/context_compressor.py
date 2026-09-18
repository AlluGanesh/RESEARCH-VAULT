import re
from typing import List, Dict, Any, Tuple


class ContextCompressor:
    def __init__(self, max_tokens_per_chunk: int = 350):
        self.max_tokens_per_chunk = max_tokens_per_chunk

    def _split_sentences(self, text: str) -> List[str]:
        sentence_endings = re.compile(r'(?<=[.!?])\s+(?=[A-Z0-9"\'])')
        sents = sentence_endings.split(text)
        return [s.strip() for s in sents if s.strip()]

    def _score_sentence(self, sentence: str, query_words: set) -> float:
        s_words = set(re.findall(r'\b\w{3,}\b', sentence.lower()))
        if not s_words:
            return 0.0
        overlap = len(query_words.intersection(s_words))
        length_penalty = 1.0 if len(sentence.split()) > 6 else 0.5
        return (overlap / (len(s_words) ** 0.5)) * length_penalty

    def compress_chunks(
        self,
        query: str,
        chunks: List[Dict[str, Any]]
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Compresses retrieved chunks into an optimized context prompt.
        Returns (formatted_prompt_context, enriched_chunks_with_passage).
        """
        if not chunks:
            return "", []

        query_words = set(re.findall(r'\b\w{3,}\b', query.lower()))
        compressed_chunks = []
        context_blocks = []

        for idx, chunk in enumerate(chunks):
            citation_num = idx + 1
            content = chunk.get("content", "")
            sentences = self._split_sentences(content)

            if len(sentences) <= 3:
                selected_passage = content
            else:
                # Score sentences
                scored_sents = [(s, self._score_sentence(s, query_words)) for s in sentences]
                # Always include first sentence if introductory, and highest-scoring sentences
                high_scoring = sorted(scored_sents, key=lambda x: x[1], reverse=True)
                top_sents = set(s for s, score in high_scoring[:4])
                
                # Keep original document order of selected sentences
                selected_ordered = [s for s in sentences if s in top_sents]
                selected_passage = " ".join(selected_ordered) if selected_ordered else content

            doc_title = chunk.get("document_title", "Document")
            page_num = chunk.get("page_number", 1)
            section = chunk.get("section", "General")
            
            header = f"[{citation_num}] [Document: {doc_title} | Page: {page_num} | Section: {section}]"
            block = f"{header}\n{selected_passage}"
            context_blocks.append(block)

            enriched = dict(chunk)
            enriched["citation_number"] = citation_num
            enriched["passage_text"] = selected_passage
            compressed_chunks.append(enriched)

        final_context_str = "\n\n".join(context_blocks)
        return final_context_str, compressed_chunks


# Global instance
context_compressor = ContextCompressor()
