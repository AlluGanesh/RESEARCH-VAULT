from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from researchvault.database.session import get_db
from researchvault.models.user import User
from researchvault.schemas.research import ResearchRequest, ResearchResponse
from researchvault.api.deps import get_current_user
from researchvault.generation.research_engine import research_engine

router = APIRouter(prefix="/research", tags=["Research Mode"])


@router.post("", response_model=ResearchResponse)
async def execute_research_mode(
    req: ResearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        response = await research_engine.execute_research(
            db=db,
            query=req.query,
            user_id=current_user.id,
            collection_id=req.collection_id,
            document_ids=req.document_ids
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Research synthesis error: {str(e)}")
