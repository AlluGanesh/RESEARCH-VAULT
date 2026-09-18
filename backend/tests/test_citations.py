import pytest
from researchvault.generation.citation_engine import citation_engine


def test_citation_extraction_from_grounded_text():
    sample_text = (
        "Retrieval-Augmented Generation pairs a pre-trained sequence-to-sequence model with a dense index [1]. "
        "The model achieves 44.5% exact match on Natural Questions benchmarks [1, 2]. "
        "Self-RAG adds special reflection tokens [3]."
    )
    
    mock_chunks = [
        {
            "citation_number": 1,
            "document_id": "doc_rag",
            "document_title": "RAG for Knowledge-Intensive NLP",
            "page_number": 1,
            "section": "1. Introduction",
            "content": "RAG pairs a pre-trained sequence-to-sequence model with a dense vector index."
        },
        {
            "citation_number": 2,
            "document_id": "doc_rag",
            "document_title": "RAG for Knowledge-Intensive NLP",
            "page_number": 4,
            "section": "3. Experiments",
            "content": "On Natural Questions, RAG achieves 44.5% exact match."
        },
        {
            "citation_number": 3,
            "document_id": "doc_selfrag",
            "document_title": "Self-RAG Reflection",
            "page_number": 1,
            "section": "1. Framework",
            "content": "Self-RAG introduces special reflection tokens."
        }
    ]

    citations = citation_engine._extract_citations_from_text(sample_text, mock_chunks)
    
    assert len(citations) == 3
    assert citations[0]["citation_number"] == 1
    assert citations[0]["document_title"] == "RAG for Knowledge-Intensive NLP"
    assert citations[1]["citation_number"] == 2
    assert citations[2]["citation_number"] == 3
