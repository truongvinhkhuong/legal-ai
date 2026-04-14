"use client";

import { useRiskReview } from "@/hooks/use-risk-review";
import type { RiskIssue } from "@/lib/types";

const CATEGORY_LABELS: Record<string, string> = {
  vi_pham: "Vi phạm",
  thieu: "Thiếu",
  bat_loi: "Bất lợi",
};

const SEVERITY_STYLES: Record<string, string> = {
  high: "bg-red-100 text-red-800 border-red-200",
  medium: "bg-yellow-100 text-yellow-800 border-yellow-200",
  low: "bg-blue-100 text-blue-800 border-blue-200",
};

const SEVERITY_LABELS: Record<string, string> = {
  high: "Nghiêm trọng",
  medium: "Trung bình",
  low: "Thấp",
};

function RiskIssueCard({ issue }: { issue: RiskIssue }) {
  const sevStyle = SEVERITY_STYLES[issue.severity] || SEVERITY_STYLES.medium;

  return (
    <details className="border border-gray-200 rounded-lg bg-white group">
      <summary className="p-3 cursor-pointer list-none flex items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium text-gray-500">
              {CATEGORY_LABELS[issue.category] || issue.category}
            </span>
            <span className={`px-1.5 py-0.5 rounded text-[10px] border ${sevStyle}`}>
              {SEVERITY_LABELS[issue.severity] || issue.severity}
            </span>
          </div>
          <p className="text-sm font-medium text-gray-900 mt-1">{issue.title_vi}</p>
        </div>
      </summary>
      <div className="px-3 pb-3 space-y-2">
        <p className="text-xs text-gray-600">{issue.description_vi}</p>
        {issue.matched_clause && (
          <p className="text-xs text-gray-500 italic">
            &quot;{issue.matched_clause}&quot;
          </p>
        )}
        <div className="flex items-center gap-3 text-xs">
          {issue.legal_basis && (
            <span className="text-gray-400">{issue.legal_basis}</span>
          )}
        </div>
        {issue.suggestion_vi && (
          <p className="text-xs text-brand-700 font-medium">{issue.suggestion_vi}</p>
        )}
      </div>
    </details>
  );
}

export default function ContractReviewPage() {
  const review = useRiskReview();

  const scoreColor =
    review.report && review.report.risk_score >= 8
      ? "text-green-600"
      : review.report && review.report.risk_score >= 5
        ? "text-yellow-600"
        : "text-red-600";

  return (
    <div className="h-full overflow-y-auto">
      <div className="p-4 md:p-6 max-w-3xl mx-auto">
        <h1 className="text-lg font-bold text-gray-900">Kiểm tra hợp đồng</h1>
        <p className="text-sm text-gray-500 mt-1">
          Upload hợp đồng để phát hiện rủi ro pháp lý
        </p>

        {/* Upload + config */}
        <div className="mt-4 bg-white border border-gray-200 rounded-lg p-4 space-y-3">
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">
              Loại hợp đồng
            </label>
            <select
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-brand-500"
              value={review.selectedType}
              onChange={(e) => review.setSelectedType(e.target.value)}
              disabled={review.loadingTypes}
            >
              {review.contractTypes.map((ct) => (
                <option key={ct.key} value={ct.key}>
                  {ct.label} ({ct.rules_count} quy tắc)
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">
              Upload hợp đồng (.txt, .html)
            </label>
            <input
              type="file"
              accept=".txt,.html,.htm"
              onChange={(e) => review.setFile(e.target.files?.[0] || null)}
              className="w-full text-sm text-gray-500 file:mr-3 file:py-1.5 file:px-3 file:rounded-md file:border-0 file:text-sm file:bg-brand-50 file:text-brand-700 hover:file:bg-brand-100"
            />
          </div>

          <button
            onClick={review.analyze}
            disabled={review.loading || !review.file}
            className="w-full px-4 py-2 bg-brand-600 text-white rounded-md text-sm font-medium hover:bg-brand-700 disabled:opacity-50"
          >
            {review.loading ? (review.progress || "Đang phân tích...") : "Phân tích rủi ro"}
          </button>

          {review.error && (
            <p className="text-xs text-red-600">{review.error}</p>
          )}
        </div>

        {/* Results */}
        {review.report && (
          <div className="mt-4 space-y-4">
            {/* Score badge */}
            <div className="bg-white border border-gray-200 rounded-lg p-6 text-center">
              <p className="text-sm text-gray-500 mb-1">Điểm an toàn</p>
              <div className={`text-5xl font-bold ${scoreColor}`}>
                {review.report.risk_score}/10
              </div>
              <p className="text-sm text-gray-600 mt-3">{review.report.summary_vi}</p>
              <div className="flex justify-center gap-4 mt-3 text-xs">
                {review.report.high_count > 0 && (
                  <span className="text-red-700">{review.report.high_count} nghiêm trọng</span>
                )}
                {review.report.medium_count > 0 && (
                  <span className="text-yellow-700">{review.report.medium_count} trung bình</span>
                )}
                {review.report.low_count > 0 && (
                  <span className="text-blue-700">{review.report.low_count} thấp</span>
                )}
              </div>
            </div>

            {/* Issues grouped by category */}
            {review.report.issues.length > 0 && (
              <div className="space-y-2">
                <h3 className="text-sm font-semibold text-gray-700">
                  Chi tiết ({review.report.issues_count} vấn đề)
                </h3>
                {review.report.issues.map((issue) => (
                  <RiskIssueCard key={issue.rule_id} issue={issue} />
                ))}
              </div>
            )}

            {review.report.issues.length === 0 && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-center">
                <p className="text-sm text-green-800 font-medium">
                  Không phát hiện vấn đề rủi ro nào
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
