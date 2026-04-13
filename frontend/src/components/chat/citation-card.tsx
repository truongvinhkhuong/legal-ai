import type { LegalCitation } from "@/lib/types";

interface Props {
  citation: LegalCitation;
}

export function CitationCard({ citation }: Props) {
  const statusStyles: Record<string, string> = {
    hieu_luc: "border-green-200 bg-green-50",
    het_hieu_luc: "border-red-200 bg-red-50",
    da_sua_doi: "border-yellow-200 bg-yellow-50",
  };

  const statusLabels: Record<string, string> = {
    hieu_luc: "Con hieu luc",
    het_hieu_luc: "Het hieu luc",
    da_sua_doi: "Da sua doi",
  };

  const borderStyle = statusStyles[citation.validity_status] || "border-gray-200 bg-gray-50";

  return (
    <details className={`border rounded-md text-xs ${borderStyle} group`}>
      <summary className="px-3 py-2 cursor-pointer list-none flex items-start justify-between">
        <div className="min-w-0">
          <span className="font-medium text-gray-700">
            {citation.doc_number}
          </span>
          {citation.article && (
            <span className="ml-2 text-gray-500">
              {citation.article}
              {citation.clause && `, ${citation.clause}`}
              {citation.point && `, ${citation.point}`}
            </span>
          )}
        </div>
        <span
          className={`px-1.5 py-0.5 rounded text-[10px] flex-shrink-0 ml-2 ${
            citation.validity_status === "hieu_luc"
              ? "bg-green-100 text-green-700"
              : citation.validity_status === "het_hieu_luc"
              ? "bg-red-100 text-red-700"
              : "bg-yellow-100 text-yellow-700"
          }`}
        >
          {statusLabels[citation.validity_status] || citation.validity_status}
        </span>
      </summary>

      <div className="px-3 pb-2">
        {citation.exact_quote && (
          <p className="text-gray-600 italic line-clamp-3">
            &quot;{citation.exact_quote}&quot;
          </p>
        )}

        <div className="mt-1 text-gray-400">
          {citation.hierarchy_path}
          {citation.is_cross_reference && " (tham chieu cheo)"}
        </div>
      </div>
    </details>
  );
}
