"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import type { TemplateDetail } from "@/lib/types";
import { fetchTemplateDetail } from "@/lib/api-client";
import { FormWizard } from "@/components/contracts/form-wizard";

export default function NewContractPage() {
  const params = useParams();
  const templateKey = params.templateKey as string;
  const [template, setTemplate] = useState<TemplateDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchTemplateDetail(templateKey)
      .then(setTemplate)
      .catch(() => setError("Không tìm thấy mẫu hợp đồng"));
  }, [templateKey]);

  if (error) {
    return (
      <div className="h-full flex items-center justify-center">
        <p className="text-sm text-red-600">{error}</p>
      </div>
    );
  }

  if (!template) {
    return (
      <div className="h-full flex items-center justify-center">
        <p className="text-sm text-gray-400">Đang tải...</p>
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto">
      <div className="p-4 md:p-6">
        <FormWizard
          templateKey={template.template_key}
          templateName={template.name_vi}
          steps={template.form_steps}
        />
      </div>
    </div>
  );
}
