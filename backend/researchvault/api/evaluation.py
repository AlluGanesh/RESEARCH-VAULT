import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from researchvault.database.session import get_db
from researchvault.models.user import User
from researchvault.models.evaluation import (
    EvaluationDataset, EvaluationTestCase, EvaluationRun, EvaluationResult,
    HybridBenchmarkRun, HallucinationAuditLog
)
from researchvault.schemas.evaluation import (
    DatasetCreate, DatasetResponse, TestCaseCreate, TestCaseResponse,
    RunEvaluationRequest, EvaluationRunResponse, EvaluationResultResponse,
    HallucinationDetectionRequest, HallucinationReportResponse,
    HumanBenchmarkReportResponse, HybridSimulateRequest, HybridSimulateResponse,
    HybridBenchmarkRequest, HybridBenchmarkResponse, OptimizeRatioRequest,
    OptimalRecommendationResponse
)
from researchvault.api.deps import get_current_user
from researchvault.evaluation.runner import evaluation_runner
from researchvault.evaluation.hallucination_detector import hallucination_detector
from researchvault.evaluation.ratio_optimizer import ratio_optimizer
from researchvault.retrieval.hybrid_retriever import HybridRetriever

router = APIRouter(prefix="/evaluation", tags=["Evaluation Framework"])



