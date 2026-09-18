import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from researchvault.core.config import settings
from researchvault.database.session import init_db, AsyncSessionLocal
from researchvault.database.seed import seed_database

# Routers
from researchvault.api.auth import router as auth_router
from researchvault.api.documents import router as documents_router
from researchvault.api.collections import router as collections_router
from researchvault.api.chat import router as chat_router
from researchvault.api.research import router as research_router
from researchvault.api.compare import router as compare_router
from researchvault.api.evaluation import router as evaluation_router
from researchvault.api.observability import router as observability_router
from researchvault.api.knowledge_graph import router as kg_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("ResearchVaultAI")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database schemas...")
    await init_db()
    
    # Run seed script
    async with AsyncSessionLocal() as session:
        try:
            await seed_database(session)
        except Exception as e:
            logger.warning(f"Database seed notice: {e}")
            
    logger.info("ResearchVault AI Backend initialized and ready.")
    yield
    logger.info("Shutting down ResearchVault AI...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers under /api
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(documents_router, prefix=settings.API_V1_STR)
app.include_router(collections_router, prefix=settings.API_V1_STR)
app.include_router(chat_router, prefix=settings.API_V1_STR)
app.include_router(research_router, prefix=settings.API_V1_STR)
app.include_router(compare_router, prefix=settings.API_V1_STR)
app.include_router(evaluation_router, prefix=settings.API_V1_STR)
app.include_router(observability_router, prefix=settings.API_V1_STR)
app.include_router(kg_router, prefix=settings.API_V1_STR)


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "embedding_provider": settings.EMBEDDING_PROVIDER,
        "reranker": settings.RERANKER_TYPE,
        "llm_provider": settings.DEFAULT_LLM_PROVIDER
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
