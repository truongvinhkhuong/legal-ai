"""Ingestion endpoint: upload and process documents."""

from __future__ import annotations

import json
import tempfile
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_engine
from src.api.models import IngestResponse
from src.auth.dependencies import get_current_user
from src.config.database import get_db
from src.core.audit import log_action
from src.db.models.document import Document
from src.db.models.user import User

router = APIRouter(tags=["ingestion"])


@router.post("/api/ingest", response_model=IngestResponse)
async def ingest_document(
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
    file: UploadFile = File(...),
    metadata: str = Form("{}"),
):
    engine = get_engine()

    try:
        override_metadata = json.loads(metadata)
    except json.JSONDecodeError:
        override_metadata = {}

    # Create Document row in DB first to get a stable doc_id
    doc_row = Document(
        tenant_id=current_user.tenant_id,
        doc_number=override_metadata.get("doc_number", ""),
        doc_title=override_metadata.get("doc_title", file.filename or ""),
        doc_type=override_metadata.get("doc_type", "khac"),
        status=override_metadata.get("status", "hieu_luc"),
        issuing_authority=override_metadata.get("issuing_authority", ""),
        access_level=override_metadata.get("access_level", "public"),
        uploaded_by=current_user.id,
    )
    db.add(doc_row)
    await db.flush()  # get doc_row.id without committing

    # Inject tenant_id and doc_id so Qdrant chunks are linked to this DB row
    override_metadata["tenant_id"] = str(current_user.tenant_id)
    override_metadata["doc_id"] = str(doc_row.id)

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

    # Update Document row with ingestion results
    doc_row.chunks_count = result.chunks_created
    doc_row.structure_detected = result.structure_detected
    doc_row.original_file_path = tmp_path

    await log_action(
        db, tenant_id=current_user.tenant_id, user_id=current_user.id,
        action="ingest", resource_type="document", resource_id=doc_row.id,
        details={"filename": file.filename, "chunks": result.chunks_created},
    )

    return result
