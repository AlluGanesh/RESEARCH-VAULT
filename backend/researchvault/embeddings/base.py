from abc import ABC, abstractmethod
from typing import List


class BaseEmbeddingProvider(ABC):
    @abstractmethod
    def get_dimension(self) -> int:
        """Returns the embedding vector dimension."""
        pass

    @abstractmethod
    def generate_embedding(self, text: str) -> List[float]:
        """Generates embedding for a single text string."""
        pass

    @abstractmethod
    def generate_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generates embeddings for a batch of text strings."""
        pass
