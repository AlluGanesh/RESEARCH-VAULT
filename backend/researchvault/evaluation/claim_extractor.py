import re
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class AtomicClaim:
    def __init__(
        self,
        claim_id: str,
        claim_text: str,
        original_sentence: str,
        cited_indices: List[int],
        sentence_index: int = 0
    ):
        self.claim_id = claim_id
        self.claim_text = claim_text
        self.original_sentence = original_sentence
        self.cited_indices = cited_indices
        self.sentence_index = sentence_index

    def to_dict(self) -> Dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "claim_text": self.claim_text,
            "original_sentence": self.original_sentence,
            "cited_indices": self.cited_indices,
            "sentence_index": self.sentence_index
        }


class ClaimExtractor:
    """
    Deconstructs generated AI answers into verifiable, atomic factual claims.
    Parses inline citations [N] to track document provenance links.
    """

    CITATION_PATTERN = re.compile(r'\[(\d+(?:\s*,\s*\d+)*)\]')
    RANGE_CITATION_PATTERN = re.compile(r'\[(\d+)\s*-\s*(\d+)\]')

    # Heuristic sentence delimiters preserving common abbreviations
    SENTENCE_SPLIT_REGEX = re.compile(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|!)\s+')

    # Conversational non-factual phrases to filter out
    BOILERPLATE_PATTERNS = [
        re.compile(r'^(sure|certainly|here is|based on the retrieved|in conclusion|to summarize|as mentioned|according to|overall|in summary|let me know)', re.IGNORECASE),
        re.compile(r'^(i hope this helps|please let me know|feel free to ask)', re.IGNORECASE)
    ]

    def extract_claims(self, answer_text: str) -> List[AtomicClaim]:
        if not answer_text or not answer_text.strip():
            return []

        # 1. Normalize whitespace & bullet markers
        clean_text = answer_text.strip()
        lines = [line.strip() for line in clean_text.splitlines() if line.strip()]

        sentences: List[str] = []
        for line in lines:
            # Strip markdown list markers: - , * , 1. , etc.
            line_content = re.sub(r'^(?:[-*•]|\d+\.)\s*', '', line).strip()
            if not line_content:
                continue

            # Split line into sentences
            splits = self.SENTENCE_SPLIT_REGEX.split(line_content)
            for s in splits:
                s_str = s.strip()
                if len(s_str) > 10:
                    sentences.append(s_str)

        claims: List[AtomicClaim] = []
        claim_counter = 1

        for sent_idx, raw_sentence in enumerate(sentences):
            # Extract citation indices
            cited_indices = self._parse_citations(raw_sentence)

            # Clean citations from sentence to get the core claim
            cleaned_claim = self._clean_citations(raw_sentence).strip()

            # Skip trivial boilerplate greetings
            if self._is_boilerplate(cleaned_claim):
                continue

            # Subdivide compound sentences with contrasting/connective clauses if distinct facts exist
            sub_clauses = self._decompose_into_subclauses(cleaned_claim)

            if len(sub_clauses) > 1:
                for sub in sub_clauses:
                    if len(sub.split()) >= 4:
                        claims.append(
                            AtomicClaim(
                                claim_id=f"c_{claim_counter}",
                                claim_text=sub,
                                original_sentence=raw_sentence,
                                cited_indices=cited_indices,
                                sentence_index=sent_idx
                            )
                        )
                        claim_counter += 1
            else:
                if len(cleaned_claim.split()) >= 4:
                    claims.append(
                        AtomicClaim(
                            claim_id=f"c_{claim_counter}",
                            claim_text=cleaned_claim,
                            original_sentence=raw_sentence,
                            cited_indices=cited_indices,
                            sentence_index=sent_idx
                        )
                    )
                    claim_counter += 1

        return claims

    def _parse_citations(self, text: str) -> List[int]:
        indices: List[int] = []

        # Parse range citations e.g. [1-3]
        for match in self.RANGE_CITATION_PATTERN.finditer(text):
            try:
                start = int(match.group(1))
                end = int(match.group(2))
                indices.extend(range(start, end + 1))
            except ValueError:
                pass

        # Parse list citations e.g. [1], [1, 2]
        for match in self.CITATION_PATTERN.finditer(text):
            raw_nums = match.group(1)
            for part in raw_nums.split(','):
                p_clean = part.strip()
                if p_clean.isdigit():
                    indices.append(int(p_clean))

        return sorted(list(set(indices)))

    def _clean_citations(self, text: str) -> str:
        # Remove [1], [1, 2], [1-3]
        t = self.RANGE_CITATION_PATTERN.sub('', text)
        t = self.CITATION_PATTERN.sub('', t)
        # Collapse multiple spaces
        t = re.sub(r'\s{2,}', ' ', t)
        return t.strip()

    def _is_boilerplate(self, text: str) -> bool:
        for p in self.BOILERPLATE_PATTERNS:
            if p.search(text):
                # Only boilerplate if short or lacks factual verbs/numbers
                if len(text.split()) < 8 and not re.search(r'\d+', text):
                    return True
        return False

    def _decompose_into_subclauses(self, sentence: str) -> List[str]:
        """
        Decomposes long compound sentences separated by semicolons or strong conjunctions
        while preserving semantic clarity.
        """
        # Split on semicolon
        if ';' in sentence:
            parts = [p.strip() for p in sentence.split(';') if len(p.strip()) > 15]
            if len(parts) > 1:
                return parts

        # Check for bullet or structured list within sentence
        return [sentence]


claim_extractor = ClaimExtractor()