@router.post("/datasets", response_model=DatasetResponse)
async def create_dataset(
    data_in: DatasetCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    dataset = EvaluationDataset(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        name=data_in.name,
        description=data_in.description
    )
    db.add(dataset)
    await db.commit()
    await db.refresh(dataset)

    # Add initial test cases
    for tc in data_in.test_cases:
        tc_obj = EvaluationTestCase(
            id=str(uuid.uuid4()),
            dataset_id=dataset.id,
            question=tc.question,
            ground_truth_answer=tc.ground_truth_answer,
            relevant_doc_titles=tc.relevant_doc_titles,
            relevant_passages=tc.relevant_passages
        )
        db.add(tc_obj)

    await db.commit()

    # Reload
    stmt = select(EvaluationDataset).options(selectinload(EvaluationDataset.test_cases)).where(EvaluationDataset.id == dataset.id)
    res = await db.execute(stmt)
    full_ds = res.scalar_one()

    resp = DatasetResponse.model_validate(full_ds)
    resp.test_case_count = len(full_ds.test_cases)
    return resp


@router.get("/datasets", response_model=List[DatasetResponse])
async def list_datasets(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(EvaluationDataset).options(selectinload(EvaluationDataset.test_cases)).where(
        EvaluationDataset.user_id == current_user.id
    ).order_by(EvaluationDataset.created_at.desc())
    
    res = await db.execute(stmt)
    datasets = res.scalars().all()

    output = []
    for ds in datasets:
        resp = DatasetResponse.model_validate(ds)
        resp.test_case_count = len(ds.test_cases)
        output.append(resp)

    return output


@router.post("/datasets/{dataset_id}/test-cases", response_model=TestCaseResponse)
async def add_test_case(
    dataset_id: str,
    tc_in: TestCaseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(EvaluationDataset).where(EvaluationDataset.id == dataset_id, EvaluationDataset.user_id == current_user.id)
    res = await db.execute(stmt)
    if not res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Dataset not found")

    tc_obj = EvaluationTestCase(
        id=str(uuid.uuid4()),
        dataset_id=dataset_id,
        question=tc_in.question,
        ground_truth_answer=tc_in.ground_truth_answer,
        relevant_doc_titles=tc_in.relevant_doc_titles,
        relevant_passages=tc_in.relevant_passages
    )
    db.add(tc_obj)
    await db.commit()
    await db.refresh(tc_obj)
    return TestCaseResponse.model_validate(tc_obj)


@router.post("/run", response_model=EvaluationRunResponse)
async def run_evaluation(
    req: RunEvaluationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        run_record = await evaluation_runner.run_evaluation(
            db=db,
            dataset_id=req.dataset_id,
            user_id=current_user.id,
            run_name=req.run_name,
            llm_provider=req.llm_provider,
            top_k=req.top_k or 5
        )

        # Reload with results
        stmt = select(EvaluationRun).options(selectinload(EvaluationRun.results)).where(EvaluationRun.id == run_record.id)
        res = await db.execute(stmt)
        full_run = res.scalar_one()
        return EvaluationRunResponse.model_validate(full_run)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation execution error: {str(e)}")


@router.get("/runs", response_model=List[EvaluationRunResponse])
async def list_evaluation_runs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(EvaluationRun).options(selectinload(EvaluationRun.results)).where(
        EvaluationRun.user_id == current_user.id
    ).order_by(EvaluationRun.created_at.desc())
    
    res = await db.execute(stmt)
    runs = res.scalars().all()
    return [EvaluationRunResponse.model_validate(r) for r in runs]


@router.get("/runs/{run_id}", response_model=EvaluationRunResponse)
async def get_evaluation_run(
    run_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(EvaluationRun).options(selectinload(EvaluationRun.results)).where(
        EvaluationRun.id == run_id,
        EvaluationRun.user_id == current_user.id
    )
    res = await db.execute(stmt)
    run = res.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Evaluation run not found")
    return EvaluationRunResponse.model_validate(run)


# ============================================================================
# 1. Hallucination Detection & Scoring Endpoints
# ============================================================================

@router.post("/hallucination", response_model=HallucinationReportResponse)
async def detect_hallucination(
    req: HallucinationDetectionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Evaluates generated AI answer at individual atomic claim level.
    Verifies each claim against retrieved evidence passages and computes:
    Hallucination Rate = (Unsupported + Contradicted Claims) / Total Claims * 100
    """
    passages = req.context_passages or []

    # If no passages explicitly provided but query exists, retrieve from knowledge base
    if not passages and req.query:
        retriever = HybridRetriever()
        candidates = await retriever.retrieve(
            db=db,
            queries=[req.query],
            top_k=8,
            user_id=current_user.id
        )
        passages = candidates

    report = await hallucination_detector.detect_hallucinations(
        answer_text=req.answer_text,
        retrieved_contexts=passages,
        llm_provider=req.llm_provider
    )

    report_dict = report.to_dict()

    # Persist audit record
    try:
        audit_log = HallucinationAuditLog(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            query=req.query,
            answer_text=req.answer_text,
            total_claims=report.total_claims,
            supported_count=report.supported_count,
            contradicted_count=report.contradicted_count,
            unverifiable_count=report.unverifiable_count,
            hallucination_rate=report.hallucination_rate,
            claim_support_rate=report.claim_support_rate,
            contradiction_rate=report.contradiction_rate,
            unverifiable_rate=report.unverifiable_rate,
            citation_accuracy=report.citation_accuracy,
            verified_claims=report_dict["verified_claims"],
            execution_time_ms=report.execution_time_ms
        )
        db.add(audit_log)
        await db.commit()
    except Exception as e:
        # Don't fail the request if logging encounters a minor issue
        pass

    return HallucinationReportResponse(**report_dict)


@router.post("/hallucination/human-benchmark", response_model=HumanBenchmarkReportResponse)
async def evaluate_against_human_benchmark(
    current_user: User = Depends(get_current_user)
):
    """
    Evaluates the hallucination detection engine against human-labeled ground truth benchmark cases.
    """
    results = await hallucination_detector.evaluate_against_human_benchmark()
    return HumanBenchmarkReportResponse(**results)


@router.get("/hallucination/history")
async def get_hallucination_history(
    limit: int = 15,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(HallucinationAuditLog).where(
        HallucinationAuditLog.user_id == current_user.id
    ).order_by(HallucinationAuditLog.created_at.desc()).limit(limit)
    res = await db.execute(stmt)
    records = res.scalars().all()
    return [
        {
            "id": r.id,
            "query": r.query,
            "answer_preview": (r.answer_text[:100] + "...") if r.answer_text else "",
            "total_claims": r.total_claims,
            "supported_count": r.supported_count,
            "contradicted_count": r.contradicted_count,
            "unverifiable_count": r.unverifiable_count,
            "hallucination_rate": r.hallucination_rate,
            "claim_support_rate": r.claim_support_rate,
            "created_at": r.created_at.isoformat() if r.created_at else None
        }
        for r in records
    ]


# ============================================================================
# 2. Hybrid Retrieval Ratio Simulator, Benchmark & Optimizer Endpoints
# ============================================================================

@router.post("/hybrid-simulate", response_model=HybridSimulateResponse)
async def simulate_hybrid_retrieval(
    req: HybridSimulateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Interactive Hybrid Retrieval Simulator:
    Applies weighted RRF S(d) = w_d / (k + r_d(d)) + w_s / (k + r_s(d))
    Returns live candidates with retrieval source breakdown (dense_only, sparse_only, hybrid_overlap).
    """
    retriever = HybridRetriever()
    import time
    start_t = time.time()

    candidates = await retriever.retrieve(
        db=db,
        queries=[req.query],
        top_k=req.k,
        user_id=current_user.id,
        dense_weight=req.dense_weight,
        sparse_weight=req.sparse_weight
    )
    latency = (time.time() - start_t) * 1000.0

    overlap_count = sum(1 for c in candidates if c.get("retrieval_source") == "hybrid_overlap")
    dense_only_count = sum(1 for c in candidates if c.get("retrieval_source") == "dense_only")
    sparse_only_count = sum(1 for c in candidates if c.get("retrieval_source") == "sparse_only")

    total_k = len(candidates)
    overlap_ratio = (overlap_count / total_k) if total_k > 0 else 0.0

    formatted_candidates = []
    for c in candidates:
        preview = (c.get("passage_text") or c.get("content", ""))
        formatted_candidates.append({
            "chunk_id": c.get("chunk_id"),
            "document_title": c.get("document_title"),
            "retrieval_source": c.get("retrieval_source", "hybrid_overlap"),
            "rrf_score": float(c.get("rrf_score", 0.0)),
            "vector_score": float(c.get("vector_score")) if c.get("vector_score") is not None else None,
            "lexical_score": float(c.get("lexical_score")) if c.get("lexical_score") is not None else None,
            "passage_preview": (preview[:140] + "...") if len(preview) > 140 else preview
        })

    return HybridSimulateResponse(
        query=req.query,
        dense_weight=req.dense_weight,
        sparse_weight=req.sparse_weight,
        k=req.k,
        total_retrieved=total_k,
        overlap_count=overlap_count,
        overlap_ratio=round(overlap_ratio, 3),
        dense_only_count=dense_only_count,
        sparse_only_count=sparse_only_count,
        latency_ms=round(latency, 2),
        candidates=formatted_candidates
    )


@router.post("/hybrid-benchmark", response_model=HybridBenchmarkResponse)
async def run_hybrid_benchmark(
    req: HybridBenchmarkRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Runs multi-ratio benchmark sweep across 0:100 to 100:0.
    Measures NDCG@K, Recall@K, Precision@K, Overlap@K, and Hallucination correlation.
    """
    try:
        benchmark_data = await ratio_optimizer.run_hybrid_benchmark(
            db=db,
            dataset_id=req.dataset_id,
            user_id=current_user.id,
            k=req.k or 10,
            ratios=req.ratios
        )

        # Persist benchmark run record
        opt = benchmark_data["optimal_recommendation"]
        b_record = HybridBenchmarkRun(
            id=str(uuid.uuid4()),
            dataset_id=req.dataset_id,
            user_id=current_user.id,
            dataset_name=benchmark_data["dataset_name"],
            k=req.k or 10,
            total_test_cases=benchmark_data["total_test_cases"],
            benchmark_curves=benchmark_data["benchmark_curves"],
            optimal_dense_weight=opt["dense_weight"],
            optimal_sparse_weight=opt["sparse_weight"],
            peak_ndcg=opt["peak_ndcg"],
            peak_recall=opt["peak_recall"],
            composite_score=opt["composite_score"],
            estimated_hallucination_rate=opt["estimated_hallucination_rate"],
            rationale=opt["rationale"],
            execution_time_ms=benchmark_data["execution_time_ms"]
        )
        db.add(b_record)
        await db.commit()

        return HybridBenchmarkResponse(**benchmark_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hybrid benchmark failed: {str(e)}")


@router.post("/optimize-ratio", response_model=OptimalRecommendationResponse)
async def optimize_ratio(
    req: OptimizeRatioRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Optimizes the fusion ratio automatically based on benchmark dataset metrics.
    """
    try:
        benchmark_data = await ratio_optimizer.run_hybrid_benchmark(
            db=db,
            dataset_id=req.dataset_id,
            user_id=current_user.id,
            k=req.k or 10
        )
        return OptimalRecommendationResponse(**benchmark_data["optimal_recommendation"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ratio optimization failed: {str(e)}")


@router.get("/benchmark-results")
async def get_benchmark_results(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns historical hybrid benchmark runs and ratio evaluations.
    """
    stmt = select(HybridBenchmarkRun).where(
        HybridBenchmarkRun.user_id == current_user.id
    ).order_by(HybridBenchmarkRun.created_at.desc()).limit(limit)
    res = await db.execute(stmt)
    records = res.scalars().all()
    return [
        {
            "id": r.id,
            "dataset_id": r.dataset_id,
            "dataset_name": r.dataset_name,
            "k": r.k,
            "total_test_cases": r.total_test_cases,
            "optimal_dense_weight": r.optimal_dense_weight,
            "optimal_sparse_weight": r.optimal_sparse_weight,
            "peak_ndcg": r.peak_ndcg,
            "peak_recall": r.peak_recall,
            "composite_score": r.composite_score,
            "estimated_hallucination_rate": r.estimated_hallucination_rate,
            "rationale": r.rationale,
            "benchmark_curves": r.benchmark_curves,
            "execution_time_ms": r.execution_time_ms,
            "created_at": r.created_at.isoformat() if r.created_at else None
        }
        for r in records
    ]

