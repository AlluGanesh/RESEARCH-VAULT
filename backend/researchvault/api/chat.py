import time
import uuid
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from researchvault.database.session import get_db
from researchvault.models.user import User
from researchvault.models.chat import Conversation, Message, Citation, MessageRole
from researchvault.schemas.chat import ChatRequest, MessageResponse, ConversationResponse, CitationResponse
from researchvault.api.deps import get_current_user
from researchvault.retrieval.query_transformer import QueryTransformer
from researchvault.retrieval.hybrid_retriever import HybridRetriever
from researchvault.retrieval.reranker import reranker_service
from researchvault.retrieval.context_compressor import context_compressor
from researchvault.generation.llm_service import llm_service
from researchvault.generation.citation_engine import citation_engine
from researchvault.services.observability_service import ObservabilityService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("", response_model=MessageResponse)
async def chat_interaction(
    req: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    total_start = time.time()
    
    # 1. Resolve or create Conversation
    conv = None
    conversation_history = []
    if req.conversation_id:
        c_stmt = select(Conversation).options(selectinload(Conversation.messages)).where(
            Conversation.id == req.conversation_id,
            Conversation.user_id == current_user.id
        )
        c_res = await db.execute(c_stmt)
        conv = c_res.scalar_one_or_none()
        if conv and conv.messages:
            conversation_history = [{"role": m.role.value, "content": m.content} for m in conv.messages[-6:]]

    if not conv:
        conv_title = req.message[:50] + ("..." if len(req.message) > 50 else "")
        conv = Conversation(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            collection_id=req.collection_id,
            title=conv_title,
            mode=req.mode or "rag"
        )
        db.add(conv)
        await db.commit()
        await db.refresh(conv)

    # Record User Message
    user_msg = Message(
        id=str(uuid.uuid4()),
        conversation_id=conv.id,
        role=MessageRole.USER,
        content=req.message
    )
    db.add(user_msg)
    await db.commit()

    # Stage 1: Query Transformation
    t0 = time.time()
    transformer = QueryTransformer(llm_service=llm_service)
    transformed = await transformer.transform_query(
        query=req.message,
        conversation_history=conversation_history
    )
    t_transform_ms = (time.time() - t0) * 1000.0

    # Stage 2: Hybrid Retrieval
    t0 = time.time()
    retriever = HybridRetriever()
    search_queries = transformed.expansion_queries or [transformed.rewritten_query]
    
    hybrid_candidates = await retriever.retrieve(
        db=db,
        queries=search_queries,
        top_k=25,
        user_id=current_user.id,
        collection_id=req.collection_id or conv.collection_id,
        document_ids=req.document_ids
    )
    t_retrieval_ms = (time.time() - t0) * 1000.0

    # Stage 3: Reranking
    t0 = time.time()
    reranked_candidates = reranker_service.rerank(
        query=transformed.rewritten_query,
        candidates=hybrid_candidates,
        top_k=req.top_k or 7
    )
    t_rerank_ms = (time.time() - t0) * 1000.0

    # Stage 4: Context Compression
    t0 = time.time()
    compressed_ctx, enriched_chunks = context_compressor.compress_chunks(
        query=transformed.rewritten_query,
        chunks=reranked_candidates
    )
    t_compress_ms = (time.time() - t0) * 1000.0

    # Stage 5: Generation & Citations
    t0 = time.time()
    answer_text, citations_data = await citation_engine.generate_grounded_answer(
        query=transformed.rewritten_query,
        compressed_context=compressed_ctx,
        retrieved_chunks=enriched_chunks,
        llm_provider=req.llm_provider
    )
    t_gen_ms = (time.time() - t0) * 1000.0
    total_latency_ms = (time.time() - total_start) * 1000.0

    # Save Assistant Message
    asst_msg_id = str(uuid.uuid4())
    asst_msg = Message(
        id=asst_msg_id,
        conversation_id=conv.id,
        role=MessageRole.ASSISTANT,
        content=answer_text,
        rewritten_query=transformed.rewritten_query,
        expansion_queries=transformed.expansion_queries,
        latency_ms=total_latency_ms,
        tokens_used=len(answer_text.split()) * 2
    )
    db.add(asst_msg)

    # Save Citations
    saved_citations = []
    for c in citations_data:
        cite_obj = Citation(
            id=str(uuid.uuid4()),
            message_id=asst_msg_id,
            document_id=c.get("document_id") or "doc_unknown",
            chunk_id=c.get("chunk_id"),
            citation_number=c.get("citation_number", 1),
            document_title=c.get("document_title", "Unknown"),
            page_number=c.get("page_number", 1),
            section=c.get("section", "General"),
            passage_text=c.get("passage_text", ""),
            similarity_score=float(c.get("similarity_score", 0.0)),
            rerank_score=float(c.get("rerank_score", 0.0))
        )
        db.add(cite_obj)
        saved_citations.append(cite_obj)

    await db.commit()

    # Stage 6: Record Observability Trace
    try:
        await ObservabilityService.record_trace(
            db=db,
            user_id=current_user.id,
            conversation_id=conv.id,
            raw_query=req.message,
            rewritten_query=transformed.rewritten_query,
            expansion_queries=transformed.expansion_queries,
            extracted_keywords=transformed.extracted_keywords,
            applied_filters={"collection_id": req.collection_id, "document_ids": req.document_ids},
            vector_candidates_count=len(hybrid_candidates),
            lexical_candidates_count=len(hybrid_candidates),
            rrf_candidates=hybrid_candidates[:5],
            reranked_candidates=reranked_candidates[:5],
            compressed_context=compressed_ctx,
            llm_prompt=transformed.rewritten_query,
            llm_response=answer_text,
            citations_count=len(saved_citations),
            query_transform_ms=t_transform_ms,
            retrieval_ms=t_retrieval_ms,
            rerank_ms=t_rerank_ms,
            compression_ms=t_compress_ms,
            generation_ms=t_gen_ms,
            total_latency_ms=total_latency_ms,
            prompt_tokens=len(compressed_ctx.split()) * 2,
            completion_tokens=len(answer_text.split()) * 2
        )
    except Exception as e:
        logger.warning(f"Failed to record trace: {e}")

    # Build response
    resp = MessageResponse(
        id=asst_msg.id,
        conversation_id=conv.id,
        role=asst_msg.role,
        content=asst_msg.content,
        rewritten_query=asst_msg.rewritten_query,
        expansion_queries=asst_msg.expansion_queries or [],
        latency_ms=asst_msg.latency_ms,
        tokens_used=asst_msg.tokens_used,
        structured_data={},
        citations=[CitationResponse.model_validate(c) for c in saved_citations],
        created_at=asst_msg.created_at
    )
    return resp


@router.get("/conversations", response_model=List[ConversationResponse])
async def list_conversations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Conversation).options(
        selectinload(Conversation.messages).selectinload(Message.citations)
    ).where(Conversation.user_id == current_user.id).order_by(Conversation.updated_at.desc())
    
    res = await db.execute(stmt)
    convs = res.scalars().all()
    return [ConversationResponse.model_validate(c) for c in convs]


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Conversation).options(
        selectinload(Conversation.messages).selectinload(Message.citations)
    ).where(Conversation.id == conversation_id, Conversation.user_id == current_user.id)
    
    res = await db.execute(stmt)
    conv = res.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return ConversationResponse.model_validate(conv)


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Conversation).where(Conversation.id == conversation_id, Conversation.user_id == current_user.id)
    res = await db.execute(stmt)
    conv = res.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    await db.delete(conv)
    await db.commit()
    return {"message": "Conversation deleted"}
