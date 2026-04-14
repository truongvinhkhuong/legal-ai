"use client";

import { useEffect, useState } from "react";
import type { ChecklistInfo, GapReport } from "@/lib/types";
import { fetchChecklists, analyzeCompliance } from "@/lib/api-client";

export function useComplianceCheck() {
  const [checklists, setChecklists] = useState<ChecklistInfo[]>([]);
  const [selectedType, setSelectedType] = useState("noi_quy");
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingChecklists, setLoadingChecklists] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<GapReport | null>(null);

  useEffect(() => {
    fetchChecklists()
      .then((data) => { setChecklists(data); setLoadingChecklists(false); })
      .catch(() => setLoadingChecklists(false));
  }, []);

  async function analyze() {
    if (!file) { setError("Vui lòng chọn file"); return; }
    setLoading(true); setError(null); setReport(null);
    try {
      const result = await analyzeCompliance(file, selectedType);
      if (result.error) {
        setError(result.error);
      } else {
        setReport(result);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Lỗi phân tích");
    } finally {
      setLoading(false);
    }
  }

  return {
    checklists, selectedType, setSelectedType,
    file, setFile,
    loading, loadingChecklists, error,
    report, analyze,
  };
}
