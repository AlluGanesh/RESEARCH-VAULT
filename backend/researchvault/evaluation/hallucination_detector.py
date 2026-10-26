import time
import logging
from typing import List, Dict, Any, Optional

from researchvault.evaluation.claim_extractor import claim_extractor, AtomicClaim
from researchvault.evaluation.evidence_verifier import (
    evidence_verifier,
    ClaimVerificationResult,
    VerificationVerdict
)

logger = logging.getLogger(__name__)


# Standard human-labeled benchmark examples for testing and verifying the detector
HUMAN_LABELED_GOLD_BENCHMARK = [
    {
        "id": "gold_1",
        "question": "What is the primary contribution and architecture of the Transformer model?",
        "claim_text": "The Transformer relies entirely on self-attention mechanisms, dispensing with recurrence and convolutions entirely.",
        "context_passages": [
            "We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely."
        ],
        "gold_verdict": "SUPPORTED"
    },
    {
        "id": "gold_2",
        "question": "What BLEU score did the big transformer achieve on English-to-German translation?",
        "claim_text": "On the WMT 2014 English-to-German translation task, the Transformer achieved a BLEU score of 52.4.",
        "context_passages": [
            "On the WMT 2014 English-to-German translation task, the big transformer model achieves a state-of-the-art BLEU score of 28.4, outperforming existing best models by over 2.0 BLEU."
        ],
        "gold_verdict": "CONTRADICTED"
    },
    {
        "id": "gold_3",
        "question": "Does the Transformer use recurrent neural connections?",
        "claim_text": "The Transformer architecture relies on recurrent LSTM layers to model sequential dependencies.",
        "context_passages": [
            "We propose the Transformer, a model architecture eschewing recurrence and convolutions, instead relying entirely on an attention mechanism."
        ],
        "gold_verdict": "CONTRADICTED"
    },
    {
        "id": "gold_4",
        "question": "Does Self-RAG improve reasoning benchmarks?",
        "claim_text": "Self-RAG improves open-domain QA and reasoning benchmarks like ARC and GSM8K while reducing unnecessary retrieval steps.",
        "context_passages": [
            "Experiments across open-domain QA (PopQA, TriviaQA), reasoning (ARC, GSM8K), and fact-checking (FactScore) show that Self-RAG significantly outperforms standard RAG and reduces unnecessary retrieval steps by over 60%."
        ],
        "gold_verdict": "SUPPORTED"
    },
    {
        "id": "gold_5",
        "question": "What optimizer was used in the RAG paper?",
        "claim_text": "Patrick Lewis et al. trained RAG with the Lion optimizer and cosine decay schedule.",
        "context_passages": [
            "RAG pairs a pre-trained sequence-to-sequence model with a non-parametric dense vector index of Wikipedia accessed via a neural retriever (DPR)."
        ],
        "gold_verdict": "UNVERIFIABLE"
    }
]


class HallucinationReport:
    def __init__(
        self,
        total_claims: int,
        supported_count: int,
        contradicted_count: int,
        unverifiable_count: int,
        hallucination_rate: float,
        claim_support_rate: float,
        contradiction_rate: float,
        unverifiable_rate: float,
        citation_valid_count: int,
        total_citations_checked: int,
        citation_accuracy: float,
        verified_claims: List[ClaimVerificationResult],
        execution_time_ms: float
    ):
        self.total_claims = total_claims
        self.supported_count = supported_count
        self.contradicted_count = contradicted_count
        self.unverifiable_count = unverifiable_count
        self.hallucination_rate = hallucination_rate
        self.claim_support_rate = claim_support_rate
        self.contradiction_rate = contradiction_rate
        self.unverifiable_rate = unverifiable_rate
        self.citation_valid_count = citation_valid_count
        self.total_citations_checked = total_citations_checked
        self.citation_accuracy = citation_accuracy
        self.verified_claims = verified_claims
        self.execution_time_ms = execution_time_ms

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_claims": self.total_claims,
            "supported_count": self.supported_count,
            "contradicted_count": self.contradicted_count,
            "unverifiable_count": self.unverifiable_count,
            "hallucination_rate": round(self.hallucination_rate, 2),
            "claim_support_rate": round(self.claim_support_rate, 2),
            "contradiction_rate": round(self.contradiction_rate, 2),
            "unverifiable_rate": round(self.unverifiable_rate, 2),
            "citation_valid_count": self.citation_valid_count,
            "total_citations_checked": self.total_citations_checked,
            "citation_accuracy": round(self.citation_accuracy, 2),
            "verified_claims": [c.to_dict() for c in self.verified_claims],
            "execution_time_ms": round(self.execution_time_ms, 2)
        }


