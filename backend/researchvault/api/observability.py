from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from researchvault.database.session import get_db
from researchvault.models.user import User
from researchvault.models.observability import QueryTrace
from researchvault.schemas.observability import QueryTraceResponse, ObservabilityStatsResponse
from researchvault.api.deps import get_current_user
from researchvault.services.observability_service import ObservabilityService

router = APIRouter(prefix="/observability", tags=["Observability & Analytics"])


@router.get("/stats", response_model=ObservabilityStatsResponse)
async def get_system_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await ObservabilityService.get_stats(db=db, user_id=current_user.id)


@router.get("/traces", response_model=List[QueryTraceResponse])
async def list_query_traces(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(QueryTrace).where(QueryTrace.user_id == current_user.id).order_by(QueryTrace.created_at.desc()).limit(limit)
    res = await db.execute(stmt)
    traces = res.scalars().all()
    return [QueryTraceResponse.model_validate(t) for t in traces]


@router.get("/traces/{trace_id}", response_model=QueryTraceResponse)
async def get_query_trace(
    trace_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(QueryTrace).where(QueryTrace.id == trace_id, QueryTrace.user_id == current_user.id)
    res = await db.execute(stmt)
    trace = res.scalar_one_or_none()
    if not trace:
        raise HTTPException(status_code=404, detail="Trace not found")
    return QueryTraceResponse.model_validate(trace)
