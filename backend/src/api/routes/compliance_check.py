"""Compliance gap check API routes."""

from __future__ import annotations

import io
from dataclasses import asdict
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile

from src.auth.dependencies import get_current_user
from src.compliance_check.checklists import CHECKLIST_LABELS, CHECKLISTS
from src.compliance_check.gap_analyzer import analyze_gaps
from src.db.models.user import User

router = APIRouter(prefix="/api/compliance-check", tags=["compliance-check"])


async def _extract_text(file: UploadFile) -> str:
    """Extract plain text from uploaded file."""
    content = await file.read()

    # For now, treat as UTF-8 text (supports .txt, .html, .htm)
    # PDF/DOCX support can be added later via existing ingestion pipeline
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError:
        return content.decode("latin-1")


@router.get("/checklists")
async def list_checklists(
    _current_user: Annotated[User, Depends(get_current_user)],
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
    _current_user: Annotated[User, Depends(get_current_user)],
    file: UploadFile = File(...),
    checklist_type: str = Form(default="noi_quy"),
) -> dict:
    """Upload file + checklist type → gap analysis report."""
    text = await _extract_text(file)

    if not text.strip():
        return {
            "error": "Không đọc được nội dung file. Vui lòng thử file .txt hoặc .html.",
        }

    report = await analyze_gaps(text, checklist_type)
    return asdict(report)
