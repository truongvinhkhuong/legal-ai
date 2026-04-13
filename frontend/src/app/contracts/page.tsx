"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import type { ContractListItem, TemplateListItem } from "@/lib/types";
import { fetchContracts, fetchTemplates } from "@/lib/api-client";
import { TemplateCard } from "@/components/contracts/template-card";

export default function ContractsPage() {
  const router = useRouter();
  const [templates, setTemplates] = useState<TemplateListItem[]>([]);
  const [contracts, setContracts] = useState<ContractListItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetchTemplates().catch(() => []),
      fetchContracts().catch(() => []),
    ]).then(([t, c]) => {
      setTemplates(t);
      setContracts(c);
      setLoading(false);
    });
  }, []);

  return (
    <div className="h-full overflow-y-auto">
      <div className="p-4 md:p-6 max-w-4xl mx-auto">
        <h1 className="text-lg font-bold text-gray-900">Soan thao hop dong</h1>
        <p className="text-sm text-gray-500 mt-1">
          Chon mau hop dong de bat dau soan thao
        </p>

        {/* Template grid */}
        <section className="mt-6">
          <h2 className="text-sm font-semibold text-gray-700 mb-3">
            Mau hop dong
          </h2>
          {loading ? (
            <p className="text-sm text-gray-400">Dang tai...</p>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {templates.map((t) => (
                <TemplateCard
                  key={t.template_key}
                  template={t}
                  onClick={() =>
                    router.push(`/contracts/new/${t.template_key}`)
                  }
                />
              ))}
            </div>
          )}
        </section>

        {/* User's contracts */}
        {contracts.length > 0 && (
          <section className="mt-8">
            <h2 className="text-sm font-semibold text-gray-700 mb-3">
              Hop dong da tao
            </h2>
            <div className="space-y-2">
              {contracts.map((c) => {
                const statusLabel =
                  c.status === "draft"
                    ? "Ban nhap"
                    : c.status === "review"
                      ? "Dang duyet"
                      : "Hoan thanh";
                const statusColor =
                  c.status === "final"
                    ? "bg-green-100 text-green-800"
                    : c.status === "review"
                      ? "bg-yellow-100 text-yellow-800"
                      : "bg-gray-100 text-gray-700";

                return (
                  <button
                    key={c.contract_id}
                    onClick={() => router.push(`/contracts/${c.contract_id}`)}
                    className="w-full text-left flex items-center justify-between border border-gray-200 rounded-lg p-3 hover:border-brand-400 transition-colors bg-white"
                  >
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {c.title}
                      </p>
                      <p className="text-xs text-gray-400 mt-0.5">
                        {c.created_at ? new Date(c.created_at).toLocaleDateString("vi-VN") : ""}
                      </p>
                    </div>
                    <span
                      className={`text-xs font-medium px-2 py-0.5 rounded flex-shrink-0 ml-2 ${statusColor}`}
                    >
                      {statusLabel}
                    </span>
                  </button>
                );
              })}
            </div>
          </section>
        )}
      </div>
    </div>
  );
}
