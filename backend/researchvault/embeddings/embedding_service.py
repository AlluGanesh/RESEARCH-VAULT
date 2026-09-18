import logging
from typing import List, Optional
from researchvault.core.config import settings
from researchvault.embeddings.base import BaseEmbeddingProvider
from researchvault.embeddings.sentence_transformer_provider import SentenceTransformerProvider
from researchvault.embeddings.openai_provider import OpenAIEmbeddingProvider
from researchvault.embeddings.gemini_provider import GeminiEmbeddingProvider
from researchvault.embeddings.ollama_provider import OllamaEmbeddingProvider
from researchvault.embeddings.fast_numpy_provider import FastNumpyFallbackProvider

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self, provider_type: Optional[str] = None):
        self.provider_type = provider_type or settings.EMBEDDING_PROVIDER
        self.provider: BaseEmbeddingProvider = self._initialize_provider()

    def _initialize_provider(self) -> BaseEmbeddingProvider:
        ptype = (self.provider_type or "").lower()
        try:
            if "openai" in ptype:
                return OpenAIEmbeddingProvider()
            elif "gemini" in ptype:
                return GeminiEmbeddingProvider()
            elif "ollama" in ptype:
                return OllamaEmbeddingProvider()
            elif "numpy" in ptype or "fast" in ptype:
                return FastNumpyFallbackProvider(dimension=settings.EMBEDDING_DIMENSION)
            else:
                # Default to SentenceTransformers
                return SentenceTransformerProvider()
        except Exception as e:
            logger.warning(f"Failed to load embedding provider '{ptype}': {e}. Falling back to FastNumpyFallbackProvider.")
            return FastNumpyFallbackProvider(dimension=settings.EMBEDDING_DIMENSION)

    def get_dimension(self) -> int:
        return self.provider.get_dimension()

    def generate_embedding(self, text: str) -> List[float]:
        return self.provider.generate_embedding(text)

    def generate_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        return self.provider.generate_batch_embeddings(texts)


# Default global instance
embedding_service = EmbeddingService()
