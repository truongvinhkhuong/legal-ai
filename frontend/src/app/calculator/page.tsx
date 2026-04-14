"use client";

import { FormEvent, useState } from "react";
import ReactMarkdown from "react-markdown";
import { useCalculator, type CalcTab } from "@/hooks/use-calculator";

const TABS: { key: CalcTab; label: string }[] = [
  { key: "tax", label: "Thuế HKD" },
  { key: "bhxh", label: "BHXH" },
  { key: "tncn", label: "Thuế TNCN" },
];

const LOAI_HINH_OPTIONS = [
  { value: "dich_vu", label: "Dịch vụ" },
  { value: "thuong_mai", label: "Thương mại" },
  { value: "san_xuat", label: "Sản xuất" },
  { value: "cho_thue_tai_san", label: "Cho thuê tài sản" },
  { value: "hoat_dong_khac", label: "Hoạt động khác" },
];

const REGION_OPTIONS = [
  { value: "vung_1", label: "Vùng 1" },
  { value: "vung_2", label: "Vùng 2" },
  { value: "vung_3", label: "Vùng 3" },
  { value: "vung_4", label: "Vùng 4" },
];

function fmtVND(n: number): string {
  return n.toLocaleString("vi-VN") + "đ";
}

function fmtPct(n: number): string {
  return (n * 100).toFixed(1) + "%";
}

const inputClass =
  "w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-brand-500 focus:border-brand-500";

