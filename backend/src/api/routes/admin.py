"""Admin endpoints: document management, user management, audit logs."""

from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_user, require_role
from src.config.database import get_db
from src.core.audit import log_action
from src.db.models.audit_log import AuditLog
from src.db.models.contract import Contract
from src.db.models.document import Document, DocumentRelationship
from src.db.models.usage import UsageRecord
from src.db.models.user import User
from src.retrieval.hierarchical_retriever import delete_chunks_by_doc_id

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


class UserListItem(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    departments: list[str]
    is_active: bool
    created_at: str


class UserUpdate(BaseModel):
    full_name: str | None = None
    role: str | None = None
    departments: list[str] | None = None


# ---------------------------------------------------------------------------
# Document CRUD
# ---------------------------------------------------------------------------

@router.get("/documents")
async def list_documents(
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
    doc_type: str | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    query = (
        select(Document)
        .where(Document.tenant_id == current_user.tenant_id)
        .order_by(Document.created_at.desc())
    )

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
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> dict:
    doc = await db.get(Document, uuid.UUID(doc_id))
    if not doc or doc.tenant_id != current_user.tenant_id:
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
    current_user: Annotated[User, Depends(require_role(["admin", "editor"]))],
    db: AsyncSession = Depends(get_db),
) -> dict:
    doc = await db.get(Document, uuid.UUID(doc_id))
    if not doc or doc.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="Document not found")

    update_data = update.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(doc, field, value)

    await log_action(
        db, tenant_id=current_user.tenant_id, user_id=current_user.id,
        action="update", resource_type="document", resource_id=doc.id,
        details={"fields": list(update_data.keys())},
    )

    return {"status": "updated", "id": doc_id}


@router.delete("/documents/{doc_id}")
async def delete_document(
    doc_id: str,
    current_user: Annotated[User, Depends(require_role(["admin"]))],
    db: AsyncSession = Depends(get_db),
) -> dict:
    doc = await db.get(Document, uuid.UUID(doc_id))
    if not doc or doc.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete chunks from Qdrant first, then remove DB row
    await delete_chunks_by_doc_id(str(doc.id))

    await log_action(
        db, tenant_id=current_user.tenant_id, user_id=current_user.id,
        action="delete", resource_type="document", resource_id=doc.id,
        details={"doc_title": doc.doc_title},
    )

    await db.delete(doc)

    return {"status": "deleted", "id": doc_id}


# ---------------------------------------------------------------------------
# Document relationships
# ---------------------------------------------------------------------------

@router.post("/documents/{doc_id}/relationships")
async def create_relationship(
    doc_id: str,
    body: RelationshipCreate,
    current_user: Annotated[User, Depends(require_role(["admin", "editor"]))],
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


# ---------------------------------------------------------------------------
# User management (admin only)
# ---------------------------------------------------------------------------

@router.get("/users")
async def list_users(
    current_user: Annotated[User, Depends(require_role(["admin"]))],
    db: AsyncSession = Depends(get_db),
) -> list[UserListItem]:
    """List all users in the current tenant."""
    result = await db.execute(
        select(User)
        .where(User.tenant_id == current_user.tenant_id)
        .order_by(User.created_at.desc())
    )
    users = result.scalars().all()
    return [
        UserListItem(
            id=str(u.id),
            email=u.email,
            full_name=u.full_name,
            role=u.role,
            departments=u.departments or [],
            is_active=u.is_active,
            created_at=u.created_at.isoformat(),
        )
        for u in users
    ]


@router.patch("/users/{user_id}")
async def update_user(
    user_id: str,
    update: UserUpdate,
    current_user: Annotated[User, Depends(require_role(["admin"]))],
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Update user role, name, or departments."""
    user = await db.get(User, uuid.UUID(user_id))
    if not user or user.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = update.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    await log_action(
        db, tenant_id=current_user.tenant_id, user_id=current_user.id,
        action="update", resource_type="user", resource_id=user.id,
        details={"fields": list(update_data.keys())},
    )

    return {"status": "updated", "id": user_id}


@router.post("/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: str,
    current_user: Annotated[User, Depends(require_role(["admin"]))],
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Deactivate a user (prevents login)."""
    user = await db.get(User, uuid.UUID(user_id))
    if not user or user.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")

    user.is_active = False

    await log_action(
        db, tenant_id=current_user.tenant_id, user_id=current_user.id,
        action="update", resource_type="user", resource_id=user.id,
        details={"action": "deactivate"},
    )

    return {"status": "deactivated", "id": user_id}


@router.post("/users/{user_id}/reactivate")
async def reactivate_user(
    user_id: str,
    current_user: Annotated[User, Depends(require_role(["admin"]))],
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Reactivate a previously deactivated user."""
    user = await db.get(User, uuid.UUID(user_id))
    if not user or user.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = True

    await log_action(
        db, tenant_id=current_user.tenant_id, user_id=current_user.id,
        action="update", resource_type="user", resource_id=user.id,
        details={"action": "reactivate"},
    )

    return {"status": "reactivated", "id": user_id}


# ---------------------------------------------------------------------------
# Audit logs (admin only)
# ---------------------------------------------------------------------------

@router.get("/audit-logs")
async def list_audit_logs(
    current_user: Annotated[User, Depends(require_role(["admin"]))],
    db: AsyncSession = Depends(get_db),
    action: str | None = None,
    resource_type: str | None = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
) -> dict[str, Any]:
    """List audit logs for the current tenant."""
    query = (
        select(AuditLog)
        .where(AuditLog.tenant_id == current_user.tenant_id)
        .order_by(AuditLog.created_at.desc())
    )

    if action:
        query = query.where(AuditLog.action == action)
    if resource_type:
        query = query.where(AuditLog.resource_type == resource_type)

    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    logs = result.scalars().all()

    return {
        "items": [
            {
                "id": str(log.id),
                "user_id": str(log.user_id) if log.user_id else None,
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": str(log.resource_id) if log.resource_id else None,
                "details": log.details,
                "ip_address": log.ip_address,
                "created_at": log.created_at.isoformat(),
            }
            for log in logs
        ],
        "total": len(logs),
    }


# ---------------------------------------------------------------------------
# Admin dashboard stats
# ---------------------------------------------------------------------------

@router.get("/stats")
async def get_stats(
    current_user: Annotated[User, Depends(require_role(["admin"]))],
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Tenant usage summary for admin dashboard."""
    tid = current_user.tenant_id

    # Count users
    user_count = (await db.execute(
        select(func.count(User.id)).where(User.tenant_id == tid)
    )).scalar_one()

    # Count documents
    doc_count = (await db.execute(
        select(func.count(Document.id)).where(Document.tenant_id == tid)
    )).scalar_one()

    # Count contracts
    contract_count = (await db.execute(
        select(func.count(Contract.id)).where(Contract.tenant_id == tid)
    )).scalar_one()

    # Monthly usage per feature
    from datetime import datetime
    now = datetime.now()
    usage_result = await db.execute(
        select(UsageRecord.action, UsageRecord.count).where(
            UsageRecord.tenant_id == tid,
            UsageRecord.period_year == now.year,
            UsageRecord.period_month == now.month,
        )
    )
    usage = {row.action: row.count for row in usage_result}

    return {
        "user_count": user_count,
        "doc_count": doc_count,
        "contract_count": contract_count,
        "monthly_usage": usage,
    }
