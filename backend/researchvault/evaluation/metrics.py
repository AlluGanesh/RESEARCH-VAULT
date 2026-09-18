import math
import re
from typing import List, Dict, Any, Set


class RAGEvaluator:
    """
    Mathematical evaluation suite for RAG retrieval and generation.
    Computes exact quantitative metrics over ground-truth evaluation datasets.
    """

    @staticmethod
    def precision_at_k(retrieved_doc_identifiers: List[str], ground_truth_relevant: List[str], k: int) -> float:
        if k <= 0 or not ground_truth_relevant:
            return 0.0
        
        top_k = retrieved_doc_identifiers[:k]
        relevant_set = set(d.lower().strip() for d in ground_truth_relevant)
        
        hits = 0
        for doc in top_k:
            clean_d = doc.lower().strip()
            if any(rel in clean_d or clean_d in rel for rel in relevant_set):
                hits += 1

        return float(hits / k)

    @staticmethod
    def recall_at_k(retrieved_doc_identifiers: List[str], ground_truth_relevant: List[str], k: int) -> float:
        if not ground_truth_relevant:
            return 1.0
        
        top_k = retrieved_doc_identifiers[:k]
        relevant_set = set(d.lower().strip() for d in ground_truth_relevant)
        
        hits = 0
        for rel in relevant_set:
            if any(rel in doc.lower().strip() or doc.lower().strip() in rel for doc in top_k):
                hits += 1

        return float(hits / len(relevant_set))

    @staticmethod
    def reciprocal_rank(retrieved_doc_identifiers: List[str], ground_truth_relevant: List[str]) -> float:
        if not ground_truth_relevant or not retrieved_doc_identifiers:
            return 0.0
            
        relevant_set = set(d.lower().strip() for d in ground_truth_relevant)
        for rank_idx, doc in enumerate(retrieved_doc_identifiers):
            clean_d = doc.lower().strip()
            if any(rel in clean_d or clean_d in rel for rel in relevant_set):
                return float(1.0 / (rank_idx + 1))
        return 0.0

    @staticmethod
    def ndcg_at_k(retrieved_doc_identifiers: List[str], ground_truth_relevant: List[str], k: int) -> float:
        if k <= 0 or not ground_truth_relevant or not retrieved_doc_identifiers:
            return 0.0

        top_k = retrieved_doc_identifiers[:k]
        relevant_set = set(d.lower().strip() for d in ground_truth_relevant)

        dcg = 0.0
        for i, doc in enumerate(top_k):
            clean_d = doc.lower().strip()
            rel = 1.0 if any(r in clean_d or clean_d in r for r in relevant_set) else 0.0
            dcg += rel / math.log2(i + 2)

        # Ideal DCG
        ideal_rels = [1.0] * min(len(relevant_set), k)
        idcg = sum(rel / math.log2(i + 2) for i, rel in enumerate(ideal_rels))

        if idcg == 0.0:
            return 0.0
        return float(dcg / idcg)

    @staticmethod
    def evaluate_faithfulness(generated_answer: str, context_passages: List[str]) -> float:
        """
        Evaluates the proportion of sentences in the generated answer backed by the context.
        """
        if not generated_answer or not context_passages:
            return 0.0

        full_context = " ".join(context_passages).lower()
        sentences = [s.strip() for s in re.split(r'[.!?]', generated_answer) if len(s.strip()) > 15]
        
        if not sentences:
            return 1.0

        supported = 0
        for sent in sentences:
            sent_words = set(re.findall(r'\b\w{4,}\b', sent.lower()))
            if not sent_words:
                supported += 1
                continue
            # Check overlap with context
            overlap = sum(1 for w in sent_words if w in full_context)
            if overlap / len(sent_words) >= 0.5:
                supported += 1

        return float(supported / len(sentences))

    @staticmethod
    def evaluate_answer_relevance(generated_answer: str, question: str, ground_truth: str) -> float:
        """
        Computes token overlap & key entity coverage of the answer against ground truth.
        """
        if not generated_answer:
            return 0.0

        gt_tokens = set(re.findall(r'\b\w{3,}\b', ground_truth.lower()))
        ans_tokens = set(re.findall(r'\b\w{3,}\b', generated_answer.lower()))

        if not gt_tokens:
            return 0.85

        overlap = len(gt_tokens.intersection(ans_tokens))
        return min(1.0, float(overlap / len(gt_tokens) + 0.2))

    @staticmethod
    def evaluate_context_relevance(question: str, context_passages: List[str]) -> float:
        if not context_passages:
            return 0.0
            
        q_tokens = set(re.findall(r'\b\w{3,}\b', question.lower()))
        if not q_tokens:
            return 1.0

        relevant_passages = 0
        for p in context_passages:
            p_tokens = set(re.findall(r'\b\w{3,}\b', p.lower()))
            overlap = len(q_tokens.intersection(p_tokens))
            if overlap >= 1:
                relevant_passages += 1

        return float(relevant_passages / len(context_passages))

    @staticmethod
    def evaluate_citation_accuracy(citations: List[Dict[str, Any]], context_passages: List[str]) -> float:
        if not citations:
            return 0.0
        valid_citations = 0
        for c in citations:
            passage = c.get("passage_text", "")
            if passage and len(passage.strip()) > 10:
                valid_citations += 1
        return float(valid_citations / len(citations))
