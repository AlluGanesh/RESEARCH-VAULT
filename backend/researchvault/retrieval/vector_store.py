import logging
import uuid
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from researchvault.core.config import settings

logger = logging.getLogger(__name__)


class QdrantVectorStore:
    def __init__(
        self,
        collection_name: str = None,
        dimension: int = None
    ):
        self.collection_name = collection_name or settings.QDRANT_COLLECTION_NAME
        self.dimension = dimension or settings.EMBEDDING_DIMENSION
        self.client = self._init_client()
        self._ensure_collection()

    def _init_client(self) -> QdrantClient:
        # Check if remote host is provided
        if settings.QDRANT_HOST:
            try:
                client = QdrantClient(
                    host=settings.QDRANT_HOST,
                    port=settings.QDRANT_PORT,
                    api_key=settings.QDRANT_API_KEY,
                    timeout=10.0
                )
                client.get_collections()
                logger.info(f"Connected to remote Qdrant at {settings.QDRANT_HOST}:{settings.QDRANT_PORT}")
                return client
            except Exception as e:
                logger.warning(f"Could not connect to remote Qdrant: {e}. Falling back to local storage.")
        
        # Fallback to local embedded storage
        try:
            client = QdrantClient(path=settings.QDRANT_PATH)
            logger.info(f"Initialized local embedded Qdrant at {settings.QDRANT_PATH}")
            return client
        except Exception as e:
            logger.warning(f"Embedded Qdrant error: {e}. Using in-memory Qdrant instance.")
            return QdrantClient(location=":memory:")

    def _ensure_collection(self):
        try:
            collections = self.client.get_collections().collections
            exists = any(c.name == self.collection_name for c in collections)
            if not exists:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=qmodels.VectorParams(
                        size=self.dimension,
                        distance=qmodels.Distance.COSINE
                    )
                )
                logger.info(f"Created Qdrant collection: {self.collection_name} (dim: {self.dimension})")
                
                # Create payload indexes for fast filtered search if remote Qdrant
                if settings.QDRANT_HOST:
                    for field in ["user_id", "document_id", "collection_id", "author"]:
                        try:
                            self.client.create_payload_index(
                                collection_name=self.collection_name,
                                field_name=field,
                                field_schema=qmodels.PayloadSchemaType.KEYWORD
                            )
                        except Exception:
                            pass
        except Exception as e:
            logger.error(f"Error ensuring Qdrant collection: {e}")

    def upsert_chunks(
        self,
        chunk_ids: List[str],
        embeddings: List[List[float]],
        payloads: List[Dict[str, Any]]
    ) -> List[str]:
        if not chunk_ids or not embeddings:
            return []

        points = []
        point_ids = []
        for cid, emb, payload in zip(chunk_ids, embeddings, payloads):
            # Qdrant requires valid UUID or integer point IDs
            try:
                point_id = str(uuid.UUID(cid))
            except Exception:
                point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, cid))
            point_ids.append(point_id)

            points.append(qmodels.PointStruct(
                id=point_id,
                vector=emb,
                payload=payload
            ))

        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        return point_ids

    def search(
        self,
        query_vector: List[float],
        top_k: int = 20,
        user_id: Optional[str] = None,
        collection_id: Optional[str] = None,
        document_ids: Optional[List[str]] = None,
        author: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        must_conditions = []

        if user_id:
            must_conditions.append(
                qmodels.FieldCondition(
                    key="user_id",
                    match=qmodels.MatchValue(value=user_id)
                )
            )
        if collection_id:
            must_conditions.append(
                qmodels.FieldCondition(
                    key="collection_id",
                    match=qmodels.MatchValue(value=collection_id)
                )
            )
        if document_ids and len(document_ids) > 0:
            must_conditions.append(
                qmodels.FieldCondition(
                    key="document_id",
                    match=qmodels.MatchAny(any=document_ids)
                )
            )
        if author:
            must_conditions.append(
                qmodels.FieldCondition(
                    key="author",
                    match=qmodels.MatchValue(value=author)
                )
            )

        q_filter = qmodels.Filter(must=must_conditions) if must_conditions else None

        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            query_filter=q_filter,
            limit=top_k,
            with_payload=True
        )

        formatted_results = []
        for r in results:
            item = dict(r.payload) if r.payload else {}
            item["score"] = float(r.score)
            item["point_id"] = str(r.id)
            formatted_results.append(item)

        return formatted_results

    def delete_by_document_id(self, document_id: str):
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=qmodels.FilterSelector(
                    filter=qmodels.Filter(
                        must=[
                            qmodels.FieldCondition(
                                key="document_id",
                                match=qmodels.MatchValue(value=document_id)
                            )
                        ]
                    )
                )
            )
        except Exception as e:
            logger.error(f"Error deleting chunks from Qdrant for document {document_id}: {e}")


# Global vector store instance
vector_store = QdrantVectorStore()
