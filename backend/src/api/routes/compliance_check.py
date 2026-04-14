"""Compliance gap check API routes."""

from __future__ import annotations

from dataclasses import asdict
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile

from src.api.utils.file_parser import extract_text_from_upload
from src.auth.dependencies import get_current_user
from src.core.gate import require_feature
from src.compliance_check.checklists import CHECKLIST_LABELS, CHECKLISTS
from src.compliance_check.gap_analyzer import analyze_gaps
from src.db.models.user import User

router = APIRouter(prefix="/api/compliance-check", tags=["compliance-check"])


@router.get("/checklists")
async def list_checklists(
    _current_user: Annotated[User, Depends(require_feature("compliance_check"))],
) -> list[dict]:
    """List available checklist types."""
    return [
        {
            "key": key,
            "label": CHECKLIST_LABELS.get(key, key),
            "items_count": len(items),
        }
        for key, items in CHECKLISTS.items()
    ]


@router.post("/analyze")
async def analyze(
    _current_user: Annotated[User, Depends(require_feature("compliance_check"))],
    file: UploadFile = File(...),
    checklist_type: str = Form(default="noi_quy"),
) -> dict:
    """Upload file + checklist type → gap analysis report."""
    text = await extract_text_from_upload(file)

    if not text.strip():
        return {
            "error": "Không đọc được nội dung file. Vui lòng thử file .txt, .html, .pdf hoặc .docx.",
        }

    report = await analyze_gaps(text, checklist_type)
    return asdict(report)
