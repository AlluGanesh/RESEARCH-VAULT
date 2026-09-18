import time
import uuid
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from researchvault.models.evaluation import EvaluationDataset, EvaluationTestCase, EvaluationRun, EvaluationResult
from researchvault.retrieval.hybrid_retriever import HybridRetriever
from researchvault.retrieval.reranker import reranker_service
from researchvault.retrieval.context_compressor import context_compressor
from researchvault.generation.citation_engine import citation_engine
from researchvault.evaluation.metrics import RAGEvaluator
from researchvault.core.config import settings

logger = logging.getLogger(__name__)


class EvaluationRunner:
    def __init__(self):
        self.retriever = HybridRetriever()

    async def run_evaluation(
        self,
        db: AsyncSession,
        dataset_id: str,
        user_id: str,
        run_name: Optional[str] = None,
        llm_provider: Optional[str] = None,
        top_k: int = 5
    ) -> EvaluationRun:
        # Load dataset
        stmt = select(EvaluationDataset).options(selectinload(EvaluationDataset.test_cases)).where(EvaluationDataset.id == dataset_id)
        res = await db.execute(stmt)
        dataset = res.scalar_one_or_none()
        
        if not dataset or not dataset.test_cases:
            raise ValueError("Dataset not found or contains no test cases.")

        run_id = str(uuid.uuid4())
        name = run_name or f"Evaluation Run - {dataset.name} ({time.strftime('%Y-%m-%d %H:%M')})"
        
        eval_run = EvaluationRun(
            id=run_id,
            dataset_id=dataset.id,
            user_id=user_id,
            run_name=name,
            llm_provider=llm_provider or settings.DEFAULT_LLM_PROVIDER,
            embedding_provider=settings.EMBEDDING_PROVIDER,
            reranker_used=settings.RERANKER_TYPE,
            total_test_cases=len(dataset.test_cases),
            status="RUNNING"
        )
        db.add(eval_run)
        await db.commit()

        results_list: List[EvaluationResult] = []
        p_list, r_list, mrr_list, ndcg_list, faith_list, ans_rel_list, ctx_rel_list, cite_acc_list = [], [], [], [], [], [], [], []

        for tc in dataset.test_cases:
            tc_start = time.time()
            q = tc.question
            expected_docs = tc.relevant_doc_titles or []
            expected_passages = tc.relevant_passages or []

            # 1. Retrieve
            candidates = await self.retriever.retrieve(
                db=db,
                queries=[q],
                top_k=20,
                user_id=user_id
            )

            # 2. Rerank
            reranked = reranker_service.rerank(query=q, candidates=candidates, top_k=top_k)
            retrieved_doc_titles = [c.get("document_title", "") for c in reranked]

            # 3. Context compression
            compressed_ctx, enriched = context_compressor.compress_chunks(q, reranked)
            context_passages = [c.get("passage_text", "") for c in enriched]

            # 4. Generation & Citations
            answer_text, citations = await citation_engine.generate_grounded_answer(
                query=q,
                compressed_context=compressed_ctx,
                retrieved_chunks=enriched,
                llm_provider=llm_provider
            )

            # 5. Calculate Metrics
            p_at_k = RAGEvaluator.precision_at_k(retrieved_doc_titles, expected_docs, k=top_k)
            r_at_k = RAGEvaluator.recall_at_k(retrieved_doc_titles, expected_docs, k=top_k)
            rr = RAGEvaluator.reciprocal_rank(retrieved_doc_titles, expected_docs)
            ndcg = RAGEvaluator.ndcg_at_k(retrieved_doc_titles, expected_docs, k=top_k)
            faithfulness = RAGEvaluator.evaluate_faithfulness(answer_text, context_passages)
            ans_rel = RAGEvaluator.evaluate_answer_relevance(answer_text, q, tc.ground_truth_answer)
            ctx_rel = RAGEvaluator.evaluate_context_relevance(q, context_passages)
            cite_acc = RAGEvaluator.evaluate_citation_accuracy(citations, context_passages)

            tc_latency = (time.time() - tc_start) * 1000.0

            # Store lists for means
            p_list.append(p_at_k)
            r_list.append(r_at_k)
            mrr_list.append(rr)
            ndcg_list.append(ndcg)
            faith_list.append(faithfulness)
            ans_rel_list.append(ans_rel)
            ctx_rel_list.append(ctx_rel)
            cite_acc_list.append(cite_acc)

            eval_result = EvaluationResult(
                id=str(uuid.uuid4()),
                run_id=run_id,
                test_case_id=tc.id,
                question=q,
                ground_truth=tc.ground_truth_answer,
                generated_answer=answer_text,
                retrieved_contexts=context_passages,
                citations=citations,
                precision_at_k=p_at_k,
                recall_at_k=r_at_k,
                reciprocal_rank=rr,
                ndcg_score=ndcg,
                faithfulness_score=faithfulness,
                answer_relevance_score=ans_rel,
                context_relevance_score=ctx_rel,
                citation_accuracy=cite_acc,
                latency_ms=tc_latency
            )
            db.add(eval_result)
            results_list.append(eval_result)

        # Calculate mean metrics
        eval_run.mean_precision_at_k = sum(p_list) / len(p_list) if p_list else 0.0
        eval_run.mean_recall_at_k = sum(r_list) / len(r_list) if r_list else 0.0
        eval_run.mean_mrr = sum(mrr_list) / len(mrr_list) if mrr_list else 0.0
        eval_run.mean_ndcg = sum(ndcg_list) / len(ndcg_list) if ndcg_list else 0.0
        eval_run.mean_faithfulness = sum(faith_list) / len(faith_list) if faith_list else 0.0
        eval_run.mean_answer_relevance = sum(ans_rel_list) / len(ans_rel_list) if ans_rel_list else 0.0
        eval_run.mean_context_relevance = sum(ctx_rel_list) / len(ctx_rel_list) if ctx_rel_list else 0.0
        eval_run.mean_citation_accuracy = sum(cite_acc_list) / len(cite_acc_list) if cite_acc_list else 0.0
        eval_run.status = "COMPLETED"

        await db.commit()
        await db.refresh(eval_run)
        return eval_run


# Global instance
evaluation_runner = EvaluationRunner()
