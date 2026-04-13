"use client";

import { useEffect, useState } from "react";
import { DocumentUpload } from "@/components/admin/document-upload";
import type { DocumentListItem } from "@/lib/types";

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<DocumentListItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/admin/documents")
      .then((r) => r.json())
      .then((data) => {
        setDocuments(data.items || []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  return (
    <div className="h-full flex flex-col">
      <header className="px-6 py-3 border-b border-gray-200 bg-white flex justify-between items-center">
        <div>
          <h2 className="text-lg font-semibold">Quan ly Van ban</h2>
          <p className="text-sm text-gray-500">{documents.length} van ban</p>
        </div>
        <DocumentUpload onSuccess={() => window.location.reload()} />
      </header>

      <div className="flex-1 overflow-auto p-6">
        {loading ? (
          <p className="text-gray-500">Dang tai...</p>
        ) : documents.length === 0 ? (
          <div className="text-center py-12 text-gray-400">
            <p>Chua co van ban nao. Upload van ban dau tien.</p>
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-500 border-b">
                <th className="pb-2 font-medium">So hieu</th>
                <th className="pb-2 font-medium">Tieu de</th>
                <th className="pb-2 font-medium">Loai</th>
                <th className="pb-2 font-medium">Trang thai</th>
                <th className="pb-2 font-medium">Chunks</th>
              </tr>
            </thead>
            <tbody>
              {documents.map((doc) => (
                <tr key={doc.id} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="py-2 font-mono text-xs">{doc.doc_number}</td>
                  <td className="py-2">{doc.doc_title}</td>
                  <td className="py-2">
                    <span className="px-2 py-0.5 bg-blue-50 text-blue-700 rounded text-xs">
                      {doc.doc_type}
                    </span>
                  </td>
                  <td className="py-2">
                    <StatusBadge status={doc.status} />
                  </td>
                  <td className="py-2 text-gray-500">{doc.chunks_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    hieu_luc: "bg-green-50 text-green-700",
    het_hieu_luc: "bg-red-50 text-red-700",
    da_sua_doi: "bg-yellow-50 text-yellow-700",
  };
  const labels: Record<string, string> = {
    hieu_luc: "Con hieu luc",
    het_hieu_luc: "Het hieu luc",
    da_sua_doi: "Da sua doi",
  };
  return (
    <span className={`px-2 py-0.5 rounded text-xs ${styles[status] || "bg-gray-100"}`}>
      {labels[status] || status}
    </span>
  );
}
