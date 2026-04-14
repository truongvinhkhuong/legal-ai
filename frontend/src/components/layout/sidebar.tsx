"use client";

import { usePathname } from "next/navigation";
import type { UserProfile } from "@/lib/types";

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
  user: UserProfile | null;
  onLogout: () => void;
}

const NAV_ITEMS = [
  { href: "/chat", label: "Chat" },
  { href: "/contracts", label: "Hợp đồng" },
  { href: "/calculator", label: "Tính thuế & BHXH" },
  { href: "/calendar", label: "Lịch tuân thủ" },
  { href: "/compliance-check", label: "Kiểm tra tuân thủ" },
  { href: "/contract-review", label: "Kiểm tra hợp đồng" },
  { href: "/admin/documents", label: "Văn bản" },
];

export function Sidebar({ isOpen, onClose, user, onLogout }: SidebarProps) {
  const pathname = usePathname();

  return (
    <>
      {/* Backdrop (mobile only) */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/30 md:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar panel */}
      <aside
        className={`
          fixed top-0 left-0 z-50 h-full w-64 bg-white border-r border-gray-200
          flex flex-col
          transition-transform duration-200 ease-in-out
          md:static md:translate-x-0
          ${isOpen ? "translate-x-0" : "-translate-x-full"}
        `}
      >
        <div className="p-4 border-b border-gray-200">
          <h1 className="text-lg font-bold text-brand-700">Legal AI</h1>
          <p className="text-xs text-gray-500">Intelligence Platform</p>
        </div>
        <nav className="flex-1 p-3 space-y-1">
          {NAV_ITEMS.map((item) => {
            const isActive =
              pathname === item.href || pathname.startsWith(item.href + "/");
            return (
              <a
                key={item.href}
                href={item.href}
                onClick={onClose}
                className={`block px-3 py-2 rounded-md text-sm transition-colors ${
                  isActive
                    ? "bg-brand-50 text-brand-700 font-medium"
                    : "text-gray-700 hover:bg-gray-100 hover:text-brand-700"
                }`}
              >
                {item.label}
              </a>
            );
          })}
        </nav>

        {/* User info + logout */}
        {user && (
          <div className="p-3 border-t border-gray-200">
            <div className="flex items-center gap-3 px-2 mb-2">
              <div className="w-8 h-8 rounded-full bg-brand-100 text-brand-700 flex items-center justify-center text-sm font-medium flex-shrink-0">
                {user.full_name.charAt(0).toUpperCase()}
              </div>
              <div className="min-w-0">
                <p className="text-sm font-medium text-gray-800 truncate">
                  {user.full_name}
                </p>
                <p className="text-xs text-gray-500 truncate">
                  {user.tenant_name}
                </p>
              </div>
            </div>
            <button
              onClick={onLogout}
              className="w-full px-3 py-1.5 text-sm text-gray-600 hover:text-red-600 hover:bg-red-50 rounded-md transition-colors text-left"
            >
              Đăng xuất
            </button>
          </div>
        )}
      </aside>
    </>
  );
}
