"""Health check endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from src.core import redis_client
from src.retrieval.hierarchical_retriever import get_qdrant_client

router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.get("/api/health")
async def health_detailed():
    qdrant_ok = False
    try:
        client = await get_qdrant_client()
        await client.get_collections()
        qdrant_ok = True
    except Exception:
        pass

    redis_ok = await redis_client.ping()

    db_ok = False
    try:
        from src.config.database import engine
        async with engine.connect() as conn:
            await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
            db_ok = True
    except Exception:
        pass

    overall = "ok" if (qdrant_ok and db_ok) else "degraded"

    return {
        "status": overall,
        "qdrant": "connected" if qdrant_ok else "unavailable",
        "redis": "connected" if redis_ok else "unavailable",
        "postgres": "connected" if db_ok else "unavailable",
    }
