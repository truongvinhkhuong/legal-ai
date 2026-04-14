"""Hard-coded compliance deadlines for Vietnamese SMEs.

All deadlines are deterministic — no LLM involved.
"""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date


@dataclass
class CalendarEvent:
    date_str: str          # YYYY-MM-DD
    title: str
    description: str
    category: str          # "thue" | "bhxh" | "bao_cao"
    is_overdue: bool = False


# ---------------------------------------------------------------------------
# Monthly deadlines (apply every month)
# ---------------------------------------------------------------------------

def _monthly_deadlines(year: int, month: int, today: date) -> list[CalendarEvent]:
    """Generate monthly recurring deadlines."""
    events: list[CalendarEvent] = []

    # Previous period labels
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1

    # BHXH — due 20th every month (for previous month)
    d20 = date(year, month, 20)
    events.append(CalendarEvent(
        date_str=d20.isoformat(),
        title=f"Nộp BHXH/BHYT/BHTN tháng {prev_month:02d}/{prev_year}",
        description="Nộp tiền BHXH, BHYT, BHTN cho cơ quan BHXH",
        category="bhxh",
        is_overdue=d20 < today,
    ))

    # VAT monthly — due 20th (for previous month)
    events.append(CalendarEvent(
        date_str=d20.isoformat(),
        title=f"Nộp tờ khai & thuế GTGT tháng {prev_month:02d}",
        description="Nộp tờ khai thuế GTGT tháng trước (áp dụng kê khai theo tháng)",
        category="thue",
        is_overdue=d20 < today,
    ))

    # TNCN withholding — due 20th (for previous month)
    events.append(CalendarEvent(
        date_str=d20.isoformat(),
        title=f"Nộp thuế TNCN khấu trừ tháng {prev_month:02d}",
        description="Nộp thuế TNCN đã khấu trừ từ tiền lương tháng trước",
        category="thue",
        is_overdue=d20 < today,
    ))

    return events


# ---------------------------------------------------------------------------
# Quarterly deadlines
# ---------------------------------------------------------------------------

def _quarterly_deadlines(year: int, month: int, today: date) -> list[CalendarEvent]:
    """Generate quarterly deadlines (only in months following quarter end)."""
    events: list[CalendarEvent] = []

    # Quarterly VAT — due 30th of first month after quarter
    # Q1 (Jan-Mar) → due Apr 30, Q2 → Jul 30, Q3 → Oct 30, Q4 → Jan 30 next year
    if month in (1, 4, 7, 10):
        prev_quarter = (month - 1) // 3 if month > 1 else 4
        pq_year = year if month > 1 else year - 1
        last_day = min(30, calendar.monthrange(year, month)[1])
        d30 = date(year, month, last_day)

        events.append(CalendarEvent(
            date_str=d30.isoformat(),
            title=f"Nộp tờ khai & thuế GTGT quý {prev_quarter}/{pq_year}",
            description="Nộp tờ khai thuế GTGT quý trước (áp dụng kê khai theo quý)",
            category="thue",
            is_overdue=d30 < today,
        ))

        # Tam nop TNDN quy
        events.append(CalendarEvent(
            date_str=d30.isoformat(),
            title=f"Tạm nộp thuế TNDN quý {prev_quarter}/{pq_year}",
            description="Tạm nộp thuế thu nhập doanh nghiệp quý trước",
            category="thue",
            is_overdue=d30 < today,
        ))

    return events


# ---------------------------------------------------------------------------
# Annual deadlines
# ---------------------------------------------------------------------------

def _annual_deadlines(year: int, month: int, today: date) -> list[CalendarEvent]:
    """Generate annual deadlines."""
    events: list[CalendarEvent] = []

    # TNCN quyet toan — March 31
    if month == 3:
        d_qt = date(year, 3, 31)
        events.append(CalendarEvent(
            date_str=d_qt.isoformat(),
            title=f"Quyết toán thuế TNCN năm {year - 1}",
            description="Hạn cuối nộp tờ khai quyết toán thuế TNCN năm trước",
            category="thue",
            is_overdue=d_qt < today,
        ))

        # BCTC — March 31
        events.append(CalendarEvent(
            date_str=d_qt.isoformat(),
            title=f"Nộp báo cáo tài chính năm {year - 1}",
            description="Hạn cuối nộp báo cáo tài chính năm trước cho doanh nghiệp",
            category="bao_cao",
            is_overdue=d_qt < today,
        ))

        # Quyet toan TNDN — March 31
        events.append(CalendarEvent(
            date_str=d_qt.isoformat(),
            title=f"Quyết toán thuế TNDN năm {year - 1}",
            description="Hạn cuối quyết toán thuế thu nhập doanh nghiệp năm trước",
            category="thue",
            is_overdue=d_qt < today,
        ))

    return events


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_calendar(year: int, month: int) -> list[CalendarEvent]:
    """Generate all compliance deadlines for a given month."""
    today = date.today()
    events: list[CalendarEvent] = []

    events.extend(_monthly_deadlines(year, month, today))
    events.extend(_quarterly_deadlines(year, month, today))
    events.extend(_annual_deadlines(year, month, today))

    return sorted(events, key=lambda e: e.date_str)


def get_upcoming(days: int = 7) -> list[CalendarEvent]:
    """Return deadlines within the next N days."""
    today = date.today()
    events: list[CalendarEvent] = []

    # Check current month and next month to cover edge cases
    for offset in range(2):
        m = today.month + offset
        y = today.year
        if m > 12:
            m -= 12
            y += 1
        for event in generate_calendar(y, m):
            event_date = date.fromisoformat(event.date_str)
            diff = (event_date - today).days
            if 0 <= diff <= days:
                events.append(event)
            elif diff < 0 and event.is_overdue:
                # Include recent overdue items (up to 7 days past)
                if diff >= -7:
                    events.append(event)

    # Deduplicate by date+title
    seen: set[str] = set()
    unique: list[CalendarEvent] = []
    for e in events:
        key = f"{e.date_str}:{e.title}"
        if key not in seen:
            seen.add(key)
            unique.append(e)

    return sorted(unique, key=lambda e: e.date_str)
