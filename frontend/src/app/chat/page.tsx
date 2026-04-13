"use client";

import { ChatInterface } from "@/components/chat/chat-interface";

export default function ChatPage() {
  return (
    <div className="h-full flex flex-col">
      <header className="hidden md:block px-6 py-3 border-b border-gray-200 bg-white">
        <h2 className="text-lg font-semibold">Chat Phap Luat</h2>
        <p className="text-sm text-gray-500">
          Hoi dap van ban phap ly voi trich dan chinh xac
        </p>
      </header>
      <ChatInterface />
    </div>
  );
}
