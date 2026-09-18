import pytest
from researchvault.evaluation.metrics import RAGEvaluator


def test_precision_recall_at_k():
    retrieved = [
        "Attention Is All You Need",
        "BERT: Pre-training of Deep Bidirectional Transformers",
        "Retrieval-Augmented Generation for NLP",
        "Self-RAG"
    ]
    ground_truth = [
        "Attention Is All You Need",
        "Retrieval-Augmented Generation for NLP"
    ]

    p_at_2 = RAGEvaluator.precision_at_k(retrieved, ground_truth, k=2)
    assert p_at_2 == 0.5  # 1 relevant in top 2

    p_at_4 = RAGEvaluator.precision_at_k(retrieved, ground_truth, k=4)
    assert p_at_4 == 0.5  # 2 relevant in top 4

    r_at_2 = RAGEvaluator.recall_at_k(retrieved, ground_truth, k=2)
    assert r_at_2 == 0.5  # 1 out of 2 ground truth found

    r_at_4 = RAGEvaluator.recall_at_k(retrieved, ground_truth, k=4)
    assert r_at_4 == 1.0  # 2 out of 2 ground truth found


def test_mrr_and_ndcg():
    retrieved = [
        "Noise Document",
        "Attention Is All You Need",
        "Retrieval-Augmented Generation for NLP"
    ]
    ground_truth = ["Attention Is All You Need"]

    mrr = RAGEvaluator.reciprocal_rank(retrieved, ground_truth)
    assert mrr == 0.5  # First relevant at rank 2 -> 1/2 = 0.5

    ndcg = RAGEvaluator.ndcg_at_k(retrieved, ground_truth, k=3)
    assert 0.0 < ndcg <= 1.0


def test_faithfulness_and_relevance():
    context = [
        "The Transformer uses scaled dot-product attention to prevent gradients from vanishing."
    ]
    grounded_answer = "The Transformer relies on scaled dot-product attention to prevent vanishing gradients [1]."
    
    faith = RAGEvaluator.evaluate_faithfulness(grounded_answer, context)
    assert faith >= 0.8
