import os
import uuid
import aiofiles
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from researchvault.database.session import get_db
from researchvault.core.config import settings
from researchvault.models.user import User
from researchvault.models.document import Document, DocumentStatus
from researchvault.models.chunk import Chunk
from researchvault.schemas.document import DocumentResponse, DocumentDetailResponse, ChunkResponse, DocumentProcessRequest
from researchvault.api.deps import get_current_user
from researchvault.workers.ingestion_worker import ingestion_worker
from researchvault.retrieval.vector_store import vector_store

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    collection_id: Optional[str] = Form(None),
    title: Optional[str] = Form(None),
    author: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Validate extension
    filename = file.filename or "document.txt"
    ext = filename.rsplit(".", 1)[-1].lower()
    if ext not in ["pdf", "docx", "doc", "txt", "md"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{ext}'. Supported: PDF, DOCX, TXT, MD."
        )

    # Save to upload dir
    doc_id = str(uuid.uuid4())
    save_filename = f"{doc_id}_{filename}"
    save_path = os.path.join(settings.UPLOAD_DIR, save_filename)

    file_size = 0
    async with aiofiles.open(save_path, "wb") as out_file:
        while content := await file.read(1024 * 1024):  # 1MB chunks
            file_size += len(content)
            await out_file.write(content)

    doc_title = title or filename.rsplit(".", 1)[0].replace("_", " ").replace("-", " ")
    
    document = Document(
        id=doc_id,
        user_id=current_user.id,
        collection_id=collection_id if collection_id and len(collection_id) > 5 else None,
        title=doc_title,
        original_filename=filename,
        file_path=save_path,
        file_type=ext,
        file_size_bytes=file_size,
        author=author,
        status=DocumentStatus.UPLOADED
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)

    # Trigger background ingestion
    background_tasks.add_task(
        ingestion_worker.process_document_async,
        document_id=doc_id,
        chunk_size=settings.CHUNK_SIZE_TOKENS,
        chunk_overlap=settings.CHUNK_OVERLAP_TOKENS
    )

    return DocumentResponse.model_validate(document)


@router.get("", response_model=List[DocumentResponse])
async def list_documents(
    collection_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Document).where(Document.user_id == current_user.id)
    if collection_id:
        stmt = stmt.where(Document.collection_id == collection_id)
    stmt = stmt.order_by(Document.created_at.desc())
    
    res = await db.execute(stmt)
    docs = res.scalars().all()
    return [DocumentResponse.model_validate(d) for d in docs]


@router.get("/{document_id}", response_model=DocumentDetailResponse)
async def get_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Document).options(selectinload(Document.chunks)).where(
        Document.id == document_id,
        Document.user_id == current_user.id
    )
    res = await db.execute(stmt)
    doc = res.scalar_one_or_none()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    return DocumentDetailResponse.model_validate(doc)


@router.get("/{document_id}/chunks", response_model=List[ChunkResponse])
async def get_document_chunks(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Chunk).join(Document, Chunk.document_id == Document.id).where(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).order_by(Chunk.chunk_index)
    
    res = await db.execute(stmt)
    chunks = res.scalars().all()
    return [ChunkResponse.model_validate(c) for c in chunks]


@router.post("/{document_id}/reprocess", response_model=DocumentResponse)
async def reprocess_document(
    document_id: str,
    background_tasks: BackgroundTasks,
    req: DocumentProcessRequest = DocumentProcessRequest(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Document).where(Document.id == document_id, Document.user_id == current_user.id)
    res = await db.execute(stmt)
    doc = res.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete old Qdrant chunks
    vector_store.delete_by_document_id(doc.id)

    # Delete old DB chunks
    from sqlalchemy import delete
    await db.execute(delete(Chunk).where(Chunk.document_id == doc.id))
    doc.status = DocumentStatus.UPLOADED
    doc.error_message = None
    await db.commit()

    background_tasks.add_task(
        ingestion_worker.process_document_async,
        document_id=doc.id,
        chunk_size=req.chunk_size or settings.CHUNK_SIZE_TOKENS,
        chunk_overlap=req.chunk_overlap or settings.CHUNK_OVERLAP_TOKENS
    )

    return DocumentResponse.model_validate(doc)


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Document).where(Document.id == document_id, Document.user_id == current_user.id)
    res = await db.execute(stmt)
    doc = res.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete file from disk
    if os.path.exists(doc.file_path):
        try:
            os.remove(doc.file_path)
        except Exception:
            pass

    # Delete from Qdrant
    vector_store.delete_by_document_id(doc.id)

    # Delete from DB
    await db.delete(doc)
    await db.commit()
    return {"message": "Document deleted successfully"}
