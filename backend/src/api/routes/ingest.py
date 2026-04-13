"""Ingestion endpoint: upload and process documents."""

from __future__ import annotations

import json
import tempfile

from fastapi import APIRouter, File, Form, UploadFile

from src.api.dependencies import get_engine
from src.api.models import IngestResponse

router = APIRouter(tags=["ingestion"])


@router.post("/api/ingest", response_model=IngestResponse)
async def ingest_document(
    file: UploadFile = File(...),
    metadata: str = Form("{}"),
):
    engine = get_engine()

    try:
        override_metadata = json.loads(metadata)
    except json.JSONDecodeError:
        override_metadata = {}

    suffix = (
        f".{file.filename.split('.')[-1]}"
        if file.filename and "." in file.filename
        else ".pdf"
    )
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    result = await engine.ingest(tmp_path, override_metadata)
    return result
