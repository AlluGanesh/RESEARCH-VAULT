import re
from typing import List, Dict, Any, Optional, Tuple
import logging
import json

from researchvault.evaluation.claim_extractor import AtomicClaim
from researchvault.generation.llm_service import llm_service

logger = logging.getLogger(__name__)


class VerificationVerdict:
    SUPPORTED = "SUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    UNVERIFIABLE = "UNVERIFIABLE"  # Unsupported by retrieved evidence


class ClaimVerificationResult:
    def __init__(
        self,
        claim: AtomicClaim,
        verdict: str,
        confidence: float,
        evidence_snippet: Optional[str] = None,
        matched_doc_title: Optional[str] = None,
        matched_chunk_id: Optional[str] = None,
        citation_valid: bool = False,
        explanation: Optional[str] = None
    ):
        self.claim = claim
        self.verdict = verdict
        self.confidence = confidence
        self.evidence_snippet = evidence_snippet
        self.matched_doc_title = matched_doc_title
        self.matched_chunk_id = matched_chunk_id
        self.citation_valid = citation_valid
        self.explanation = explanation

    def to_dict(self) -> Dict[str, Any]:
        return {
            "claim_id": self.claim.claim_id,
            "claim_text": self.claim.claim_text,
            "original_sentence": self.claim.original_sentence,
            "cited_indices": self.claim.cited_indices,
            "verdict": self.verdict,
            "confidence": round(self.confidence, 3),
            "evidence_snippet": self.evidence_snippet,
            "matched_doc_title": self.matched_doc_title,
            "matched_chunk_id": self.matched_chunk_id,
            "citation_valid": self.citation_valid,
            "explanation": self.explanation
        }


