"""Compliance calendar API routes."""

from __future__ import annotations

from dataclasses import asdict
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from src.auth.dependencies import get_current_user
from src.core.gate import require_feature
from src.calendar.deadline_rules import generate_calendar, get_upcoming
from src.db.models.user import User

router = APIRouter(prefix="/api/calendar", tags=["calendar"])


@router.get("/events")
async def calendar_events(
    _current_user: Annotated[User, Depends(require_feature("calendar"))],
    year: int = Query(default_factory=lambda: date.today().year),
    month: int = Query(default_factory=lambda: date.today().month),
) -> list[dict]:
    events = generate_calendar(year, month)
    return [asdict(e) for e in events]


@router.get("/upcoming")
async def upcoming_deadlines(
    _current_user: Annotated[User, Depends(require_feature("calendar"))],
    days: int = Query(default=7, ge=1, le=90),
) -> list[dict]:
    events = get_upcoming(days)
    return [asdict(e) for e in events]
