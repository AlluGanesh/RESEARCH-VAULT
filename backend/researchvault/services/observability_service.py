import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from researchvault.models.observability import QueryTrace
from researchvault.models.document import Document
from researchvault.models.chunk import Chunk
from researchvault.schemas.observability import ObservabilityStatsResponse, QueryTraceResponse


class ObservabilityService:
    @staticmethod
    async def record_trace(
        db: AsyncSession,
        user_id: str,
        raw_query: str,
        rewritten_query: Optional[str] = None,
        expansion_queries: Optional[List[str]] = None,
        extracted_keywords: Optional[List[str]] = None,
        applied_filters: Optional[Dict[str, Any]] = None,
        vector_candidates_count: int = 0,
        lexical_candidates_count: int = 0,
        rrf_candidates: Optional[List[Dict[str, Any]]] = None,
        reranked_candidates: Optional[List[Dict[str, Any]]] = None,
        compressed_context: Optional[str] = None,
        llm_prompt: Optional[str] = None,
        llm_response: Optional[str] = None,
        citations_count: int = 0,
        query_transform_ms: float = 0.0,
        retrieval_ms: float = 0.0,
        rerank_ms: float = 0.0,
        compression_ms: float = 0.0,
        generation_ms: float = 0.0,
        total_latency_ms: float = 0.0,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        status: str = "SUCCESS",
        error_message: Optional[str] = None,
        conversation_id: Optional[str] = None
    ) -> QueryTrace:
        trace = QueryTrace(
            id=str(uuid.uuid4()),
            user_id=user_id,
            conversation_id=conversation_id,
            raw_query=raw_query,
            rewritten_query=rewritten_query,
            expansion_queries=expansion_queries or [],
            extracted_keywords=extracted_keywords or [],
            applied_filters=applied_filters or {},
            vector_candidates_count=vector_candidates_count,
            lexical_candidates_count=lexical_candidates_count,
            rrf_candidates=rrf_candidates or [],
            reranked_candidates=reranked_candidates or [],
            compressed_context=compressed_context,
            llm_prompt=llm_prompt,
            llm_response=llm_response,
            citations_count=citations_count,
            query_transform_ms=query_transform_ms,
            retrieval_ms=retrieval_ms,
            rerank_ms=rerank_ms,
            compression_ms=compression_ms,
            generation_ms=generation_ms,
            total_latency_ms=total_latency_ms,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            status=status,
            error_message=error_message,
            created_at=datetime.now(timezone.utc)
        )
        db.add(trace)
        await db.commit()
        return trace

    @staticmethod
    async def get_stats(db: AsyncSession, user_id: str) -> ObservabilityStatsResponse:
        # Document count
        doc_count_res = await db.execute(select(func.count(Document.id)).where(Document.user_id == user_id))
        doc_count = doc_count_res.scalar() or 0

        # Chunk count
        chunk_count_res = await db.execute(
            select(func.count(Chunk.id)).join(Document, Chunk.document_id == Document.id).where(Document.user_id == user_id)
        )
        chunk_count = chunk_count_res.scalar() or 0

        # Trace stats
        trace_count_res = await db.execute(select(func.count(QueryTrace.id)).where(QueryTrace.user_id == user_id))
        trace_count = trace_count_res.scalar() or 0

        avg_retrieval_res = await db.execute(select(func.avg(QueryTrace.retrieval_ms)).where(QueryTrace.user_id == user_id))
        avg_retrieval = float(avg_retrieval_res.scalar() or 0.0)

        avg_gen_res = await db.execute(select(func.avg(QueryTrace.generation_ms)).where(QueryTrace.user_id == user_id))
        avg_gen = float(avg_gen_res.scalar() or 0.0)

        avg_total_res = await db.execute(select(func.avg(QueryTrace.total_latency_ms)).where(QueryTrace.user_id == user_id))
        avg_total = float(avg_total_res.scalar() or 0.0)

        tokens_res = await db.execute(select(func.sum(QueryTrace.total_tokens)).where(QueryTrace.user_id == user_id))
        total_tokens = int(tokens_res.scalar() or 0)

        failed_res = await db.execute(
            select(func.count(QueryTrace.id)).where(QueryTrace.user_id == user_id, QueryTrace.status == "FAILED")
        )
        failed_count = failed_res.scalar() or 0

        # Latest traces
        latest_res = await db.execute(
            select(QueryTrace).where(QueryTrace.user_id == user_id).order_by(QueryTrace.created_at.desc()).limit(15)
        )
        latest_traces = latest_res.scalars().all()

        return ObservabilityStatsResponse(
            total_documents=doc_count,
            total_chunks=chunk_count,
            total_embeddings=chunk_count,
            total_queries=trace_count,
            avg_retrieval_latency_ms=avg_retrieval,
            avg_generation_latency_ms=avg_gen,
            avg_total_latency_ms=avg_total,
            total_tokens_consumed=total_tokens,
            failed_queries_count=failed_count,
            latest_traces=[QueryTraceResponse.model_validate(t) for t in latest_traces]
        )