class EvidenceVerifier:
    """
    Evaluates atomic claims against retrieved evidence passages using Natural Language
    Inference (NLI) heuristics and structured LLM verification.
    """

    NEGATION_WORDS = {
        "not", "never", "no", "none", "neither", "fails", "cannot",
        "without", "disproved", "eschewing", "eschew", "dispensing",
        "eliminating", "avoids", "opposed"
    }
    
    def __init__(self, use_llm_judge: bool = False):
        self.use_llm_judge = use_llm_judge

    async def verify_claims(
        self,
        claims: List[AtomicClaim],
        evidence_passages: List[Dict[str, Any]],
        llm_provider: Optional[str] = None
    ) -> List[ClaimVerificationResult]:
        """
        Verifies each atomic claim against the pool of evidence passages.
        """
        results: List[ClaimVerificationResult] = []

        for claim in claims:
            res = await self.verify_single_claim(claim, evidence_passages, llm_provider=llm_provider)
            results.append(res)

        return results

    async def verify_single_claim(
        self,
        claim: AtomicClaim,
        evidence_passages: List[Dict[str, Any]],
        llm_provider: Optional[str] = None
    ) -> ClaimVerificationResult:
        if not evidence_passages:
            return ClaimVerificationResult(
                claim=claim,
                verdict=VerificationVerdict.UNVERIFIABLE,
                confidence=0.95,
                explanation="No retrieved evidence passages were provided for verification."
            )

        # 1. Identify priority passages matching cited citation indices [1], [2]
        priority_passages = self._get_cited_passages(claim.cited_indices, evidence_passages)

        # 2. If LLM judge is enabled and not local fallback, try structured LLM verification
        if self.use_llm_judge and llm_provider and llm_provider != "local":
            try:
                llm_res = await self._verify_with_llm(claim, priority_passages or evidence_passages, llm_provider)
                if llm_res:
                    return llm_res
            except Exception as e:
                logger.warning(f"LLM evidence verification failed, falling back to NLI heuristic: {e}")

        # 3. Deterministic NLI / Lexical-Semantic heuristic verification
        return self._verify_with_nli_heuristics(claim, priority_passages, evidence_passages)

    def _get_cited_passages(
        self,
        cited_indices: List[int],
        evidence_passages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        cited_list = []
        for idx in cited_indices:
            # 1-based index matching
            if 1 <= idx <= len(evidence_passages):
                cited_list.append(evidence_passages[idx - 1])
        return cited_list

    def _verify_with_nli_heuristics(
        self,
        claim: AtomicClaim,
        cited_passages: List[Dict[str, Any]],
        all_passages: List[Dict[str, Any]]
    ) -> ClaimVerificationResult:
        """
        Heuristic NLI algorithm:
        - Extracts content words, entities, and numeric assertions from the claim.
        - Compares against each evidence sentence.
        - Checks for contradictory numbers, opposite polarities (negations), or lack of support.
        """
        claim_text = claim.claim_text.lower()
        claim_tokens = set(re.findall(r'\b[a-z0-9_-]{3,}\b', claim_text))
        claim_numbers = set(re.findall(r'\b\d+(?:\.\d+)?%?\b', claim.claim_text))
        claim_has_negation = bool(self.NEGATION_WORDS.intersection(set(claim_text.split())))

        best_score = 0.0
        best_passage: Optional[Dict[str, Any]] = None
        best_sentence: Optional[str] = None
        verdict = VerificationVerdict.UNVERIFIABLE
        contradiction_detected = False
        contradiction_sentence = ""

        # Search prioritized cited passages first, then all passages
        search_passages = cited_passages if cited_passages else all_passages

        for passage_dict in search_passages:
            p_text = passage_dict.get("passage_text") or passage_dict.get("content", "")
            doc_title = passage_dict.get("document_title") or passage_dict.get("title", "Retrieved Document")
            
            # Sentence split of evidence passage
            p_sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', p_text) if len(s.strip()) > 15]

            for s in p_sentences:
                s_lower = s.lower()
                s_tokens = set(re.findall(r'\b[a-z0-9_-]{3,}\b', s_lower))
                s_numbers = set(re.findall(r'\b\d+(?:\.\d+)?%?\b', s))
                s_has_negation = bool(self.NEGATION_WORDS.intersection(set(s_lower.split())))

                if not claim_tokens:
                    continue

                token_overlap = len(claim_tokens.intersection(s_tokens)) / len(claim_tokens)

                # Check for direct contradictions (e.g. polarity flip or conflicting numbers)
                if token_overlap >= 0.40:
                    # Filter out 4-digit years (e.g. 1990-2099) so years don't mask metric differences
                    claim_metric_nums = {
                        n for n in claim_numbers 
                        if not (n.isdigit() and len(n) == 4 and 1900 <= int(n) <= 2099)
                    }
                    s_metric_nums = {
                        n for n in s_numbers 
                        if not (n.isdigit() and len(n) == 4 and 1900 <= int(n) <= 2099)
                    }

                    # Number conflict: claim asserts metric numbers differing from evidence numbers
                    if claim_metric_nums and s_metric_nums:
                        if not claim_metric_nums.intersection(s_metric_nums):
                            contradiction_detected = True
                            contradiction_sentence = s
                            best_passage = passage_dict
                            break

                    # Polarity contradiction: one is negated, other is positive with high lexical overlap
                    if (claim_has_negation != s_has_negation) and token_overlap >= 0.50:
                        contradiction_detected = True
                        contradiction_sentence = s
                        best_passage = passage_dict
                        break


                if token_overlap > best_score:
                    best_score = token_overlap
                    best_passage = passage_dict
                    best_sentence = s

        # Evaluate verdict based on highest overlap & contradiction
        if contradiction_detected:
            verdict = VerificationVerdict.CONTRADICTED
            confidence = min(0.95, 0.65 + best_score * 0.3)
            snippet = contradiction_sentence
            explanation = f"Contradiction detected: Evidence contradicts claim's assertion or numerical values."
        elif best_score >= 0.50:
            verdict = VerificationVerdict.SUPPORTED
            confidence = min(0.98, 0.55 + best_score * 0.45)
            snippet = best_sentence
            explanation = f"Supported: Evidence passage demonstrates strong semantic and lexical entailment ({int(best_score * 100)}% term alignment)."
        elif best_score >= 0.30:
            # Partial support or weak ground
            verdict = VerificationVerdict.UNVERIFIABLE
            confidence = 0.65
            snippet = best_sentence
            explanation = f"Unverifiable: Relevant topics appear in evidence, but core proposition is not explicitly established."
        else:
            verdict = VerificationVerdict.UNVERIFIABLE
            confidence = 0.90
            snippet = None
            explanation = "Unverifiable: No retrieved evidence passages substantiate this claim."

        # Validate citation: does cited index actually point to supporting evidence?
        citation_valid = False
        if claim.cited_indices and cited_passages and verdict == VerificationVerdict.SUPPORTED:
            citation_valid = True

        return ClaimVerificationResult(
            claim=claim,
            verdict=verdict,
            confidence=confidence,
            evidence_snippet=snippet,
            matched_doc_title=best_passage.get("document_title") if best_passage else None,
            matched_chunk_id=best_passage.get("chunk_id") if best_passage else None,
            citation_valid=citation_valid,
            explanation=explanation
        )

    async def _verify_with_llm(
        self,
        claim: AtomicClaim,
        passages: List[Dict[str, Any]],
        llm_provider: str
    ) -> Optional[ClaimVerificationResult]:
        context_str = "\n".join([
            f"[{i+1}] {p.get('document_title', 'Doc')}: {p.get('passage_text', p.get('content', ''))}"
            for i, p in enumerate(passages[:5])
        ])

        system_prompt = (
            "You are a strict scientific Fact Verification and Natural Language Inference (NLI) judge. "
            "Your task is to classify whether the provided atomic claim is SUPPORTED, CONTRADICTED, or UNVERIFIABLE "
            "based strictly and solely on the provided evidence context. "
            "Respond ONLY with a JSON object in the exact format:\n"
            '{"verdict": "SUPPORTED" | "CONTRADICTED" | "UNVERIFIABLE", "confidence": 0.0-1.0, '
            '"evidence_snippet": "exact supporting or refuting quote", "citation_valid": true | false, '
            '"explanation": "concise rationale"}'
        )

        prompt = (
            f"Atomic Claim: {claim.claim_text}\n"
            f"Cited Reference Numbers: {claim.cited_indices}\n\n"
            f"Retrieved Evidence:\n{context_str}\n\n"
            f"Evaluate claim:"
        )

        res_text = await llm_service.generate_text(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.0,
            provider_override=llm_provider
        )

        # Parse JSON from LLM response
        match = re.search(r'\{[\s\S]*\}', res_text)
        if match:
            parsed = json.loads(match.group(0))
            raw_v = str(parsed.get("verdict", "")).upper()
            if "SUPPORT" in raw_v:
                verdict = VerificationVerdict.SUPPORTED
            elif "CONTRADICT" in raw_v:
                verdict = VerificationVerdict.CONTRADICTED
            else:
                verdict = VerificationVerdict.UNVERIFIABLE

            return ClaimVerificationResult(
                claim=claim,
                verdict=verdict,
                confidence=float(parsed.get("confidence", 0.85)),
                evidence_snippet=parsed.get("evidence_snippet"),
                matched_doc_title=passages[0].get("document_title") if passages else None,
                matched_chunk_id=passages[0].get("chunk_id") if passages else None,
                citation_valid=bool(parsed.get("citation_valid", False)),
                explanation=parsed.get("explanation")
            )

        return None


evidence_verifier = EvidenceVerifier()
