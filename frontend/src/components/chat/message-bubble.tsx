import type { ChatMessage } from "@/lib/types";

interface Props {
  message: ChatMessage;
  isStreaming?: boolean;
}

export function MessageBubble({ message, isStreaming }: Props) {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[75%] rounded-lg px-4 py-2.5 text-sm leading-relaxed ${
          isUser
            ? "bg-brand-600 text-white"
            : "bg-white border border-gray-200 text-gray-800"
        }`}
      >
        {/* Render markdown-like content */}
        <div className="whitespace-pre-wrap">{message.content}</div>

        {isStreaming && (
          <span className="inline-block w-2 h-4 bg-brand-500 animate-pulse ml-0.5" />
        )}

        {/* Metadata footer */}
        {message.metadata && !isStreaming && (
          <div className="mt-2 pt-2 border-t border-gray-100 flex items-center gap-3 text-xs text-gray-400">
            <span>
              Do tin cay: {Math.round(message.metadata.confidence)}%
            </span>
            <span>{message.metadata.sources_count} nguon</span>
            {message.metadata.has_expired_sources && (
              <span className="text-red-500">Co VB het hieu luc</span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
