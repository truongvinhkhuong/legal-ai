"use client";

import { useState } from "react";
import type {
  TaxCalcResult,
  BHXHCalcResult,
  TNCNCalcResult,
  CalculatorChatResult,
} from "@/lib/types";
import { calcTax, calcBHXH, calcTNCN, calcChat } from "@/lib/api-client";

export type CalcTab = "tax" | "bhxh" | "tncn";

export function useCalculator() {
  const [activeTab, setActiveTab] = useState<CalcTab>("tax");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Tax state
  const [taxForm, setTaxForm] = useState({ doanh_thu: "", loai_hinh: "dich_vu" });
  const [taxResult, setTaxResult] = useState<TaxCalcResult | null>(null);

  // BHXH state
  const [bhxhForm, setBhxhForm] = useState({ luong: "", so_nv: "1", region: "vung_1" });
  const [bhxhResult, setBhxhResult] = useState<BHXHCalcResult | null>(null);

  // TNCN state
  const [tncnForm, setTncnForm] = useState({ thu_nhap: "", phu_thuoc: "0" });
  const [tncnResult, setTncnResult] = useState<TNCNCalcResult | null>(null);

  // Chat state
  const [chatResult, setChatResult] = useState<CalculatorChatResult | null>(null);

  async function submitTax() {
    const dt = parseInt(taxForm.doanh_thu);
    if (!dt || dt <= 0) { setError("Vui lòng nhập doanh thu hợp lệ"); return; }
    setLoading(true); setError(null);
    try {
      const result = await calcTax(dt, taxForm.loai_hinh);
      setTaxResult(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Lỗi tính thuế");
    } finally {
      setLoading(false);
    }
  }

  async function submitBHXH() {
    const luong = parseInt(bhxhForm.luong);
    if (!luong || luong <= 0) { setError("Vui lòng nhập mức lương hợp lệ"); return; }
    setLoading(true); setError(null);
    try {
      const result = await calcBHXH(luong, parseInt(bhxhForm.so_nv) || 1, bhxhForm.region);
      setBhxhResult(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Lỗi tính BHXH");
    } finally {
      setLoading(false);
    }
  }

  async function submitTNCN() {
    const tn = parseInt(tncnForm.thu_nhap);
    if (!tn || tn <= 0) { setError("Vui lòng nhập thu nhập hợp lệ"); return; }
    setLoading(true); setError(null);
    try {
      const result = await calcTNCN(tn, parseInt(tncnForm.phu_thuoc) || 0);
      setTncnResult(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Lỗi tính TNCN");
    } finally {
      setLoading(false);
    }
  }

  async function submitChat(question: string) {
    if (!question.trim()) return;
    setLoading(true); setError(null);
    try {
      const result = await calcChat(question);
      setChatResult(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Lỗi xử lý câu hỏi");
    } finally {
      setLoading(false);
    }
  }

  return {
    activeTab, setActiveTab,
    loading, error,
    taxForm, setTaxForm, taxResult, submitTax,
    bhxhForm, setBhxhForm, bhxhResult, submitBHXH,
    tncnForm, setTncnForm, tncnResult, submitTNCN,
    chatResult, submitChat,
  };
}
