"""Async Redis client — optional for Phase 1."""

from __future__ import annotations

import json
import logging

from src.config.settings import settings

logger = logging.getLogger(__name__)

_redis = None


async def connect() -> None:
    global _redis
    try:
        import redis.asyncio as aioredis
        _redis = aioredis.from_url(settings.redis_url, decode_responses=True)
        await _redis.ping()
        logger.info("Redis connected at %s", settings.redis_url)
    except Exception:
        logger.warning("Redis unavailable — sessions/cache disabled", exc_info=True)
        _redis = None


async def close() -> None:
    global _redis
    if _redis is not None:
        await _redis.close()
        _redis = None


async def ping() -> bool:
    if _redis is None:
        return False
    try:
        return await _redis.ping()
    except Exception:
        return False


async def get_session(session_id: str) -> list[dict] | None:
    if _redis is None:
        return None
    try:
        data = await _redis.get(f"session:{session_id}")
        return json.loads(data) if data else None
    except Exception:
        return None


async def set_session(session_id: str, history: list[dict], ttl: int = 1800) -> None:
    if _redis is None:
        return
    try:
        await _redis.set(f"session:{session_id}", json.dumps(history), ex=ttl)
    except Exception:
        logger.warning("Failed to save session %s", session_id, exc_info=True)
