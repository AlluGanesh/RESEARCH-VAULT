import pytest
from researchvault.ingestion.extractors.base import ExtractedDocument, PageData, SectionBlock
from researchvault.ingestion.chunker import StructureAwareChunker


def test_structure_aware_chunking():
    doc = ExtractedDocument(
        title="Attention Is All You Need",
        author="Vaswani et al.",
        pages=[
            PageData(
                page_number=1,
                text="The dominant sequence transduction models are based on complex recurrent neural networks. We propose the Transformer.",
                sections=[
                    SectionBlock(
                        title="1. Introduction",
                        level=1,
                        content="Recurrent neural networks, especially LSTM and GRU models, have been firmly established as state-of-the-art approaches in sequence modeling. However, sequential computation precludes parallelization within training examples. In this work we propose the Transformer, a model architecture eschewing recurrence and instead relying entirely on an attention mechanism.",
                        page_number=1
                    )
                ]
            ),
            PageData(
                page_number=3,
                text="Scaled Dot-Product Attention.",
                sections=[
                    SectionBlock(
                        title="2. Scaled Dot-Product Attention",
                        level=1,
                        content="We compute attention as Attention(Q, K, V) = softmax((Q K^T) / sqrt(d_k)) V. The scale factor prevents dot products from growing excessively large in high dimensions.",
                        page_number=3
                    )
                ]
            )
        ]
    )

    chunker = StructureAwareChunker(target_chunk_size=100, chunk_overlap=20)
    chunks = chunker.chunk_document(doc, document_id="doc_123")

    assert len(chunks) >= 2
    assert chunks[0].page_number == 1
    assert "Introduction" in chunks[0].section
    assert "[Document: Attention Is All You Need" in chunks[0].context_header
    assert chunks[1].page_number == 3
    assert "Scaled Dot-Product Attention" in chunks[1].section
