"use client";

import { ChatInterface } from "@/components/chat/chat-interface";

export default function ChatPage() {
  return (
    <div className="h-full flex flex-col">
      <header className="hidden md:block px-6 py-3 border-b border-gray-200 bg-white">
        <h2 className="text-lg font-semibold">Chat Pháp Luật</h2>
        <p className="text-sm text-gray-500">
          Hỏi đáp văn bản pháp lý với trích dẫn chính xác
        </p>
      </header>
      <ChatInterface />
    </div>
  );
}
