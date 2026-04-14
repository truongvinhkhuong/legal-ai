"""Feature gate — FastAPI dependency that checks plan limits."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_user
from src.config.database import get_db
from src.core.plan_limits import PLAN_LIMITS
from src.core.usage_tracker import get_usage
from src.db.models.tenant import Tenant
from src.db.models.user import User


def require_feature(feature: str):
    """Return a FastAPI dependency that checks if the tenant's plan allows the feature.

    - Returns 403 if the feature is disabled for the plan.
    - Returns 429 if the monthly quota is exceeded.
    """

    async def _check(
        current_user: Annotated[User, Depends(get_current_user)],
        db: Annotated[AsyncSession, Depends(get_db)],
    ) -> User:
        # Load tenant to get plan
        result = await db.execute(
            select(Tenant.plan).where(Tenant.id == current_user.tenant_id)
        )
        plan = result.scalar_one_or_none() or "free"

        limits = PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])
        limit_value = limits.get(feature)

        # Feature disabled
        if limit_value is False:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Gói {plan} không bao gồm tính năng này. Vui lòng nâng cấp.",
            )

        # Feature enabled with no monthly limit
        if limit_value is True or limit_value == -1:
            return current_user

        # Feature with monthly quota
        current_usage = await get_usage(db, current_user.tenant_id, feature)
        if current_usage >= limit_value:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=(
                    f"Đã đạt giới hạn {limit_value} lượt/tháng cho tính năng này. "
                    f"Vui lòng nâng cấp gói để tiếp tục."
                ),
            )

        return current_user

    return _check
