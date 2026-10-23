import os
import uuid
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from researchvault.models.user import User
from researchvault.models.collection import Collection
from researchvault.models.document import Document, DocumentStatus
from researchvault.models.chunk import Chunk
from researchvault.models.evaluation import EvaluationDataset, EvaluationTestCase
from researchvault.core.security import get_password_hash
from researchvault.core.config import settings
from researchvault.embeddings.embedding_service import embedding_service
from researchvault.retrieval.vector_store import vector_store

logger = logging.getLogger(__name__)


SAMPLE_PAPERS = [
    {
        "title": "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks",
        "author": "Patrick Lewis, Ethan Perez, Aleksandara Piktus, et al.",
        "filename": "rag_lewis_2020.md",
        "file_type": "md",
        "abstract": "Large pre-trained language models have been shown to store vast amounts of factual knowledge in their parameters, and achieve state-of-the-art results when fine-tuned on downstream NLP tasks. However, their ability to access and precisely manipulate knowledge is still limited. We explore general-purpose fine-tuning recipes for retrieval-augmented generation (RAG) — models which combine pre-trained parametric and non-parametric memory for language generation.",
        "sections": [
            {
                "title": "1. Introduction",
                "page": 1,
                "content": "Large pre-trained language models (LMs) store significant parametric knowledge in their weights. However, they suffer from fundamental issues: they cannot easily expand or revise their memory, they cannot reliably explain their decisions with citations, and they frequently hallucinate non-factual content. To address these limitations, we introduce Retrieval-Augmented Generation (RAG) models. RAG pairs a pre-trained sequence-to-sequence model with a non-parametric dense vector index of Wikipedia accessed via a neural retriever (DPR)."
            },
            {
                "title": "2. Methods & Architecture",
                "page": 2,
                "content": "RAG models leverage two main components: a retriever p_eta(z|x) that provides top-K latent documents given query x, and a generator p_theta(y_i | x, z, y_{1:i-1}) that generates target tokens conditioned on both context z and input x. We propose two variants: RAG-Sequence, where the same retrieved document is used to generate the entire sequence, and RAG-Token, where each token can be conditioned on a different retrieved document. The retriever uses Dense Passage Retrieval (DPR) with 768-dimensional bi-encoder embeddings."
            },
            {
                "title": "3. Experiments & Results",
                "page": 4,
                "content": "We evaluate RAG on a wide range of knowledge-intensive benchmarks: Natural Questions (NQ), TriviaQA, WebQuestions, and CuratedTREC. On Natural Questions, RAG achieves 44.5% exact match, outperforming parametric-only T5-11B while using significantly fewer parameters. In generation tasks like MS-MARCO and Jeopardy question generation, human evaluators find RAG generations substantially more factual and specific than standard BART models."
            },
            {
                "title": "4. Limitations & Discussion",
                "page": 6,
                "content": "While RAG drastically reduces hallucination and provides verifiable evidence, retrieval latency remains higher than pure parametric generation. Furthermore, retrieval quality is bound by index coverage and passage segmentation boundaries. Future work includes iterative multi-hop retrieval and end-to-end retriever fine-tuning."
            }
        ]
    },
    {
        "title": "Attention Is All You Need",
        "author": "Ashish Vaswani, Noam Shazeer, Niki Parmar, et al.",
        "filename": "attention_vaswani_2017.md",
        "file_type": "md",
        "abstract": "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks. We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely.",
        "sections": [
            {
                "title": "1. Introduction",
                "page": 1,
                "content": "Recurrent neural networks, especially LSTM and GRU models, have been firmly established as state-of-the-art approaches in sequence modeling. However, sequential computation precludes parallelization within training examples. In this work we propose the Transformer, a model architecture eschewing recurrence and instead relying entirely on an attention mechanism to draw global dependencies between input and output."
            },
            {
                "title": "2. Scaled Dot-Product and Multi-Head Attention",
                "page": 3,
                "content": "We compute attention as Attention(Q, K, V) = softmax((Q K^T) / sqrt(d_k)) V. The scale factor 1/sqrt(d_k) prevents the dot products from growing large in high dimensions, which would push the softmax function into regions with extremely small gradients. Multi-head attention allows the model to jointly attend to information from different representation subspaces at different positions."
            },
            {
                "title": "3. Training & Benchmark Results",
                "page": 5,
                "content": "On the WMT 2014 English-to-German translation task, the big transformer model achieves a state-of-the-art BLEU score of 28.4, outperforming existing best models by over 2.0 BLEU. On English-to-French translation, our model establishes a new single-model state-of-the-art BLEU score of 41.8 after training for 3.5 days on 8 P100 GPUs."
            }
        ]
    },
    {
        "title": "Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection",
        "author": "Akari Asai, Zeqiu Wu, Yizhong Wang, et al.",
        "filename": "self_rag_asai_2023.md",
        "file_type": "md",
        "abstract": "Despite their remarkable capabilities, large language models (LLMs) often produce hallucinations or ungrounded responses. We introduce Self-RAG (Self-Reflective Retrieval-Augmented Generation), an innovative framework that trains a single LM to adaptively retrieve passages on-demand and evaluate its own predictions using special reflection tokens.",
        "sections": [
            {
                "title": "1. Framework & Self-Reflection Tokens",
                "page": 1,
                "content": "Self-RAG introduces special reflection tokens: [Retrieve], [IsRel], [IsSup], and [IsUse]. The model dynamically decides when to retrieve external knowledge rather than retrieving unconditionally on every step. When retrieval is triggered, the model retrieves multiple passage candidates in parallel, generates critique tokens to evaluate passage relevance ([IsRel]) and groundedness ([IsSup]), and filters out unsupported content."
            },
            {
                "title": "2. Empirical Results & Hallucination Mitigation",
                "page": 4,
                "content": "Experiments across open-domain QA (PopQA, TriviaQA), reasoning (ARC, GSM8K), and fact-checking (FactScore) show that Self-RAG (7B/13B parameters) significantly outperforms standard RAG and larger proprietary models like ChatGPT in factual accuracy and citation precision while reducing unnecessary retrieval steps by over 60%."
            }
        ]
    }
]


