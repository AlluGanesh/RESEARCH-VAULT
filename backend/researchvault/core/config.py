import os
from typing import List, Optional
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "ResearchVault AI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    DESCRIPTION: str = "Research Intelligence & RAG Platform"

    # Security
    SECRET_KEY: str = "researchvault_ai_super_secret_jwt_key_2026_dev_prod_change_me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Database: Supports SQLite (zero setup) or PostgreSQL
    DATABASE_URL: str = "sqlite+aiosqlite:///./researchvault.db"
    SYNC_DATABASE_URL: str = "sqlite:///./researchvault.db"
    POSTGRES_SERVER: Optional[str] = None
    POSTGRES_USER: Optional[str] = "postgres"
    POSTGRES_PASSWORD: Optional[str] = "postgres"
    POSTGRES_DB: Optional[str] = "researchvault"
    POSTGRES_PORT: Optional[int] = 5432

    # Qdrant Vector Store
    QDRANT_HOST: Optional[str] = None
    QDRANT_PORT: int = 6333
    QDRANT_API_KEY: Optional[str] = None
    QDRANT_PATH: Optional[str] = "./qdrant_storage"  # Local embedded Qdrant fallback
    QDRANT_COLLECTION_NAME: str = "research_vault_chunks"

    # Redis for workers (optional, falls back to in-memory/async background tasks)
    REDIS_URL: Optional[str] = "redis://localhost:6379/0"
    USE_REDIS_QUEUE: bool = False

    # LLM Settings
    DEFAULT_LLM_PROVIDER: str = "openai"  # openai, gemini, ollama, mock
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = "gpt-4o-mini"
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = "gemini-1.5-flash"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"

    # Embeddings
    EMBEDDING_PROVIDER: str = "sentence-transformers"  # sentence-transformers, openai, gemini, ollama, fast-numpy
    SENTENCE_TRANSFORMER_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSION: int = 384  # Default 384 for MiniLM

    # Reranker
    RERANKER_TYPE: str = "cross-encoder"  # cross-encoder, flashrank, llm, heuristic
    RERANKER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    # RAG Hyperparameters
    DEFAULT_TOP_K_RETRIEVAL: int = 20
    DEFAULT_TOP_K_RERANKED: int = 7
    RRF_K_CONSTANT: int = 60
    CHUNK_SIZE_TOKENS: int = 500
    CHUNK_OVERLAP_TOKENS: int = 100

    # Storage directory
    UPLOAD_DIR: str = "./uploads"

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "*"
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
