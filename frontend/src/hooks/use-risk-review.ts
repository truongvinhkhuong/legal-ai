"use client";

import { useEffect, useState } from "react";
import type { ContractTypeInfo, RiskReport } from "@/lib/types";
import { fetchContractTypes, analyzeRisk } from "@/lib/api-client";

export function useRiskReview() {
  const [contractTypes, setContractTypes] = useState<ContractTypeInfo[]>([]);
  const [selectedType, setSelectedType] = useState("chung");
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingTypes, setLoadingTypes] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<RiskReport | null>(null);
  const [progress, setProgress] = useState<string | null>(null);

  useEffect(() => {
    fetchContractTypes()
      .then((data) => { setContractTypes(data); setLoadingTypes(false); })
      .catch(() => setLoadingTypes(false));
  }, []);

  async function analyze() {
    if (!file) { setError("Vui lòng chọn file"); return; }
    setLoading(true); setError(null); setReport(null);
    setProgress("Đang phân tích...");

    try {
      setProgress("Kiểm tra vi phạm...");
      const result = await analyzeRisk(file, selectedType);
      if (result.error) {
        setError(result.error);
      } else {
        setReport(result);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Lỗi phân tích");
    } finally {
      setLoading(false);
      setProgress(null);
    }
  }

  return {
    contractTypes, selectedType, setSelectedType,
    file, setFile,
    loading, loadingTypes, error, progress,
    report, analyze,
  };
}
