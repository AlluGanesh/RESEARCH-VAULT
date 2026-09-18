import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from researchvault.database.session import get_db
from researchvault.models.user import User
from researchvault.models.evaluation import EvaluationDataset, EvaluationTestCase, EvaluationRun, EvaluationResult
from researchvault.schemas.evaluation import (
    DatasetCreate, DatasetResponse, TestCaseCreate, TestCaseResponse,
    RunEvaluationRequest, EvaluationRunResponse, EvaluationResultResponse
)
from researchvault.api.deps import get_current_user
from researchvault.evaluation.runner import evaluation_runner

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
