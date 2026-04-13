import ReactMarkdown from "react-markdown";
import type { ChatMessage } from "@/lib/types";

interface Props {
  message: ChatMessage;
  isStreaming?: boolean;
}

export function MessageBubble({ message, isStreaming }: Props) {
  const isUser = message.role === "user";
  const isActionPlan = message.metadata?.is_action_plan === true;

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[90%] md:max-w-[75%] rounded-lg px-4 py-2.5 text-sm leading-relaxed ${
          isUser
            ? "bg-brand-600 text-white"
            : "bg-white border border-gray-200 text-gray-800"
        }`}
      >
        {/* Action plan indicator */}
        {isActionPlan && !isUser && (
          <div className="mb-2 pb-2 border-b border-gray-100 text-xs font-semibold text-brand-700 uppercase tracking-wide">
            Ke hoach hanh dong
          </div>
        )}

        {/* Render markdown content */}
        {isUser ? (
          <div className="whitespace-pre-wrap">{message.content}</div>
        ) : (
          <div className="prose prose-sm max-w-none prose-headings:text-gray-900 prose-strong:text-gray-900 prose-p:my-1 prose-ul:my-1 prose-ol:my-1 prose-li:my-0.5">
            <ReactMarkdown>{message.content}</ReactMarkdown>
          </div>
        )}

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
