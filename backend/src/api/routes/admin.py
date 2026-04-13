"""Admin endpoints: document management, CRUD operations."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import get_db
from src.db.models.document import Document, DocumentRelationship

router = APIRouter(prefix="/api/admin", tags=["admin"])


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class DocumentListItem(BaseModel):
    id: str
    doc_number: str
    doc_title: str
    doc_type: str
    status: str
    issuing_authority: str
    effective_date: str | None
    chunks_count: int
    created_at: str


class DocumentUpdate(BaseModel):
    doc_title: str | None = None
    doc_type: str | None = None
    status: str | None = None
    issuing_authority: str | None = None
    access_level: str | None = None
    allowed_departments: list[str] | None = None


class RelationshipCreate(BaseModel):
    target_doc_id: str
    relationship_type: str  # sua_doi|thay_the|huong_dan|bai_bo|dan_chieu
    notes: str = ""


# ---------------------------------------------------------------------------
# Document CRUD
# ---------------------------------------------------------------------------

@router.get("/documents")
async def list_documents(
    db: AsyncSession = Depends(get_db),
    doc_type: str | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    query = select(Document).order_by(Document.created_at.desc())

    if doc_type:
        query = query.where(Document.doc_type == doc_type)
    if status:
        query = query.where(Document.status == status)

    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    docs = result.scalars().all()

    return {
        "items": [
            DocumentListItem(
                id=str(d.id),
                doc_number=d.doc_number,
                doc_title=d.doc_title,
                doc_type=d.doc_type,
                status=d.status,
                issuing_authority=d.issuing_authority,
                effective_date=d.effective_date.isoformat() if d.effective_date else None,
                chunks_count=d.chunks_count,
                created_at=d.created_at.isoformat(),
            )
            for d in docs
        ],
        "total": len(docs),
    }


@router.get("/documents/{doc_id}")
async def get_document(
    doc_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    doc = await db.get(Document, uuid.UUID(doc_id))
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    return {
        "id": str(doc.id),
        "doc_number": doc.doc_number,
        "doc_title": doc.doc_title,
        "doc_type": doc.doc_type,
        "status": doc.status,
        "issuing_authority": doc.issuing_authority,
        "issue_date": doc.issue_date.isoformat() if doc.issue_date else None,
        "effective_date": doc.effective_date.isoformat() if doc.effective_date else None,
        "expiry_date": doc.expiry_date.isoformat() if doc.expiry_date else None,
        "legal_hierarchy": doc.legal_hierarchy,
        "access_level": doc.access_level,
        "allowed_departments": doc.allowed_departments,
        "chunks_count": doc.chunks_count,
        "structure_detected": doc.structure_detected,
        "original_file_path": doc.original_file_path,
        "extra_metadata": doc.extra_metadata,
    }


@router.patch("/documents/{doc_id}")
async def update_document(
    doc_id: str,
    update: DocumentUpdate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    doc = await db.get(Document, uuid.UUID(doc_id))
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    update_data = update.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(doc, field, value)

    return {"status": "updated", "id": doc_id}


@router.delete("/documents/{doc_id}")
async def delete_document(
    doc_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    doc = await db.get(Document, uuid.UUID(doc_id))
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    await db.delete(doc)
    # TODO: Also delete chunks from Qdrant

    return {"status": "deleted", "id": doc_id}


# ---------------------------------------------------------------------------
# Document relationships
# ---------------------------------------------------------------------------

@router.post("/documents/{doc_id}/relationships")
async def create_relationship(
    doc_id: str,
    body: RelationshipCreate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    rel = DocumentRelationship(
        source_doc_id=uuid.UUID(doc_id),
        target_doc_id=uuid.UUID(body.target_doc_id),
        relationship_type=body.relationship_type,
        notes=body.notes,
    )
    db.add(rel)

    return {"status": "created", "id": str(rel.id)}
