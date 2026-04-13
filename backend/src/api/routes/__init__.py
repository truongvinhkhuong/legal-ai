"""Aggregate all route modules into a single router."""

from __future__ import annotations

from fastapi import APIRouter

from src.api.routes.chat import router as chat_router
from src.api.routes.health import router as health_router
from src.api.routes.ingest import router as ingest_router
from src.api.routes.admin import router as admin_router

router = APIRouter()
router.include_router(health_router)
router.include_router(chat_router)
router.include_router(ingest_router)
router.include_router(admin_router)
