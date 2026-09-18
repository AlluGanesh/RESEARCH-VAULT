from typing import List
import httpx
from researchvault.embeddings.base import BaseEmbeddingProvider
from researchvault.core.config import settings


class GeminiEmbeddingProvider(BaseEmbeddingProvider):
    def __init__(self, api_key: str = None, model: str = "text-embedding-004"):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model
        self.dimension = 768

    def get_dimension(self) -> int:
        return self.dimension

    def generate_embedding(self, text: str) -> List[float]:
        res = self.generate_batch_embeddings([text])
        return res[0] if res else [0.0] * self.dimension

    def generate_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not configured.")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:batchEmbedContents?key={self.api_key}"
        requests = [
            {"model": f"models/{self.model}", "content": {"parts": [{"text": t}]}}
            for t in texts
        ]
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, json={"requests": requests})
            resp.raise_for_status()
            data = resp.json()
            return [item["values"] for item in data.get("embeddings", [])]


class OllamaEmbeddingProvider(BaseEmbeddingProvider):
    def __init__(self, base_url: str = None, model: str = None):
        self.base_url = base_url or settings.OLLAMA_BASE_URL
        self.model = model or "nomic-embed-text"
        self.dimension = 768

    def get_dimension(self) -> int:
        return self.dimension

    def generate_embedding(self, text: str) -> List[float]:
        url = f"{self.base_url.rstrip('/')}/api/embeddings"
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, json={"model": self.model, "prompt": text})
            resp.raise_for_status()
            data = resp.json()
            return data.get("embedding", [0.0] * self.dimension)

    def generate_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        return [self.generate_embedding(t) for t in texts]
