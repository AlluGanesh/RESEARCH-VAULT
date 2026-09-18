from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from researchvault.database.session import get_db
from researchvault.models.user import User
from researchvault.models.collection import Collection
from researchvault.models.document import Document
from researchvault.schemas.collection import CollectionCreate, CollectionUpdate, CollectionResponse
from researchvault.api.deps import get_current_user

router = APIRouter(prefix="/collections", tags=["Collections"])


@router.post("", response_model=CollectionResponse)
async def create_collection(
    col_in: CollectionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    col = Collection(
        user_id=current_user.id,
        name=col_in.name,
        description=col_in.description,
        color=col_in.color or "#6366f1"
    )
    db.add(col)
    await db.commit()
    await db.refresh(col)
    
    resp = CollectionResponse.model_validate(col)
    resp.document_count = 0
    return resp


@router.get("", response_model=List[CollectionResponse])
async def list_collections(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Collection).where(Collection.user_id == current_user.id).order_by(Collection.created_at.desc())
    res = await db.execute(stmt)
    collections = res.scalars().all()

    resp_list = []
    for c in collections:
        # Count documents
        cnt_res = await db.execute(select(func.count(Document.id)).where(Document.collection_id == c.id))
        doc_cnt = cnt_res.scalar() or 0
        
        c_resp = CollectionResponse.model_validate(c)
        c_resp.document_count = doc_cnt
        resp_list.append(c_resp)

    return resp_list


@router.get("/{collection_id}", response_model=CollectionResponse)
async def get_collection(
    collection_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Collection).where(Collection.id == collection_id, Collection.user_id == current_user.id)
    res = await db.execute(stmt)
    col = res.scalar_one_or_none()
    if not col:
        raise HTTPException(status_code=404, detail="Collection not found")

    cnt_res = await db.execute(select(func.count(Document.id)).where(Document.collection_id == col.id))
    doc_cnt = cnt_res.scalar() or 0

    c_resp = CollectionResponse.model_validate(col)
    c_resp.document_count = doc_cnt
    return c_resp


@router.delete("/{collection_id}")
async def delete_collection(
    collection_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Collection).where(Collection.id == collection_id, Collection.user_id == current_user.id)
    res = await db.execute(stmt)
    col = res.scalar_one_or_none()
    if not col:
        raise HTTPException(status_code=404, detail="Collection not found")

    await db.delete(col)
    await db.commit()
    return {"message": "Collection deleted"}
