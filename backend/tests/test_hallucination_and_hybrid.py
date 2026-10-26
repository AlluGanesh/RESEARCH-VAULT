import pytest
from researchvault.evaluation.claim_extractor import claim_extractor, AtomicClaim
from researchvault.evaluation.evidence_verifier import (
    evidence_verifier,
    VerificationVerdict
)
from researchvault.evaluation.hallucination_detector import hallucination_detector
from researchvault.evaluation.hybrid_metrics import HybridDiagnosticMetrics


def test_claim_extractor_citations_and_claims():
    text = (
        "The Transformer relies entirely on self-attention mechanisms [1]. "
        "It achieves a BLEU score of 28.4 on English-to-German translation [1, 2]. "
        "Furthermore, Self-RAG introduces adaptive reflection tokens [3-4]."
    )
    claims = claim_extractor.extract_claims(text)

    assert len(claims) >= 3
    # Check claim texts are cleaned of brackets
    for c in claims:
        assert "[" not in c.claim_text
        assert "]" not in c.claim_text

    # First claim should have citation 1
    assert 1 in claims[0].cited_indices
    # Second claim should have citations 1 and 2
    assert 1 in claims[1].cited_indices
    assert 2 in claims[1].cited_indices
    # Third claim should have citations 3 and 4
    assert 3 in claims[2].cited_indices
    assert 4 in claims[2].cited_indices


@pytest.mark.asyncio
async def test_evidence_verifier_supported():
    claim = AtomicClaim(
        claim_id="c_1",
        claim_text="The Transformer relies solely on self-attention mechanisms, dispensing with recurrence.",
        original_sentence="The Transformer relies solely on self-attention mechanisms [1].",
        cited_indices=[1]
    )
    evidence = [
        {
            "passage_text": "We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence entirely.",
            "document_title": "Attention Is All You Need",
            "chunk_id": "chk_attn_1"
        }
    ]

    res = await evidence_verifier.verify_single_claim(claim, evidence)
    assert res.verdict == VerificationVerdict.SUPPORTED
    assert res.confidence >= 0.70
    assert res.citation_valid is True
    assert res.matched_doc_title == "Attention Is All You Need"


@pytest.mark.asyncio
async def test_evidence_verifier_contradicted():
    claim = AtomicClaim(
        claim_id="c_2",
        claim_text="On English-to-German translation, the model achieved a BLEU score of 95.5.",
        original_sentence="On English-to-German translation, the model achieved a BLEU score of 95.5 [1].",
        cited_indices=[1]
    )
    evidence = [
        {
            "passage_text": "On the WMT 2014 English-to-German translation task, the big transformer model achieves a state-of-the-art BLEU score of 28.4.",
            "document_title": "Attention Is All You Need",
            "chunk_id": "chk_attn_2"
        }
    ]

    res = await evidence_verifier.verify_single_claim(claim, evidence)
    assert res.verdict == VerificationVerdict.CONTRADICTED
    assert res.evidence_snippet is not None


@pytest.mark.asyncio
async def test_evidence_verifier_unverifiable():
    claim = AtomicClaim(
        claim_id="c_3",
        claim_text="The model was deployed across twenty decentralized quantum servers in Tokyo.",
        original_sentence="The model was deployed across twenty decentralized quantum servers in Tokyo.",
        cited_indices=[]
    )
    evidence = [
        {
            "passage_text": "On English-to-French translation, our model establishes a new single-model state-of-the-art BLEU score of 41.8.",
            "document_title": "Attention Is All You Need",
            "chunk_id": "chk_attn_3"
        }
    ]

    res = await evidence_verifier.verify_single_claim(claim, evidence)
    assert res.verdict == VerificationVerdict.UNVERIFIABLE


@pytest.mark.asyncio
async def test_hallucination_detector_scoring():
    # 1 supported, 1 contradicted, 1 unverifiable
    answer = (
        "The Transformer uses scaled dot-product attention [1]. "
        "The big transformer model achieves a BLEU score of 88.0 on German translation [1]. "
        "It was trained using the proprietary AdamW-Titanium optimizer."
    )
    evidence = [
        {
            "passage_text": "The Transformer uses scaled dot-product attention. On English-to-German translation, the big transformer model achieves a BLEU score of 28.4.",
            "document_title": "Attention Is All You Need"
        }
    ]

    report = await hallucination_detector.detect_hallucinations(
        answer_text=answer,
        retrieved_contexts=evidence
    )

    assert report.total_claims >= 3
    # Hallucination Rate = (Unsupported + Contradicted) / Total Claims * 100
    expected_hallucination = ((report.unverifiable_count + report.contradicted_count) / report.total_claims) * 100.0
    assert abs(report.hallucination_rate - round(expected_hallucination, 2)) < 0.05
    assert report.contradiction_rate > 0.0
    assert report.claim_support_rate > 0.0


@pytest.mark.asyncio
async def test_human_benchmark_evaluator():
    bench_results = await hallucination_detector.evaluate_against_human_benchmark()
    assert bench_results["total_benchmark_cases"] == 5
    # Accuracy against gold human-labeled benchmark should be high
    assert bench_results["benchmark_accuracy"] >= 80.0
