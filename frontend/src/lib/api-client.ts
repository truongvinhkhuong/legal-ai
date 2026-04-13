/* API client for communicating with the FastAPI backend. */

import type {
  ComplianceResult,
  ContractDetail,
  ContractListItem,
  ContractResponse,
  IngestResponse,
  TemplateDetail,
  TemplateListItem,
} from "./types";

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

/* ----- Contract API ----- */

export async function fetchTemplates(): Promise<TemplateListItem[]> {
  const response = await fetch(`${API_BASE}/api/contracts/templates`);
  if (!response.ok) throw new Error(`Fetch templates failed: ${response.status}`);
  return response.json();
}

export async function fetchTemplateDetail(templateKey: string): Promise<TemplateDetail> {
  const response = await fetch(`${API_BASE}/api/contracts/templates/${templateKey}`);
  if (!response.ok) throw new Error(`Fetch template failed: ${response.status}`);
  return response.json();
}

export async function validateContract(
  templateKey: string,
  inputData: Record<string, unknown>,
  region: string = "vung_1",
): Promise<ComplianceResult> {
  const response = await fetch(`${API_BASE}/api/contracts/validate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      template_key: templateKey,
      input_data: inputData,
      region,
    }),
  });
  if (!response.ok) throw new Error(`Validate failed: ${response.status}`);
  return response.json();
}

export async function createContract(
  templateKey: string,
  inputData: Record<string, unknown>,
  region: string = "vung_1",
  title: string = "",
): Promise<ContractResponse> {
  const response = await fetch(`${API_BASE}/api/contracts/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      template_key: templateKey,
      input_data: inputData,
      region,
      title,
    }),
  });
  if (!response.ok) throw new Error(`Create contract failed: ${response.status}`);
  return response.json();
}

export async function fetchContracts(): Promise<ContractListItem[]> {
  const response = await fetch(`${API_BASE}/api/contracts/`);
  if (!response.ok) throw new Error(`Fetch contracts failed: ${response.status}`);
  return response.json();
}

export async function fetchContract(contractId: string): Promise<ContractDetail> {
  const response = await fetch(`${API_BASE}/api/contracts/${contractId}`);
  if (!response.ok) throw new Error(`Fetch contract failed: ${response.status}`);
  return response.json();
}

export function getExportUrl(contractId: string, format: "pdf" | "docx" = "pdf"): string {
  return `${API_BASE}/api/contracts/${contractId}/export?format=${format}`;
}
