"use client";

import type { TemplateListItem } from "@/lib/types";

const CATEGORY_LABELS: Record<string, string> = {
  lao_dong: "Lao động",
  thue: "Thuê mặt bằng",
  dich_vu: "Dịch vụ",
};

export function TemplateCard({
  template,
  onClick,
}: {
  template: TemplateListItem;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className="w-full text-left border border-gray-200 rounded-lg p-4 hover:border-brand-500 hover:shadow-sm transition-all bg-white"
    >
      <span className="inline-block text-xs font-medium text-brand-600 bg-brand-50 px-2 py-0.5 rounded mb-2">
        {CATEGORY_LABELS[template.category] || template.category}
      </span>
      <h3 className="font-semibold text-gray-900 text-sm">
        {template.name_vi}
      </h3>
      <p className="text-xs text-gray-500 mt-1">{template.description_vi}</p>
    </button>
  );
}
