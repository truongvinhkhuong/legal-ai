"""Ingestion endpoint: upload and process documents."""

from __future__ import annotations

import json
import tempfile
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile

from src.api.dependencies import get_engine
from src.api.models import IngestResponse
from src.auth.dependencies import get_current_user
from src.db.models.user import User

router = APIRouter(tags=["ingestion"])


@router.post("/api/ingest", response_model=IngestResponse)
async def ingest_document(
    current_user: Annotated[User, Depends(get_current_user)],
    file: UploadFile = File(...),
    metadata: str = Form("{}"),
):
    engine = get_engine()

    try:
        override_metadata = json.loads(metadata)
    except json.JSONDecodeError:
        override_metadata = {}

    # Inject tenant_id so chunks are isolated per tenant
    override_metadata["tenant_id"] = str(current_user.tenant_id)

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
