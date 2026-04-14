import type { Metadata, Viewport } from "next";
import { LayoutShell } from "@/components/layout/layout-shell";
import "./globals.css";

export const metadata: Metadata = {
  title: "Legal Intelligence Platform",
  description: "Chatbot pháp luật & AI soạn thảo hợp đồng",
  manifest: "/manifest.json",
  appleWebApp: {
    capable: true,
    statusBarStyle: "default",
    title: "Legal AI",
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  themeColor: "#016494",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="vi">
      <head>
        <link rel="apple-touch-icon" href="/icons/icon-192.png" />
      </head>
      <body>
        <LayoutShell>{children}</LayoutShell>
      </body>
    </html>
  );
}
