"use client";

import type { ComplianceIssue, ComplianceResult } from "@/lib/types";

function IssueLine({ issue }: { issue: ComplianceIssue }) {
  const bg =
    issue.level === "error"
      ? "bg-red-50 text-red-800 border-red-200"
      : issue.level === "warning"
        ? "bg-yellow-50 text-yellow-800 border-yellow-200"
        : "bg-blue-50 text-blue-800 border-blue-200";

  const levelLabel =
    issue.level === "error"
      ? "Loi"
      : issue.level === "warning"
        ? "Canh bao"
        : "Thong tin";

  return (
    <div className={`text-xs p-2 rounded border ${bg}`}>
      <span className="font-semibold">[{levelLabel}]</span>{" "}
      {issue.message_vi}
      {issue.legal_basis && (
        <span className="text-[10px] ml-1 opacity-75">
          ({issue.legal_basis})
        </span>
      )}
      {issue.suggested_value && (
        <span className="block mt-0.5 text-[10px] opacity-75">
          Gia tri de xuat: {issue.suggested_value}
        </span>
      )}
    </div>
  );
}

export function ComplianceBadge({
  compliance,
}: {
  compliance: ComplianceResult | null;
}) {
  if (!compliance) return null;

  const errors = compliance.issues.filter((i) => i.level === "error");
  const warnings = compliance.issues.filter((i) => i.level === "warning");

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <span
          className={`text-xs font-semibold px-2 py-0.5 rounded ${
            compliance.is_compliant
              ? "bg-green-100 text-green-800"
              : "bg-red-100 text-red-800"
          }`}
        >
          {compliance.is_compliant ? "Dat" : "Khong dat"}
        </span>
        {errors.length > 0 && (
          <span className="text-xs text-red-600">
            {errors.length} loi
          </span>
        )}
        {warnings.length > 0 && (
          <span className="text-xs text-yellow-600">
            {warnings.length} canh bao
          </span>
        )}
      </div>
      {compliance.issues.length > 0 && (
        <div className="space-y-1">
          {compliance.issues.map((issue, i) => (
            <IssueLine key={`${issue.rule_id}-${issue.field}-${i}`} issue={issue} />
          ))}
        </div>
      )}
    </div>
  );
}
