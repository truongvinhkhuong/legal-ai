"""Contract risk review API routes."""

from __future__ import annotations

from dataclasses import asdict
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile

from src.auth.dependencies import get_current_user
from src.db.models.user import User
from src.risk_review.risk_analyzer import analyze_risk
from src.risk_review.risk_rules import CONTRACT_TYPE_LABELS, RISK_RULES

router = APIRouter(prefix="/api/risk-review", tags=["risk-review"])


async def _extract_text(file: UploadFile) -> str:
    content = await file.read()
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError:
        return content.decode("latin-1")


@router.get("/contract-types")
async def list_contract_types(
    _current_user: Annotated[User, Depends(get_current_user)],
) -> list[dict]:
    return [
        {"key": key, "label": CONTRACT_TYPE_LABELS.get(key, key), "rules_count": len(rules)}
        for key, rules in RISK_RULES.items()
    ]


@router.post("/analyze")
async def analyze(
    _current_user: Annotated[User, Depends(get_current_user)],
    file: UploadFile = File(...),
    contract_type: str = Form(default="chung"),
) -> dict:
    text = await _extract_text(file)

    if not text.strip():
        return {
            "error": "Không đọc được nội dung file. Vui lòng thử file .txt hoặc .html.",
        }

    report = await analyze_risk(text, contract_type)
    return asdict(report)
