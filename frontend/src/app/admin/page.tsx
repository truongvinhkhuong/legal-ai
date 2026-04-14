"use client";

import { useEffect, useState } from "react";
import { fetchAdminStats } from "@/lib/api-client";

const PLAN_LABELS: Record<string, string> = {
  free: "Free",
  basic: "Basic",
  professional: "Professional",
  enterprise: "Enterprise",
};

const PLAN_COLORS: Record<string, string> = {
  free: "bg-gray-100 text-gray-700",
  basic: "bg-blue-100 text-blue-700",
  professional: "bg-brand-100 text-brand-700",
  enterprise: "bg-purple-100 text-purple-700",
};

interface Stats {
  user_count: number;
  doc_count: number;
  contract_count: number;
  monthly_usage: Record<string, number>;
}

function StatCard({
  label,
  value,
  href,
}: {
  label: string;
  value: number;
  href: string;
}) {
  return (
    <a
      href={href}
      className="bg-white border border-gray-200 rounded-lg p-4 hover:border-brand-300 transition-colors"
    >
      <p className="text-xs text-gray-500">{label}</p>
      <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
    </a>
  );
}

export default function AdminDashboardPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [plan, setPlan] = useState("free");

  useEffect(() => {
    // Get plan from stored user profile
    try {
      const stored = localStorage.getItem("user_profile");
      if (stored) {
        const profile = JSON.parse(stored);
        setPlan(profile.plan || "free");
      }
    } catch {
      // ignore
    }

    fetchAdminStats()
      .then(setStats)
      .catch(() => setStats(null))
      .finally(() => setLoading(false));
  }, []);

  const usageLabels: Record<string, string> = {
    chat: "Chat",
    contract: "Hợp đồng",
    calculator: "Tính thuế",
    compliance_check: "Kiểm tra tuân thủ",
    risk_review: "Kiểm tra hợp đồng",
  };

  return (
    <div className="h-full overflow-y-auto">
      <div className="p-4 md:p-6 max-w-4xl mx-auto">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-lg font-bold text-gray-900">
              Bảng điều khiển
            </h1>
            <p className="text-sm text-gray-500 mt-1">
              Tổng quan sử dụng hệ thống
            </p>
          </div>
          <span
            className={`px-3 py-1 rounded-full text-xs font-medium ${
              PLAN_COLORS[plan] || PLAN_COLORS.free
            }`}
          >
            {PLAN_LABELS[plan] || plan}
          </span>
        </div>

        {loading ? (
          <p className="text-sm text-gray-500 mt-4">Đang tải...</p>
        ) : stats ? (
          <>
            {/* Summary cards */}
            <div className="grid grid-cols-3 gap-3 mt-4">
              <StatCard
                label="Người dùng"
                value={stats.user_count}
                href="/admin/users"
              />
              <StatCard
                label="Văn bản"
                value={stats.doc_count}
                href="/admin/documents"
              />
              <StatCard
                label="Hợp đồng"
                value={stats.contract_count}
                href="/contracts"
              />
            </div>

            {/* Monthly usage */}
            {Object.keys(stats.monthly_usage).length > 0 && (
              <div className="mt-4 bg-white border border-gray-200 rounded-lg p-4">
                <h3 className="text-sm font-semibold text-gray-700 mb-3">
                  Sử dụng tháng này
                </h3>
                <div className="space-y-2">
                  {Object.entries(stats.monthly_usage).map(
                    ([action, count]) => (
                      <div
                        key={action}
                        className="flex items-center justify-between"
                      >
                        <span className="text-sm text-gray-600">
                          {usageLabels[action] || action}
                        </span>
                        <span className="text-sm font-medium text-gray-900">
                          {count} lượt
                        </span>
                      </div>
                    )
                  )}
                </div>
              </div>
            )}

            {/* Quick links */}
            <div className="mt-4 grid grid-cols-2 gap-3">
              <a
                href="/admin/users"
                className="bg-white border border-gray-200 rounded-lg p-3 text-sm text-brand-700 hover:bg-brand-50 transition-colors"
              >
                Quản lý người dùng
              </a>
              <a
                href="/admin/documents"
                className="bg-white border border-gray-200 rounded-lg p-3 text-sm text-brand-700 hover:bg-brand-50 transition-colors"
              >
                Quản lý văn bản
              </a>
            </div>
          </>
        ) : (
          <p className="text-sm text-red-600 mt-4">
            Không thể tải dữ liệu thống kê
          </p>
        )}
      </div>
    </div>
  );
}
