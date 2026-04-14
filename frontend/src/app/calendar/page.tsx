"use client";

import { useCalendar, type CalendarFilter } from "@/hooks/use-calendar";
import type { CalendarEvent } from "@/lib/types";

const FILTER_OPTIONS: { key: CalendarFilter; label: string }[] = [
  { key: "all", label: "Tất cả" },
  { key: "thue", label: "Thuế" },
  { key: "bhxh", label: "BHXH" },
  { key: "bao_cao", label: "Báo cáo" },
];

const CATEGORY_STYLES: Record<string, string> = {
  thue: "bg-blue-50 text-blue-700 border-blue-200",
  bhxh: "bg-green-50 text-green-700 border-green-200",
  bao_cao: "bg-purple-50 text-purple-700 border-purple-200",
};

const CATEGORY_LABELS: Record<string, string> = {
  thue: "Thuế",
  bhxh: "BHXH",
  bao_cao: "Báo cáo",
};

const MONTH_NAMES = [
  "Tháng 1", "Tháng 2", "Tháng 3", "Tháng 4",
  "Tháng 5", "Tháng 6", "Tháng 7", "Tháng 8",
  "Tháng 9", "Tháng 10", "Tháng 11", "Tháng 12",
];

function EventCard({ event }: { event: CalendarEvent }) {
  const style = CATEGORY_STYLES[event.category] || "bg-gray-50 text-gray-700 border-gray-200";
  const d = new Date(event.date_str + "T00:00:00");
  const dayStr = d.toLocaleDateString("vi-VN", { weekday: "short", day: "numeric", month: "numeric" });

  return (
    <div className={`border rounded-lg p-3 ${event.is_overdue ? "border-red-300 bg-red-50" : "border-gray-200 bg-white"}`}>
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="text-sm font-medium text-gray-900">{event.title}</p>
          <p className="text-xs text-gray-500 mt-0.5">{event.description}</p>
        </div>
        <div className="flex flex-col items-end gap-1 flex-shrink-0">
          <span className="text-xs font-medium text-gray-600">{dayStr}</span>
          <span className={`px-1.5 py-0.5 rounded text-[10px] border ${style}`}>
            {CATEGORY_LABELS[event.category] || event.category}
          </span>
          {event.is_overdue && (
            <span className="px-1.5 py-0.5 rounded text-[10px] bg-red-100 text-red-700">
              Quá hạn
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

export default function CalendarPage() {
  const cal = useCalendar();

  return (
    <div className="h-full overflow-y-auto">
      <div className="p-4 md:p-6 max-w-3xl mx-auto">
        <h1 className="text-lg font-bold text-gray-900">Lịch tuân thủ</h1>
        <p className="text-sm text-gray-500 mt-1">
          Theo dõi các hạn nộp thuế, BHXH và báo cáo
        </p>

        {/* Upcoming deadlines */}
        {cal.upcoming.length > 0 && (
          <div className="mt-4 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <h2 className="text-sm font-semibold text-yellow-800 mb-2">
              Sắp đến hạn (14 ngày tới)
            </h2>
            <div className="space-y-2">
              {cal.upcoming.map((event, i) => (
                <EventCard key={`upcoming-${i}`} event={event} />
              ))}
            </div>
          </div>
        )}

        {/* Month navigation */}
        <div className="flex items-center justify-between mt-6 mb-3">
          <button
            onClick={cal.prevMonth}
            className="px-3 py-1.5 text-sm text-gray-600 hover:text-gray-900 border border-gray-300 rounded-md hover:bg-gray-50"
          >
            Trước
          </button>
          <h2 className="text-base font-semibold text-gray-900">
            {MONTH_NAMES[cal.month - 1]} {cal.year}
          </h2>
          <button
            onClick={cal.nextMonth}
            className="px-3 py-1.5 text-sm text-gray-600 hover:text-gray-900 border border-gray-300 rounded-md hover:bg-gray-50"
          >
            Sau
          </button>
        </div>

        {/* Filter */}
        <div className="flex gap-1 bg-gray-100 rounded-lg p-1 mb-4">
          {FILTER_OPTIONS.map((f) => (
            <button
              key={f.key}
              onClick={() => cal.setFilter(f.key)}
              className={`flex-1 px-2 py-1.5 text-xs rounded-md transition-colors ${
                cal.filter === f.key
                  ? "bg-white text-brand-700 font-medium shadow-sm"
                  : "text-gray-600 hover:text-gray-900"
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>

        {/* Events timeline */}
        {cal.loading ? (
          <p className="text-sm text-gray-400 text-center py-8">Đang tải...</p>
        ) : cal.events.length === 0 ? (
          <p className="text-sm text-gray-400 text-center py-8">
            Không có sự kiện nào trong tháng này
          </p>
        ) : (
          <div className="space-y-2">
            {cal.events.map((event, i) => (
              <EventCard key={`event-${i}`} event={event} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
