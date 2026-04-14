"""Audit logging utility — records user actions for compliance."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.audit_log import AuditLog


async def log_action(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID | None = None,
    action: str,
    resource_type: str,
    resource_id: uuid.UUID | None = None,
    details: dict | None = None,
    ip_address: str = "",
) -> None:
    """Create an AuditLog row in the current DB session.

    Actions:  login | create | update | delete | ingest | export | query
    Resource: user | document | contract | chat | compliance | risk_review
    """
    entry = AuditLog(
        tenant_id=tenant_id,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details or {},
        ip_address=ip_address,
    )
    db.add(entry)
