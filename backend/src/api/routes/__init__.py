"""Aggregate all route modules into a single router."""

from __future__ import annotations

from fastapi import APIRouter

from src.api.routes.chat import router as chat_router
from src.api.routes.contracts import router as contracts_router
from src.api.routes.health import router as health_router
from src.api.routes.ingest import router as ingest_router
from src.api.routes.admin import router as admin_router
from src.auth.routes import router as auth_router
from src.api.routes.calculator import router as calculator_router
from src.api.routes.calendar import router as calendar_router
from src.api.routes.compliance_check import router as compliance_check_router
from src.api.routes.risk_review import router as risk_review_router

router = APIRouter()
router.include_router(health_router)
router.include_router(auth_router)
router.include_router(chat_router)
router.include_router(ingest_router)
router.include_router(admin_router)
router.include_router(contracts_router)
router.include_router(calculator_router)
router.include_router(calendar_router)
router.include_router(compliance_check_router)
router.include_router(risk_review_router)
