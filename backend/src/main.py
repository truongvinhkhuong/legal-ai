"""FastAPI application entry point."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import router
from src.config.settings import settings
from src.core import redis_client
from src.retrieval.hierarchical_retriever import (
    close_qdrant_client,
    ensure_collection,
)

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    logger.info("Starting Legal RAG service (env=%s)", settings.app_env)

    # PostgreSQL
    try:
        from src.config.database import init_db
        await init_db()
        logger.info("PostgreSQL connected, tables ensured")
    except Exception:
        logger.warning("PostgreSQL unavailable — admin features disabled", exc_info=True)

    # Qdrant
    try:
        await ensure_collection()
    except Exception:
        logger.warning("Could not connect to Qdrant — will retry on first request", exc_info=True)

    # Redis
    await redis_client.connect()

    yield

    # --- Shutdown ---
    logger.info("Shutting down Legal RAG service")
    await redis_client.close()
    await close_qdrant_client()

    try:
        from src.config.database import close_db
        await close_db()
    except Exception:
        pass


app = FastAPI(
    title="Legal RAG API",
    description="Vietnamese Legal Document Q&A with precise citations",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
