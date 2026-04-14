"use client";

import { useRef } from "react";
import { useComplianceCheck } from "@/hooks/use-compliance-check";
import type { GapItem } from "@/lib/types";

const STATUS_STYLES: Record<string, string> = {
  dat: "bg-green-100 text-green-800 border-green-200",
  khong_dat: "bg-red-100 text-red-800 border-red-200",
  khong_ro: "bg-yellow-100 text-yellow-800 border-yellow-200",
};

const STATUS_LABELS: Record<string, string> = {
  dat: "Đạt",
  khong_dat: "Không đạt",
  khong_ro: "Không rõ",
};

function GapItemCard({ item }: { item: GapItem }) {
  const style = STATUS_STYLES[item.status] || STATUS_STYLES.khong_dat;

  return (
    <div className={`border rounded-lg p-3 ${item.status === "khong_dat" ? "border-red-200" : "border-gray-200"} bg-white`}>
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="text-sm font-medium text-gray-900">{item.title_vi}</p>
          <p className="text-xs text-gray-500 mt-0.5">{item.legal_basis}</p>
        </div>
        <span className={`px-2 py-0.5 rounded text-xs font-medium flex-shrink-0 border ${style}`}>
          {STATUS_LABELS[item.status] || item.status}
        </span>
      </div>
      {item.matched_section && (
        <p className="text-xs text-gray-500 mt-2 italic line-clamp-2">
          &quot;{item.matched_section}&quot;
        </p>
      )}
      {item.suggestion_vi && (
        <p className="text-xs text-red-600 mt-1">{item.suggestion_vi}</p>
      )}
    </div>
  );
}

export default function ComplianceCheckPage() {
  const check = useComplianceCheck();
  const fileRef = useRef<HTMLInputElement>(null);

  return (
    <div className="h-full overflow-y-auto">
      <div className="p-4 md:p-6 max-w-3xl mx-auto">
        <h1 className="text-lg font-bold text-gray-900">Kiểm tra tuân thủ</h1>
        <p className="text-sm text-gray-500 mt-1">
          Upload văn bản nội bộ để kiểm tra đầy đủ nội dung theo quy định pháp luật
        </p>

        {/* Upload + config */}
        <div className="mt-4 bg-white border border-gray-200 rounded-lg p-4 space-y-3">
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">
              Loại văn bản cần kiểm tra
            </label>
            <select
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-brand-500"
              value={check.selectedType}
              onChange={(e) => check.setSelectedType(e.target.value)}
              disabled={check.loadingChecklists}
            >
              {check.checklists.map((cl) => (
                <option key={cl.key} value={cl.key}>
                  {cl.label} ({cl.items_count} nội dung)
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">
              Upload file (.txt, .html)
            </label>
            <input
              ref={fileRef}
              type="file"
              accept=".txt,.html,.htm"
              onChange={(e) => check.setFile(e.target.files?.[0] || null)}
              className="w-full text-sm text-gray-500 file:mr-3 file:py-1.5 file:px-3 file:rounded-md file:border-0 file:text-sm file:bg-brand-50 file:text-brand-700 hover:file:bg-brand-100"
            />
          </div>

          <button
            onClick={check.analyze}
            disabled={check.loading || !check.file}
            className="w-full px-4 py-2 bg-brand-600 text-white rounded-md text-sm font-medium hover:bg-brand-700 disabled:opacity-50"
          >
            {check.loading ? "Đang phân tích..." : "Kiểm tra"}
          </button>

          {check.error && (
            <p className="text-xs text-red-600">{check.error}</p>
          )}
        </div>

        {/* Results */}
        {check.report && (
          <div className="mt-4 space-y-4">
            {/* Score summary */}
            <div className="bg-white border border-gray-200 rounded-lg p-4 text-center">
              <div className={`inline-block text-3xl font-bold ${
                check.report.coverage_pct >= 80
                  ? "text-green-600"
                  : check.report.coverage_pct >= 50
                    ? "text-yellow-600"
                    : "text-red-600"
              }`}>
                {check.report.dat_count}/{check.report.total_items}
              </div>
              <p className="text-sm text-gray-600 mt-1">
                nội dung bắt buộc đạt yêu cầu ({check.report.coverage_pct}%)
              </p>
              <div className="flex justify-center gap-4 mt-3 text-xs">
                <span className="text-green-700">
                  {check.report.dat_count} đạt
                </span>
                <span className="text-red-700">
                  {check.report.khong_dat_count} không đạt
                </span>
                {check.report.khong_ro_count > 0 && (
                  <span className="text-yellow-700">
                    {check.report.khong_ro_count} không rõ
                  </span>
                )}
              </div>
            </div>

            {/* Item list */}
            <div className="space-y-2">
              {check.report.items.map((item) => (
                <GapItemCard key={item.checklist_item_id} item={item} />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
