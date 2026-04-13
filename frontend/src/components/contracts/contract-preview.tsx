"use client";

import type { ComplianceResult } from "@/lib/types";
import { getExportUrl } from "@/lib/api-client";
import { ComplianceBadge } from "./compliance-badge";

export function ContractPreview({
  contractId,
  title,
  status,
  renderedContent,
  compliance,
}: {
  contractId: string;
  title: string;
  status: string;
  renderedContent: string;
  compliance: ComplianceResult | null;
}) {
  const statusLabel =
    status === "draft"
      ? "Ban nhap"
      : status === "review"
        ? "Dang duyet"
        : "Hoan thanh";

  const statusColor =
    status === "final"
      ? "bg-green-100 text-green-800"
      : status === "review"
        ? "bg-yellow-100 text-yellow-800"
        : "bg-gray-100 text-gray-700";

  return (
    <div className="max-w-3xl mx-auto">
      {/* Pinned summary + actions */}
      <div className="sticky top-0 z-10 bg-white border border-gray-200 rounded-lg p-4 mb-4 shadow-sm">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <h2 className="text-base font-bold text-gray-900 truncate">
              {title}
            </h2>
            <div className="flex items-center gap-2 mt-1">
              <span
                className={`text-xs font-medium px-2 py-0.5 rounded ${statusColor}`}
              >
                {statusLabel}
              </span>
              {compliance && (
                <span
                  className={`text-xs font-medium px-2 py-0.5 rounded ${
                    compliance.is_compliant
                      ? "bg-green-100 text-green-800"
                      : "bg-red-100 text-red-800"
                  }`}
                >
                  {compliance.is_compliant ? "Dat" : "Khong dat"}
                </span>
              )}
            </div>
          </div>
          <div className="flex gap-2 flex-shrink-0">
            <a
              href={getExportUrl(contractId, "docx")}
              className="px-3 py-1.5 text-xs rounded-md border border-gray-300 text-gray-700 hover:bg-gray-50"
            >
              Tai DOCX
            </a>
            <a
              href={getExportUrl(contractId, "pdf")}
              className="px-3 py-1.5 text-xs rounded-md bg-brand-500 text-white hover:bg-brand-600"
            >
              Tai PDF
            </a>
          </div>
        </div>

        {compliance && compliance.issues.length > 0 && (
          <details className="mt-3">
            <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-700">
              Ket qua kiem tra ({compliance.issues.length} van de)
            </summary>
            <div className="mt-2">
              <ComplianceBadge compliance={compliance} />
            </div>
          </details>
        )}
      </div>

      {/* Contract body */}
      <div className="bg-white border border-gray-200 rounded-lg p-6 md:p-8">
        <div
          className="whitespace-pre-wrap text-sm leading-relaxed text-gray-800"
          style={{ fontFamily: '"Times New Roman", Times, serif' }}
        >
          {renderedContent}
        </div>
      </div>
    </div>
  );
}
