from typing import List
from researchvault.embeddings.base import BaseEmbeddingProvider
from researchvault.core.config import settings
import numpy as np


class SentenceTransformerProvider(BaseEmbeddingProvider):
    def __init__(self, model_name: str = None):
        self.model_name = model_name or settings.SENTENCE_TRANSFORMER_MODEL
        self._model = None
        self._dimension = 384

    def _load_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)
            self._dimension = self._model.get_sentence_embedding_dimension()

    def get_dimension(self) -> int:
        self._load_model()
        return self._dimension

    def generate_embedding(self, text: str) -> List[float]:
        self._load_model()
        emb = self._model.encode(text, normalize_embeddings=True)
        return emb.tolist()

    def generate_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        self._load_model()
        embs = self._model.encode(texts, batch_size=32, show_progress_bar=False, normalize_embeddings=True)
        return embs.tolist()
