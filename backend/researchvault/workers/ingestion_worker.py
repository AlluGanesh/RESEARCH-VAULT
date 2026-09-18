import os
import uuid
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from researchvault.models.document import Document, DocumentStatus
from researchvault.models.chunk import Chunk
from researchvault.ingestion.extractors.pdf_extractor import PDFExtractor
from researchvault.ingestion.extractors.docx_extractor import DocxExtractor
from researchvault.ingestion.extractors.text_extractor import TextExtractor
from researchvault.ingestion.chunker import StructureAwareChunker
from researchvault.embeddings.embedding_service import embedding_service
from researchvault.retrieval.vector_store import vector_store
from researchvault.database.session import AsyncSessionLocal

logger = logging.getLogger(__name__)


class IngestionWorker:
    @staticmethod
    async def process_document_async(
        document_id: str,
        chunk_size: int = 500,
        chunk_overlap: int = 100
    ):
        """
        Background worker pipeline for document processing and vector indexing.
        """
        async with AsyncSessionLocal() as db:
            try:
                # 1. Fetch document
                stmt = select(Document).where(Document.id == document_id)
                res = await db.execute(stmt)
                doc = res.scalar_one_or_none()
                if not doc:
                    logger.error(f"Document {document_id} not found for ingestion.")
                    return

                # Status: EXTRACTING
                doc.status = DocumentStatus.EXTRACTING
                await db.commit()

                # Text & Metadata Extraction
                ft = doc.file_type.lower()
                fp = doc.file_path
                fn = doc.original_filename

                if ft == "pdf":
                    extracted = PDFExtractor.extract(fp, fn)
                elif ft in ["docx", "doc"]:
                    extracted = DocxExtractor.extract(fp, fn)
                else:
                    extracted = TextExtractor.extract(fp, fn)

                # Update document metadata
                if extracted.title and len(extracted.title) > 3:
                    doc.title = extracted.title
                if extracted.author and extracted.author != "Unknown Author":
                    doc.author = extracted.author
                if extracted.abstract:
                    doc.abstract = extracted.abstract
                doc.page_count = len(extracted.pages)
                doc.doc_metadata = extracted.metadata
                await db.commit()

                # Status: CHUNKING
                doc.status = DocumentStatus.CHUNKING
                await db.commit()

                chunker = StructureAwareChunker(
                    target_chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap
                )
                processed_chunks = chunker.chunk_document(extracted, document_id=doc.id)

                if not processed_chunks:
                    # Fallback for empty text
                    doc.status = DocumentStatus.COMPLETED
                    await db.commit()
                    return

                # Status: EMBEDDING
                doc.status = DocumentStatus.EMBEDDING
                await db.commit()

                # Prepare texts for batch embedding (prefix with contextual header)
                chunk_texts_for_embed = [
                    f"{c.context_header}\n{c.content}" for c in processed_chunks
                ]
                embeddings = embedding_service.generate_batch_embeddings(chunk_texts_for_embed)

                # Status: INDEXING
                doc.status = DocumentStatus.INDEXING
                await db.commit()

                # Store chunks in relational DB
                chunk_db_objects = []
                payloads = []
                chunk_ids = []

                for idx, (p_chunk, emb) in enumerate(zip(processed_chunks, embeddings)):
                    chunk_uuid = str(uuid.uuid4())
                    chunk_ids.append(chunk_uuid)

                    payload = {
                        "chunk_id": chunk_uuid,
                        "document_id": doc.id,
                        "collection_id": doc.collection_id,
                        "user_id": doc.user_id,
                        "document_title": doc.title,
                        "author": doc.author or "Unknown",
                        "page_number": p_chunk.page_number,
                        "section": p_chunk.section,
                        "subsection": p_chunk.subsection,
                        "chunk_index": p_chunk.chunk_index,
                        "content": p_chunk.content,
                        "context_header": p_chunk.context_header,
                        "token_count": p_chunk.token_count
                    }
                    payloads.append(payload)

                    chunk_db_objects.append(Chunk(
                        id=chunk_uuid,
                        document_id=doc.id,
                        chunk_index=p_chunk.chunk_index,
                        page_number=p_chunk.page_number,
                        section=p_chunk.section,
                        subsection=p_chunk.subsection,
                        paragraph_index=p_chunk.paragraph_index,
                        content=p_chunk.content,
                        context_header=p_chunk.context_header,
                        token_count=p_chunk.token_count,
                        qdrant_point_id=chunk_uuid,
                        chunk_metadata=p_chunk.chunk_metadata
                    ))

                # Upsert to Qdrant
                vector_store.upsert_chunks(
                    chunk_ids=chunk_ids,
                    embeddings=embeddings,
                    payloads=payloads
                )

                # Insert to relational database
                db.add_all(chunk_db_objects)
                doc.chunk_count = len(chunk_db_objects)
                doc.token_count = sum(c.token_count for c in chunk_db_objects)
                doc.status = DocumentStatus.COMPLETED
                doc.error_message = None
                await db.commit()

                logger.info(f"Successfully processed document {doc.id} ({doc.title}): {len(chunk_db_objects)} chunks indexed.")

            except Exception as e:
                logger.error(f"Error processing document {document_id}: {e}", exc_info=True)
                stmt = select(Document).where(Document.id == document_id)
                res = await db.execute(stmt)
                doc = res.scalar_one_or_none()
                if doc:
                    doc.status = DocumentStatus.FAILED
                    doc.error_message = str(e)
                    await db.commit()


ingestion_worker = IngestionWorker()
