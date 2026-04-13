"""Shared FastAPI dependencies: engine singleton, DB session, auth."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import get_db
from src.core.rag_engine import RAGEngine

_engine: RAGEngine | None = None


def get_engine() -> RAGEngine:
    """Return singleton RAGEngine instance."""
    global _engine
    if _engine is None:
        _engine = RAGEngine()
    return _engine


# Re-export get_db for convenience
get_db_session = get_db