class HallucinationDetector:
    """
    Sentence and claim-level hallucination detection engine.
    Measures whether AI answers generate claims unsupported or contradicted
    by retrieved research documents.
    """

    def __init__(self, use_llm_judge: bool = False):
        self.use_llm_judge = use_llm_judge

    async def detect_hallucinations(
        self,
        answer_text: str,
        retrieved_contexts: List[Dict[str, Any]],
        llm_provider: Optional[str] = None
    ) -> HallucinationReport:
        start_time = time.time()

        # 1. Claim Extraction
        claims: List[AtomicClaim] = claim_extractor.extract_claims(answer_text)

        if not claims:
            exec_time = (time.time() - start_time) * 1000.0
            return HallucinationReport(
                total_claims=0,
                supported_count=0,
                contradicted_count=0,
                unverifiable_count=0,
                hallucination_rate=0.0,
                claim_support_rate=100.0,
                contradiction_rate=0.0,
                unverifiable_rate=0.0,
                citation_valid_count=0,
                total_citations_checked=0,
                citation_accuracy=100.0,
                verified_claims=[],
                execution_time_ms=exec_time
            )

        # 2. Evidence Verification
        verified_claims: List[ClaimVerificationResult] = await evidence_verifier.verify_claims(
            claims=claims,
            evidence_passages=retrieved_contexts,
            llm_provider=llm_provider
        )

        # 3. Quantitative Hallucination Scoring
        total = len(verified_claims)
        supported = sum(1 for c in verified_claims if c.verdict == VerificationVerdict.SUPPORTED)
        contradicted = sum(1 for c in verified_claims if c.verdict == VerificationVerdict.CONTRADICTED)
        unverifiable = sum(1 for c in verified_claims if c.verdict == VerificationVerdict.UNVERIFIABLE)

        # Hallucination Rate = (Unsupported + Contradicted) / Total Claims * 100
        hallucination_rate = ((unverifiable + contradicted) / total * 100.0) if total > 0 else 0.0
        claim_support_rate = (supported / total * 100.0) if total > 0 else 0.0
        contradiction_rate = (contradicted / total * 100.0) if total > 0 else 0.0
        unverifiable_rate = (unverifiable / total * 100.0) if total > 0 else 0.0

        # Citations check
        cited_claims = [c for c in verified_claims if c.claim.cited_indices]
        valid_citations = sum(1 for c in cited_claims if c.citation_valid)
        total_citations = len(cited_claims)
        citation_acc = (valid_citations / total_citations * 100.0) if total_citations > 0 else 100.0

        exec_time = (time.time() - start_time) * 1000.0

        return HallucinationReport(
            total_claims=total,
            supported_count=supported,
            contradicted_count=contradicted,
            unverifiable_count=unverifiable,
            hallucination_rate=hallucination_rate,
            claim_support_rate=claim_support_rate,
            contradiction_rate=contradiction_rate,
            unverifiable_rate=unverifiable_rate,
            citation_valid_count=valid_citations,
            total_citations_checked=total_citations,
            citation_accuracy=citation_acc,
            verified_claims=verified_claims,
            execution_time_ms=exec_time
        )

    async def evaluate_against_human_benchmark(self) -> Dict[str, Any]:
        """
        Evaluates the accuracy and agreement of the hallucination detector
        against human-labeled ground truth benchmark examples.
        """
        correct_matches = 0
        total = len(HUMAN_LABELED_GOLD_BENCHMARK)
        details = []

        for item in HUMAN_LABELED_GOLD_BENCHMARK:
            claim = AtomicClaim(
                claim_id=item["id"],
                claim_text=item["claim_text"],
                original_sentence=item["claim_text"],
                cited_indices=[1]
            )
            contexts = [{"passage_text": p, "document_title": "Gold Research Document"} for p in item["context_passages"]]
            res = await evidence_verifier.verify_single_claim(claim, contexts)

            is_correct = (res.verdict == item["gold_verdict"])
            if is_correct:
                correct_matches += 1

            details.append({
                "id": item["id"],
                "claim": item["claim_text"],
                "gold_verdict": item["gold_verdict"],
                "predicted_verdict": res.verdict,
                "confidence": res.confidence,
                "is_match": is_correct
            })

        accuracy = (correct_matches / total * 100.0) if total > 0 else 100.0

        return {
            "total_benchmark_cases": total,
            "correct_matches": correct_matches,
            "benchmark_accuracy": round(accuracy, 2),
            "test_cases": details
        }


hallucination_detector = HallucinationDetector()