export default function CalculatorPage() {
  const calc = useCalculator();
  const [chatInput, setChatInput] = useState("");

  const handleChat = (e: FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim() || calc.loading) return;
    calc.submitChat(chatInput);
  };

  return (
    <div className="h-full overflow-y-auto">
      <div className="p-4 md:p-6 max-w-3xl mx-auto">
        <h1 className="text-lg font-bold text-gray-900">Tính thuế & BHXH</h1>
        <p className="text-sm text-gray-500 mt-1">
          Tính toán nhanh thuế hộ kinh doanh, BHXH, thuế TNCN
        </p>

        {/* Tabs */}
        <div className="flex gap-1 mt-4 bg-gray-100 rounded-lg p-1">
          {TABS.map((tab) => (
            <button
              key={tab.key}
              onClick={() => calc.setActiveTab(tab.key)}
              className={`flex-1 px-3 py-2 text-sm rounded-md transition-colors ${
                calc.activeTab === tab.key
                  ? "bg-white text-brand-700 font-medium shadow-sm"
                  : "text-gray-600 hover:text-gray-900"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Error */}
        {calc.error && (
          <div className="mt-3 p-2 bg-red-50 border border-red-200 rounded-md text-xs text-red-700">
            {calc.error}
          </div>
        )}

        {/* Tax form */}
        {calc.activeTab === "tax" && (
          <div className="mt-4 space-y-4">
            <div className="bg-white border border-gray-200 rounded-lg p-4 space-y-3">
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  Doanh thu tháng (VNĐ)
                </label>
                <input
                  type="number"
                  className={inputClass}
                  placeholder="VD: 150000000"
                  value={calc.taxForm.doanh_thu}
                  onChange={(e) => calc.setTaxForm({ ...calc.taxForm, doanh_thu: e.target.value })}
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  Loại hình kinh doanh
                </label>
                <select
                  className={inputClass}
                  value={calc.taxForm.loai_hinh}
                  onChange={(e) => calc.setTaxForm({ ...calc.taxForm, loai_hinh: e.target.value })}
                >
                  {LOAI_HINH_OPTIONS.map((o) => (
                    <option key={o.value} value={o.value}>{o.label}</option>
                  ))}
                </select>
              </div>
              <button
                onClick={calc.submitTax}
                disabled={calc.loading}
                className="w-full px-4 py-2 bg-brand-600 text-white rounded-md text-sm font-medium hover:bg-brand-700 disabled:opacity-50"
              >
                {calc.loading ? "Đang tính..." : "Tính thuế"}
              </button>
            </div>

            {calc.taxResult && (
              <div className="bg-white border border-gray-200 rounded-lg p-4">
                <h3 className="text-sm font-semibold text-gray-900 mb-3">Kết quả</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Doanh thu</span>
                    <span className="font-medium">{fmtVND(calc.taxResult.doanh_thu)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Thuế GTGT ({fmtPct(calc.taxResult.vat_rate)})</span>
                    <span className="font-medium">{fmtVND(calc.taxResult.vat_amount)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Thuế TNCN ({fmtPct(calc.taxResult.tncn_rate)})</span>
                    <span className="font-medium">{fmtVND(calc.taxResult.tncn_amount)}</span>
                  </div>
                  <div className="flex justify-between border-t border-gray-100 pt-2">
                    <span className="font-semibold text-gray-900">Tổng thuế</span>
                    <span className="font-bold text-brand-700 text-base">
                      {fmtVND(calc.taxResult.total_tax)}
                    </span>
                  </div>
                  <div className="text-xs text-gray-400 text-right">
                    Tỷ lệ thực: {fmtPct(calc.taxResult.effective_rate)}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* BHXH form */}
        {calc.activeTab === "bhxh" && (
          <div className="mt-4 space-y-4">
            <div className="bg-white border border-gray-200 rounded-lg p-4 space-y-3">
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  Mức lương đóng BHXH (VNĐ)
                </label>
                <input
                  type="number"
                  className={inputClass}
                  placeholder="VD: 10000000"
                  value={calc.bhxhForm.luong}
                  onChange={(e) => calc.setBhxhForm({ ...calc.bhxhForm, luong: e.target.value })}
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  Số nhân viên
                </label>
                <input
                  type="number"
                  className={inputClass}
                  placeholder="1"
                  value={calc.bhxhForm.so_nv}
                  onChange={(e) => calc.setBhxhForm({ ...calc.bhxhForm, so_nv: e.target.value })}
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  Khu vực
                </label>
                <select
                  className={inputClass}
                  value={calc.bhxhForm.region}
                  onChange={(e) => calc.setBhxhForm({ ...calc.bhxhForm, region: e.target.value })}
                >
                  {REGION_OPTIONS.map((o) => (
                    <option key={o.value} value={o.value}>{o.label}</option>
                  ))}
                </select>
              </div>
              <button
                onClick={calc.submitBHXH}
                disabled={calc.loading}
                className="w-full px-4 py-2 bg-brand-600 text-white rounded-md text-sm font-medium hover:bg-brand-700 disabled:opacity-50"
              >
                {calc.loading ? "Đang tính..." : "Tính BHXH"}
              </button>
            </div>

            {calc.bhxhResult && (
              <div className="bg-white border border-gray-200 rounded-lg p-4">
                <h3 className="text-sm font-semibold text-gray-900 mb-3">Kết quả BHXH/BHYT/BHTN</h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="text-left text-gray-500 border-b">
                        <th className="pb-2 font-medium">Loại</th>
                        <th className="pb-2 font-medium text-right">NLĐ</th>
                        <th className="pb-2 font-medium text-right">DN</th>
                      </tr>
                    </thead>
                    <tbody>
                      {calc.bhxhResult.lines.map((line) => (
                        <tr key={line.label} className="border-b border-gray-50">
                          <td className="py-1.5 text-gray-700">{line.label} ({fmtPct(line.rate_employee)} / {fmtPct(line.rate_employer)})</td>
                          <td className="py-1.5 text-right">{fmtVND(line.amount_employee)}</td>
                          <td className="py-1.5 text-right">{fmtVND(line.amount_employer)}</td>
                        </tr>
                      ))}
                      <tr className="font-semibold">
                        <td className="py-2 text-gray-900">Tổng</td>
                        <td className="py-2 text-right">{fmtVND(calc.bhxhResult.total_employee)}</td>
                        <td className="py-2 text-right">{fmtVND(calc.bhxhResult.total_employer)}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
                <div className="mt-3 space-y-1 text-sm">
                  <div className="flex justify-between border-t border-gray-100 pt-2">
                    <span className="text-gray-600">Tổng/người/tháng</span>
                    <span className="font-bold text-brand-700">{fmtVND(calc.bhxhResult.total_monthly)}</span>
                  </div>
                  {calc.bhxhResult.so_nhan_vien > 1 && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">Toàn công ty ({calc.bhxhResult.so_nhan_vien} NV)</span>
                      <span className="font-bold text-brand-700">{fmtVND(calc.bhxhResult.total_company_monthly)}</span>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {/* TNCN form */}
        {calc.activeTab === "tncn" && (
          <div className="mt-4 space-y-4">
            <div className="bg-white border border-gray-200 rounded-lg p-4 space-y-3">
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  Thu nhập hàng tháng (VNĐ)
                </label>
                <input
                  type="number"
                  className={inputClass}
                  placeholder="VD: 30000000"
                  value={calc.tncnForm.thu_nhap}
                  onChange={(e) => calc.setTncnForm({ ...calc.tncnForm, thu_nhap: e.target.value })}
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  Số người phụ thuộc
                </label>
                <input
                  type="number"
                  className={inputClass}
                  placeholder="0"
                  value={calc.tncnForm.phu_thuoc}
                  onChange={(e) => calc.setTncnForm({ ...calc.tncnForm, phu_thuoc: e.target.value })}
                />
              </div>
              <button
                onClick={calc.submitTNCN}
                disabled={calc.loading}
                className="w-full px-4 py-2 bg-brand-600 text-white rounded-md text-sm font-medium hover:bg-brand-700 disabled:opacity-50"
              >
                {calc.loading ? "Đang tính..." : "Tính thuế TNCN"}
              </button>
            </div>

            {calc.tncnResult && (
              <div className="bg-white border border-gray-200 rounded-lg p-4">
                <h3 className="text-sm font-semibold text-gray-900 mb-3">Kết quả thuế TNCN</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Thu nhập</span>
                    <span className="font-medium">{fmtVND(calc.tncnResult.thu_nhap)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Giảm trừ bản thân</span>
                    <span className="font-medium">-{fmtVND(calc.tncnResult.giam_tru_ban_than)}</span>
                  </div>
                  {calc.tncnResult.so_nguoi_phu_thuoc > 0 && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">
                        Giảm trừ {calc.tncnResult.so_nguoi_phu_thuoc} người phụ thuộc
                      </span>
                      <span className="font-medium">-{fmtVND(calc.tncnResult.giam_tru_phu_thuoc)}</span>
                    </div>
                  )}
                  <div className="flex justify-between border-t border-gray-100 pt-1">
                    <span className="text-gray-600">Thu nhập chịu thuế</span>
                    <span className="font-medium">{fmtVND(calc.tncnResult.thu_nhap_chiu_thue)}</span>
                  </div>

                  {/* Bracket detail */}
                  {calc.tncnResult.brackets.length > 0 && (
                    <details className="mt-2">
                      <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-700">
                        Chi tiết biểu thuế lũy tiến
                      </summary>
                      <div className="mt-1 space-y-0.5">
                        {calc.tncnResult.brackets.map((b, i) => (
                          <div key={i} className="flex justify-between text-xs text-gray-500">
                            <span>
                              {fmtVND(b.from)} - {fmtVND(b.to)} ({fmtPct(b.rate)})
                            </span>
                            <span>{fmtVND(b.tax)}</span>
                          </div>
                        ))}
                      </div>
                    </details>
                  )}

                  <div className="flex justify-between border-t border-gray-100 pt-2">
                    <span className="font-semibold text-gray-900">Thuế TNCN phải nộp</span>
                    <span className="font-bold text-brand-700 text-base">
                      {fmtVND(calc.tncnResult.total_tax)}
                    </span>
                  </div>
                  <div className="text-xs text-gray-400 text-right">
                    Tỷ lệ thực: {fmtPct(calc.tncnResult.effective_rate)}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Chat input */}
        <div className="mt-6 bg-white border border-gray-200 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-gray-700 mb-2">
            Hỏi bằng ngôn ngữ tự nhiên
          </h3>
          <form onSubmit={handleChat} className="flex gap-2">
            <input
              type="text"
              className={`flex-1 ${inputClass}`}
              placeholder="VD: Tháng này doanh thu 150 triệu, kinh doanh dịch vụ, tính thuế giúp"
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              disabled={calc.loading}
            />
            <button
              type="submit"
              disabled={calc.loading || !chatInput.trim()}
              className="px-4 py-2 bg-brand-600 text-white rounded-md text-sm font-medium hover:bg-brand-700 disabled:opacity-50 flex-shrink-0"
            >
              {calc.loading ? "Đang xử lý..." : "Tính"}
            </button>
          </form>

          {calc.chatResult && (
            <div className="mt-3 pt-3 border-t border-gray-100">
              <div className="prose prose-sm max-w-none text-sm text-gray-800">
                <ReactMarkdown>{calc.chatResult.summary}</ReactMarkdown>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
