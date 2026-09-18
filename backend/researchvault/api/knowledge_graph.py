import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from researchvault.database.session import get_db
from researchvault.models.user import User
from researchvault.models.document import Document
from researchvault.models.knowledge_graph import EntityNode, RelationEdge
from researchvault.schemas.knowledge_graph import KnowledgeGraphResponse, NodeSchema, EdgeSchema
from researchvault.api.deps import get_current_user

router = APIRouter(prefix="/knowledge-graph", tags=["Knowledge Graph"])


@router.get("", response_model=KnowledgeGraphResponse)
async def get_graph(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Fetch nodes
    n_stmt = select(EntityNode).where(EntityNode.user_id == current_user.id)
    n_res = await db.execute(n_stmt)
    nodes = n_res.scalars().all()

    # Fetch edges
    e_stmt = select(RelationEdge).join(EntityNode, RelationEdge.source_id == EntityNode.id).where(EntityNode.user_id == current_user.id)
    e_res = await db.execute(e_stmt)
    edges = e_res.scalars().all()

    # If empty, automatically build nodes from user's indexed documents
    if not nodes:
        d_stmt = select(Document).where(Document.user_id == current_user.id)
        d_res = await db.execute(d_stmt)
        docs = d_res.scalars().all()

        created_nodes = []
        created_edges = []

        for d in docs:
            # Paper Node
            paper_node = EntityNode(
                id=str(uuid.uuid4()),
                user_id=current_user.id,
                name=d.title,
                entity_type="Paper",
                description=f"Indexed research document ({d.page_count} pages, {d.chunk_count} chunks)",
                properties={"document_id": d.id, "file_type": d.file_type}
            )
            db.add(paper_node)
            created_nodes.append(paper_node)

            # Author Node
            if d.author and d.author != "Unknown Author":
                author_node = EntityNode(
                    id=str(uuid.uuid4()),
                    user_id=current_user.id,
                    name=d.author,
                    entity_type="Author",
                    description="Lead researcher / Author",
                    properties={}
                )
                db.add(author_node)
                created_nodes.append(author_node)

                # Edge: Author -> WROTE -> Paper
                edge = RelationEdge(
                    id=str(uuid.uuid4()),
                    source_id=author_node.id,
                    target_id=paper_node.id,
                    relation_type="WROTE",
                    document_id=d.id
                )
                db.add(edge)
                created_edges.append(edge)

            # Concept node: RAG / LLM
            concept_node = EntityNode(
                id=str(uuid.uuid4()),
                user_id=current_user.id,
                name="Retrieval-Augmented Generation",
                entity_type="Concept",
                description="Core AI research domain",
                properties={}
            )
            db.add(concept_node)
            created_nodes.append(concept_node)

            edge2 = RelationEdge(
                id=str(uuid.uuid4()),
                source_id=paper_node.id,
                target_id=concept_node.id,
                relation_type="CONTRIBUTES_TO",
                document_id=d.id
            )
            db.add(edge2)
            created_edges.append(edge2)

        if created_nodes:
            await db.commit()
            nodes = created_nodes
            edges = created_edges

    return KnowledgeGraphResponse(
        nodes=[NodeSchema(id=n.id, name=n.name, entity_type=n.entity_type, description=n.description, properties=n.properties or {}) for n in nodes],
        edges=[EdgeSchema(id=e.id, source_id=e.source_id, target_id=e.target_id, relation_type=e.relation_type, weight=e.weight, evidence_text=e.evidence_text, document_id=e.document_id) for e in edges]
    )