async def seed_database(db: AsyncSession):
    # Check if demo user exists
    user_stmt = select(User).where(User.email == "researcher@researchvault.ai")
    res = await db.execute(user_stmt)
    user = res.scalar_one_or_none()

    if not user:
        user = User(
            id=str(uuid.uuid4()),
            email="researcher@researchvault.ai",
            hashed_password=get_password_hash("ResearchVault2026!"),
            full_name="Ganesh",
            is_active=True,
            is_superuser=True
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    # Check collections
    col_stmt = select(Collection).where(Collection.user_id == user.id)
    col_res = await db.execute(col_stmt)
    existing_cols = col_res.scalars().all()
    
    if not existing_cols:
        col1 = Collection(
            id=str(uuid.uuid4()),
            user_id=user.id,
            name="Generative AI & RAG Foundations",
            description="Seminal papers on Retrieval-Augmented Generation and factual grounding",
            color="#6366f1"
        )
        col2 = Collection(
            id=str(uuid.uuid4()),
            user_id=user.id,
            name="Transformer Architectures",
            description="Core foundational models and self-attention mechanisms",
            color="#10b981"
        )
        db.add_all([col1, col2])
        await db.commit()
        await db.refresh(col1)
        await db.refresh(col2)
        default_col_id = col1.id
    else:
        default_col_id = existing_cols[0].id

    # Check documents
    doc_stmt = select(Document).where(Document.user_id == user.id)
    doc_res = await db.execute(doc_stmt)
    existing_docs = doc_res.scalars().all()

    if not existing_docs:
        logger.info("Seeding initial research papers into ResearchVault AI...")
        
        for paper_data in SAMPLE_PAPERS:
            doc_id = str(uuid.uuid4())
            file_path = os.path.join(settings.UPLOAD_DIR, f"{doc_id}_{paper_data['filename']}")
            
            # Write markdown file
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"# {paper_data['title']}\n\n**Author:** {paper_data['author']}\n\n## Abstract\n{paper_data['abstract']}\n\n")
                for s in paper_data["sections"]:
                    f.write(f"## {s['title']}\n{s['content']}\n\n")

            doc = Document(
                id=doc_id,
                user_id=user.id,
                collection_id=default_col_id,
                title=paper_data["title"],
                original_filename=paper_data["filename"],
                file_path=file_path,
                file_type=paper_data["file_type"],
                file_size_bytes=os.path.getsize(file_path),
                author=paper_data["author"],
                abstract=paper_data["abstract"],
                page_count=len(paper_data["sections"]),
                status=DocumentStatus.COMPLETED
            )
            db.add(doc)

            # Create chunks
            chunk_objs = []
            chunk_ids = []
            embeddings_texts = []
            payloads = []

            for idx, s in enumerate(paper_data["sections"]):
                chunk_id = str(uuid.uuid4())
                chunk_ids.append(chunk_id)
                
                context_hdr = f"[Document: {paper_data['title']} | Author: {paper_data['author']} | Section: {s['title']} | Page: {s['page']}]"
                full_text = f"{context_hdr}\n{s['content']}"
                embeddings_texts.append(full_text)

                payload = {
                    "chunk_id": chunk_id,
                    "document_id": doc_id,
                    "collection_id": default_col_id,
                    "user_id": user.id,
                    "document_title": paper_data["title"],
                    "author": paper_data["author"],
                    "page_number": s["page"],
                    "section": s["title"],
                    "subsection": None,
                    "chunk_index": idx,
                    "content": s["content"],
                    "context_header": context_hdr,
                    "token_count": len(s["content"].split()) * 2
                }
                payloads.append(payload)

                chunk_obj = Chunk(
                    id=chunk_id,
                    document_id=doc_id,
                    chunk_index=idx,
                    page_number=s["page"],
                    section=s["title"],
                    content=s["content"],
                    context_header=context_hdr,
                    token_count=len(s["content"].split()) * 2,
                    qdrant_point_id=chunk_id
                )
                chunk_objs.append(chunk_obj)

            # Generate embeddings and upsert to Qdrant
            embeddings = embedding_service.generate_batch_embeddings(embeddings_texts)
            vector_store.upsert_chunks(
                chunk_ids=chunk_ids,
                embeddings=embeddings,
                payloads=payloads
            )

            db.add_all(chunk_objs)
            doc.chunk_count = len(chunk_objs)
            doc.token_count = sum(c.token_count for c in chunk_objs)

        await db.commit()
        logger.info("Sample research papers seeded successfully into database & Qdrant.")

    # Seed Evaluation Dataset
    eval_stmt = select(EvaluationDataset).where(EvaluationDataset.user_id == user.id)
    eval_res = await db.execute(eval_stmt)
    existing_ds = eval_res.scalars().all()

    if not existing_ds:
        dataset_id = str(uuid.uuid4())
        eval_ds = EvaluationDataset(
            id=dataset_id,
            user_id=user.id,
            name="LLM & RAG Grounding Benchmark v1",
            description="Gold-standard research QA evaluation suite testing retrieval precision, factual attribution, and citation accuracy."
        )
        db.add(eval_ds)

        test_cases = [
            EvaluationTestCase(
                id=str(uuid.uuid4()),
                dataset_id=dataset_id,
                question="How does Retrieval-Augmented Generation combine parametric and non-parametric memory?",
                ground_truth_answer="RAG combines a pre-trained sequence-to-sequence parametric neural generator (such as BART) with a non-parametric dense vector index of passages accessed via Dense Passage Retrieval (DPR).",
                relevant_doc_titles=["Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks"],
                relevant_passages=["RAG pairs a pre-trained sequence-to-sequence model with a non-parametric dense vector index"]
            ),
            EvaluationTestCase(
                id=str(uuid.uuid4()),
                dataset_id=dataset_id,
                question="Why is scaled dot-product attention divided by the square root of d_k in Transformers?",
                ground_truth_answer="Dividing by sqrt(d_k) prevents dot products from growing excessively large in high dimensions, which would otherwise push the softmax function into regions with extremely small gradients.",
                relevant_doc_titles=["Attention Is All You Need"],
                relevant_passages=["The scale factor 1/sqrt(d_k) prevents the dot products from growing large in high dimensions"]
            ),
            EvaluationTestCase(
                id=str(uuid.uuid4()),
                dataset_id=dataset_id,
                question="What special reflection tokens does Self-RAG introduce to regulate on-demand retrieval?",
                ground_truth_answer="Self-RAG introduces reflection tokens including [Retrieve], [IsRel], [IsSup], and [IsUse] to dynamically determine when to retrieve and to evaluate passage relevance and support.",
                relevant_doc_titles=["Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection"],
                relevant_passages=["Self-RAG introduces special reflection tokens: [Retrieve], [IsRel], [IsSup], and [IsUse]"]
            )
        ]
        db.add_all(test_cases)
        await db.commit()
        logger.info("Evaluation benchmark dataset seeded successfully.")
