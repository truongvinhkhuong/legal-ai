/* API client for communicating with the FastAPI backend. */

import type { IngestResponse } from "./types";

const API_BASE = "";

export async function* streamChat(
  question: string,
  conversationId?: string,
): AsyncGenerator<{ type: string; data: unknown }> {
  const response = await fetch(`${API_BASE}/api/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      question,
      conversation_id: conversationId,
      language: "vi",
    }),
  });

  if (!response.ok) {
    throw new Error(`Chat failed: ${response.status}`);
  }

  const reader = response.body?.getReader();
  if (!reader) throw new Error("No response body");

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (line.startsWith("data: ")) {
        const raw = line.slice(6);
        try {
          const parsed = JSON.parse(raw);
          yield parsed;
        } catch {
          // skip malformed
        }
      } else if (line.startsWith("event: done")) {
        // next data line is the final payload
      }
    }
  }
}

export async function ingestDocument(
  file: File,
  metadata: Record<string, unknown>,
): Promise<IngestResponse> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("metadata", JSON.stringify(metadata));

  const response = await fetch(`${API_BASE}/api/ingest`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`Ingest failed: ${response.status}`);
  }

  return response.json();
}

export async function fetchDocuments() {
  const response = await fetch(`${API_BASE}/api/admin/documents`);
  if (!response.ok) throw new Error(`Fetch failed: ${response.status}`);
  return response.json();
}

export async function checkHealth() {
  const response = await fetch(`${API_BASE}/api/health`);
  return response.json();
}
