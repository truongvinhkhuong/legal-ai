"""Usage tracking — monthly counters per tenant per feature."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.usage import UsageRecord


async def increment_usage(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    action: str,
) -> int:
    """Increment the monthly usage counter and return the new count."""
    now = datetime.now()
    year, month = now.year, now.month

    result = await db.execute(
        select(UsageRecord).where(
            UsageRecord.tenant_id == tenant_id,
            UsageRecord.action == action,
            UsageRecord.period_year == year,
            UsageRecord.period_month == month,
        )
    )
    record = result.scalar_one_or_none()

    if record:
        record.count += 1
        return record.count

    record = UsageRecord(
        tenant_id=tenant_id,
        action=action,
        period_year=year,
        period_month=month,
        count=1,
    )
    db.add(record)
    await db.flush()
    return 1


async def get_usage(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    action: str,
    year: int | None = None,
    month: int | None = None,
) -> int:
    """Get the current monthly usage count."""
    now = datetime.now()
    year = year or now.year
    month = month or now.month

    result = await db.execute(
        select(UsageRecord.count).where(
            UsageRecord.tenant_id == tenant_id,
            UsageRecord.action == action,
            UsageRecord.period_year == year,
            UsageRecord.period_month == month,
        )
    )
    row = result.scalar_one_or_none()
    return row or 0
