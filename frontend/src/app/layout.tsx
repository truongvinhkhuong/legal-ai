import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Legal Intelligence Platform",
  description: "Chatbot phap luat & AI soan thao hop dong",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="vi">
      <body>
        <div className="flex h-screen">
          <nav className="w-64 bg-white border-r border-gray-200 flex flex-col">
            <div className="p-4 border-b border-gray-200">
              <h1 className="text-lg font-bold text-brand-700">Legal AI</h1>
              <p className="text-xs text-gray-500">Intelligence Platform</p>
            </div>
            <div className="flex-1 p-3 space-y-1">
              <NavLink href="/chat" label="Chat" />
              <NavLink href="/admin/documents" label="Documents" />
            </div>
          </nav>
          <main className="flex-1 overflow-hidden">{children}</main>
        </div>
      </body>
    </html>
  );
}

function NavLink({ href, label }: { href: string; label: string }) {
  return (
    <a
      href={href}
      className="block px-3 py-2 rounded-md text-sm text-gray-700 hover:bg-gray-100 hover:text-brand-700 transition-colors"
    >
      {label}
    </a>
  );
}
