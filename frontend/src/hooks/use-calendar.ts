"use client";

import { useCallback, useEffect, useState } from "react";
import type { CalendarEvent } from "@/lib/types";
import { fetchCalendarEvents, fetchUpcomingDeadlines } from "@/lib/api-client";

export type CalendarFilter = "all" | "thue" | "bhxh" | "bao_cao";

export function useCalendar() {
  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [upcoming, setUpcoming] = useState<CalendarEvent[]>([]);
  const [filter, setFilter] = useState<CalendarFilter>("all");
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [evts, upc] = await Promise.all([
        fetchCalendarEvents(year, month),
        fetchUpcomingDeadlines(14),
      ]);
      setEvents(evts);
      setUpcoming(upc);
    } catch {
      // silently fail
    } finally {
      setLoading(false);
    }
  }, [year, month]);

  useEffect(() => { load(); }, [load]);

  const filteredEvents = filter === "all"
    ? events
    : events.filter((e) => e.category === filter);

  const filteredUpcoming = filter === "all"
    ? upcoming
    : upcoming.filter((e) => e.category === filter);

  function prevMonth() {
    if (month === 1) { setMonth(12); setYear(year - 1); }
    else { setMonth(month - 1); }
  }

  function nextMonth() {
    if (month === 12) { setMonth(1); setYear(year + 1); }
    else { setMonth(month + 1); }
  }

  return {
    year, month, prevMonth, nextMonth,
    events: filteredEvents,
    upcoming: filteredUpcoming,
    filter, setFilter,
    loading,
  };
}
