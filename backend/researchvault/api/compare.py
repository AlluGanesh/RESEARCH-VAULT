from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from researchvault.database.session import get_db
from researchvault.models.user import User
from researchvault.schemas.compare import CompareRequest, CompareResponse
from researchvault.api.deps import get_current_user
from researchvault.generation.comparison_engine import comparison_engine

router = APIRouter(prefix="/compare", tags=["Document Comparison"])


@router.post("", response_model=CompareResponse)
async def compare_documents(
    req: CompareRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not req.document_ids or len(req.document_ids) < 1:
        raise HTTPException(status_code=400, detail="Please select at least 1 document to compare.")
        
    try:
        response = await comparison_engine.compare_documents(
            db=db,
            document_ids=req.document_ids,
            question=req.question
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison error: {str(e)}")
