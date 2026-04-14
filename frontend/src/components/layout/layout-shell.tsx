"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { Sidebar } from "./sidebar";
import { MobileHeader } from "./mobile-header";
import { isAuthenticated, clearTokens } from "@/lib/auth";
import { fetchProfile } from "@/lib/api-client";
import type { UserProfile } from "@/lib/types";

const PUBLIC_PATHS = ["/login", "/register"];

export function LayoutShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [user, setUser] = useState<UserProfile | null>(null);
  const [authChecked, setAuthChecked] = useState(false);

  const isPublic = PUBLIC_PATHS.includes(pathname);

  useEffect(() => {
    if (isPublic) {
      setAuthChecked(true);
      return;
    }

    if (!isAuthenticated()) {
      router.replace("/login");
      return;
    }

    // Load user profile
    fetchProfile()
      .then(setUser)
      .catch(() => {
        clearTokens();
        router.replace("/login");
      })
      .finally(() => setAuthChecked(true));
  }, [pathname, isPublic, router]);

  useEffect(() => {
    if ("serviceWorker" in navigator) {
      navigator.serviceWorker.register("/sw.js").catch(() => {});
    }
  }, []);

  function handleLogout() {
    clearTokens();
    setUser(null);
    router.push("/login");
  }

  // Public pages render without shell
  if (isPublic) {
    return <>{children}</>;
  }

  // Wait for auth check
  if (!authChecked) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-sm text-gray-500">Đang tải...</div>
      </div>
    );
  }

  return (
    <div className="flex h-screen flex-col md:flex-row">
      <Sidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        user={user}
        onLogout={handleLogout}
      />
      <div className="flex-1 flex flex-col overflow-hidden">
        <MobileHeader onToggleSidebar={() => setSidebarOpen((o) => !o)} />
        <main className="flex-1 overflow-hidden">{children}</main>
      </div>
    </div>
  );
}
