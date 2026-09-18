import hashlib
import numpy as np
from typing import List
from researchvault.embeddings.base import BaseEmbeddingProvider


class FastNumpyFallbackProvider(BaseEmbeddingProvider):
    """
    Ultra-fast deterministic projection embedding provider.
    Computes normalized projection vectors from word-level & character hashes.
    Guarantees deterministic, reproducible vector similarity for semantic unit testing offline.
    """
    def __init__(self, dimension: int = 384):
        self.dimension = dimension

    def get_dimension(self) -> int:
        return self.dimension

    def _embed(self, text: str) -> List[float]:
        if not text:
            return [0.0] * self.dimension

        vec = np.zeros(self.dimension, dtype=np.float32)
        words = text.lower().split()
        
        for w in words:
            # Word hash index
            h = int(hashlib.md5(w.encode('utf-8')).hexdigest(), 16)
            idx = h % self.dimension
            sign = 1.0 if (h % 2 == 0) else -1.0
            vec[idx] += sign

        # Add 3-gram character hashes
        for i in range(len(text) - 2):
            gram = text[i:i+3].lower()
            h = int(hashlib.sha256(gram.encode('utf-8')).hexdigest(), 16)
            idx = h % self.dimension
            sign = 0.5 if (h % 2 == 0) else -0.5
            vec[idx] += sign

        norm = np.linalg.norm(vec)
        if norm > 1e-6:
            vec = vec / norm
        return vec.tolist()

    def generate_embedding(self, text: str) -> List[float]:
        return self._embed(text)

    def generate_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        return [self._embed(t) for t in texts]
