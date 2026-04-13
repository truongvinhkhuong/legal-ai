"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import type { ContractDetail } from "@/lib/types";
import { fetchContract } from "@/lib/api-client";
import { ContractPreview } from "@/components/contracts/contract-preview";

export default function ContractDetailPage() {
  const params = useParams();
  const contractId = params.contractId as string;
  const [contract, setContract] = useState<ContractDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchContract(contractId)
      .then(setContract)
      .catch(() => setError("Khong tim thay hop dong"));
  }, [contractId]);

  if (error) {
    return (
      <div className="h-full flex items-center justify-center">
        <p className="text-sm text-red-600">{error}</p>
      </div>
    );
  }

  if (!contract) {
    return (
      <div className="h-full flex items-center justify-center">
        <p className="text-sm text-gray-400">Dang tai...</p>
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto">
      <div className="p-4 md:p-6">
        <ContractPreview
          contractId={contract.contract_id}
          title={contract.title}
          status={contract.status}
          renderedContent={contract.rendered_content}
          compliance={contract.compliance}
        />
      </div>
    </div>
  );
}
