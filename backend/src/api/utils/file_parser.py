"""Shared file text extraction — reuses the ingestion FormatRouter for PDF/DOCX."""

from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import UploadFile

from src.ingestion.format_router import FormatRouter

_router = FormatRouter()

# Extensions that need a temp file (binary formats)
_BINARY_EXTS = {".pdf", ".docx"}


async def extract_text_from_upload(file: UploadFile) -> str:
    """Read an UploadFile and return its plain-text content.

    Supports: .txt, .html, .htm, .pdf, .docx
    """
    content = await file.read()
    filename = file.filename or "upload.txt"
    ext = Path(filename).suffix.lower()

    if ext in _BINARY_EXTS:
        # Binary formats: write to temp file, parse via FormatRouter
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        try:
            parsed = await _router.parse(file_path=tmp_path)
            return parsed.raw_text
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    # Text-based formats: decode and optionally strip HTML tags
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        text = content.decode("latin-1")

    if ext in {".html", ".htm"}:
        parsed = await _router.parse(file_path=f"upload{ext}", file_content=content)
        return parsed.raw_text

    return text
