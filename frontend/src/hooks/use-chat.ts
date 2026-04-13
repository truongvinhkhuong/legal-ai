"use client";

import { useCallback, useRef, useState } from "react";
import { streamChat } from "@/lib/api-client";
import type { ChatMessage, ChatResponseMetadata, LegalCitation } from "@/lib/types";

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const conversationIdRef = useRef<string | undefined>(undefined);
  const abortRef = useRef<AbortController | null>(null);

  const sendMessage = useCallback(async (question: string) => {
    const userMsg: ChatMessage = { role: "user", content: question };
    setMessages((prev) => [...prev, userMsg]);
    setIsStreaming(true);

    let assistantContent = "";
    let citations: LegalCitation[] = [];
    let metadata: ChatResponseMetadata | undefined;

    // Add placeholder assistant message
    setMessages((prev) => [
      ...prev,
      { role: "assistant", content: "" },
    ]);

    try {
      for await (const event of streamChat(question, conversationIdRef.current)) {
        if (event.type === "chunk") {
          assistantContent += event.data as string;
          setMessages((prev) => {
            const updated = [...prev];
            updated[updated.length - 1] = {
              role: "assistant",
              content: assistantContent,
            };
            return updated;
          });
        } else if (event.type === "done" || (event as Record<string, unknown>).confidence !== undefined) {
          // Done event — contains metadata + citations
          const doneData = (event.data ?? event) as ChatResponseMetadata & {
            citations?: LegalCitation[];
          };
          citations = doneData.citations || [];
          metadata = doneData;
          conversationIdRef.current = doneData.conversation_id;
        }
      }
    } catch (err) {
      assistantContent = "Loi ket noi. Vui long thu lai.";
    }

    // Final update with citations
    setMessages((prev) => {
      const updated = [...prev];
      updated[updated.length - 1] = {
        role: "assistant",
        content: assistantContent,
        citations,
        metadata,
      };
      return updated;
    });

    setIsStreaming(false);
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
    conversationIdRef.current = undefined;
  }, []);

  return { messages, isStreaming, sendMessage, clearMessages };
}
