"use client";

import { FormEvent, useRef, useState, useEffect } from "react";
import { useChat } from "@/hooks/use-chat";
import { MessageBubble } from "./message-bubble";
import { CitationCard } from "./citation-card";

export function ChatInterface() {
  const { messages, isStreaming, sendMessage, clearMessages } = useChat();
  const [input, setInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    const question = input.trim();
    if (!question || isStreaming) return;
    setInput("");
    sendMessage(question);
  };

  return (
    <div className="flex-1 flex flex-col">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-3 md:px-6 py-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-400 mt-12 md:mt-20 px-4">
            <p className="text-lg font-medium text-gray-600">Xin chào! Tôi có thể giúp gì cho bạn?</p>
            <p className="text-sm mt-3 text-gray-400">Thử hỏi một trong những câu sau:</p>
            <div className="mt-4 space-y-2 max-w-md mx-auto">
              {[
                "Nhân viên nghỉ việc không báo trước, xử lý thế nào?",
                "Quy định về thời gian thử việc theo luật mới nhất?",
                "Hợp đồng thuê mặt bằng cần những điều khoản gì?",
              ].map((q) => (
                <button
                  key={q}
                  type="button"
                  onClick={() => { setInput(q); }}
                  className="block w-full text-left px-4 py-2.5 text-sm text-gray-600 bg-white border border-gray-200 rounded-lg hover:border-brand-400 hover:text-brand-700 transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i}>
            <MessageBubble message={msg} isStreaming={isStreaming && i === messages.length - 1} />
            {msg.citations && msg.citations.length > 0 && (
              <div className="ml-4 mt-2 space-y-2">
                {msg.citations.map((c, j) => (
                  <CitationCard key={j} citation={c} />
                ))}
              </div>
            )}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-gray-200 bg-white px-3 md:px-6 py-3">
        <form onSubmit={handleSubmit} className="flex gap-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Nhập câu hỏi pháp lý..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent"
            disabled={isStreaming}
          />
          <button
            type="submit"
            disabled={isStreaming || !input.trim()}
            className="px-4 py-2 bg-brand-600 text-white rounded-lg text-sm font-medium hover:bg-brand-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isStreaming ? "Đang trả lời..." : "Gửi"}
          </button>
          {messages.length > 0 && (
            <button
              type="button"
              onClick={clearMessages}
              className="px-3 py-2 text-gray-500 hover:text-gray-700 text-sm"
            >
              Xóa
            </button>
          )}
        </form>
      </div>
    </div>
  );
}
