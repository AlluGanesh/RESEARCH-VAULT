import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import create_engine
from researchvault.core.config import settings

# Create upload directory if it does not exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
if settings.QDRANT_PATH:
    os.makedirs(settings.QDRANT_PATH, exist_ok=True)

# Async Engine for FastAPI handlers
# If DATABASE_URL starts with postgresql://, replace with postgresql+asyncpg://
db_url = settings.DATABASE_URL
if db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

async_engine = create_async_engine(
    db_url,
    echo=False,
    future=True,
    connect_args={"check_same_thread": False} if "sqlite" in db_url else {}
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

Base = declarative_base()


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    from researchvault.models import (
        user,
        collection,
        document,
        chunk,
        chat,
        observability,
        evaluation,
        knowledge_graph
    )
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
