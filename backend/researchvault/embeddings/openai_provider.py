from typing import List
import httpx
from researchvault.embeddings.base import BaseEmbeddingProvider
from researchvault.core.config import settings


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or settings.OPENAI_EMBEDDING_MODEL
        self.dimension = 1536 if "ada" in self.model else 1536

    def get_dimension(self) -> int:
        return self.dimension

    def generate_embedding(self, text: str) -> List[float]:
        res = self.generate_batch_embeddings([text])
        return res[0] if res else [0.0] * self.dimension

    def generate_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is not set. Please configure it in settings.")
        
        url = "https://api.openai.com/v1/embeddings"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "input": texts,
            "model": self.model
        }
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            # Sort by index
            sorted_data = sorted(data["data"], key=lambda x: x["index"])
            return [item["embedding"] for item in sorted_data]
