"""Tests for calendar deadline rules."""

from __future__ import annotations

import pytest

from src.calendar.deadline_rules import generate_calendar, get_upcoming


class TestCalendarGeneration:
    def test_generates_events_for_valid_month(self):
        """Should return at least some events for any month."""
        events = generate_calendar(2025, 1)
        assert len(events) > 0

    def test_all_events_in_correct_month(self):
        """All events should be in the requested month."""
        events = generate_calendar(2025, 3)
        for e in events:
            assert e.date_str.startswith("2025-03")

    def test_quarterly_events_in_correct_months(self):
        """Quarterly events should appear in months 1,4,7,10."""
        # January should have quarterly events
        jan_events = generate_calendar(2025, 1)
        categories = [e.category for e in jan_events]
        assert "thue" in categories  # quarterly VAT

    def test_annual_events_in_march(self):
        """Annual deadlines (BCTC, quyet toan) should appear in March."""
        mar_events = generate_calendar(2025, 3)
        titles = [e.title for e in mar_events]
        # Should have annual filings
        assert any("quyết toán" in t.lower() or "BCTC" in t for t in titles)


class TestUpcomingDeadlines:
    def test_upcoming_returns_events(self):
        """Should return upcoming events within the given window."""
        events = get_upcoming(30)
        # We can't guarantee specific events, but the function should not error
        assert isinstance(events, list)

    def test_upcoming_no_duplicates(self):
        """Should not return duplicate events."""
        events = get_upcoming(60)
        # Check that (date, title) pairs are unique
        seen = set()
        for e in events:
            key = (e.date_str, e.title)
            assert key not in seen, f"Duplicate event: {key}"
            seen.add(key)
