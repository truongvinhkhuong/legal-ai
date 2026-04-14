/* API client for communicating with the FastAPI backend. */

import type {
  ComplianceResult,
  ContractDetail,
  ContractListItem,
  ContractResponse,
  IngestResponse,
  LoginResponse,
  TemplateDetail,
  TemplateListItem,
  UserProfile,
} from "./types";
import { clearTokens, getAuthHeaders, getRefreshToken, setTokens } from "./auth";

const API_BASE = "";

/* ----- Auth-aware fetch wrapper ----- */

async function authFetch(url: string, options: RequestInit = {}): Promise<Response> {
  const headers = {
    ...getAuthHeaders(),
    ...options.headers,
  };

  const response = await fetch(url, { ...options, headers });

  // On 401, try refreshing the token once
  if (response.status === 401) {
    const refreshToken = getRefreshToken();
    if (refreshToken) {
      const refreshResp = await fetch(`${API_BASE}/api/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (refreshResp.ok) {
        const data = await refreshResp.json();
        setTokens(data.access_token, refreshToken);

        // Retry original request with new token
        const retryHeaders = {
          Authorization: `Bearer ${data.access_token}`,
          ...options.headers,
        };
        return fetch(url, { ...options, headers: retryHeaders });
      }
    }

    // Refresh failed — redirect to login
    clearTokens();
    if (typeof window !== "undefined") {
      window.location.href = "/login";
    }
  }

  return response;
}

/* ----- Auth API ----- */

export async function login(email: string, password: string): Promise<LoginResponse> {
  const response = await fetch(`${API_BASE}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || `Dang nhap that bai: ${response.status}`);
  }
  return response.json();
}

export async function register(
  email: string,
  password: string,
  fullName: string,
  companyName: string,
): Promise<LoginResponse> {
  const response = await fetch(`${API_BASE}/api/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      email,
      password,
      full_name: fullName,
      company_name: companyName,
    }),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || `Dang ky that bai: ${response.status}`);
  }
  return response.json();
}

export async function fetchProfile(): Promise<UserProfile> {
  const response = await authFetch(`${API_BASE}/api/auth/me`);
  if (!response.ok) throw new Error(`Fetch profile failed: ${response.status}`);
  return response.json();
}

/* ----- Chat API ----- */

export async function* streamChat(
  question: string,
  conversationId?: string,
): AsyncGenerator<{ type: string; data: unknown }> {
  const response = await authFetch(`${API_BASE}/api/chat/stream`, {
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

/* ----- Ingest API ----- */

export async function ingestDocument(
  file: File,
  metadata: Record<string, unknown>,
): Promise<IngestResponse> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("metadata", JSON.stringify(metadata));

  const response = await authFetch(`${API_BASE}/api/ingest`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`Ingest failed: ${response.status}`);
  }

  return response.json();
}

/* ----- Admin API ----- */

export async function fetchDocuments() {
  const response = await authFetch(`${API_BASE}/api/admin/documents`);
  if (!response.ok) throw new Error(`Fetch failed: ${response.status}`);
  return response.json();
}

/* ----- Health API (no auth needed) ----- */

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
  const response = await authFetch(`${API_BASE}/api/contracts/`, {
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
  const response = await authFetch(`${API_BASE}/api/contracts/`);
  if (!response.ok) throw new Error(`Fetch contracts failed: ${response.status}`);
  return response.json();
}

export async function fetchContract(contractId: string): Promise<ContractDetail> {
  const response = await authFetch(`${API_BASE}/api/contracts/${contractId}`);
  if (!response.ok) throw new Error(`Fetch contract failed: ${response.status}`);
  return response.json();
}

export function getExportUrl(contractId: string, format: "pdf" | "docx" = "pdf"): string {
  return `${API_BASE}/api/contracts/${contractId}/export?format=${format}`;
}

/* ----- Calculator API ----- */

export async function calcTax(doanh_thu_thang: number, loai_hinh: string) {
  const response = await authFetch(`${API_BASE}/api/calculator/tax`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ doanh_thu_thang, loai_hinh }),
  });
  if (!response.ok) throw new Error(`Calc tax failed: ${response.status}`);
  return response.json();
}

export async function calcBHXH(luong_dong_bhxh: number, so_nhan_vien: number, region: string) {
  const response = await authFetch(`${API_BASE}/api/calculator/bhxh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ luong_dong_bhxh, so_nhan_vien, region }),
  });
  if (!response.ok) throw new Error(`Calc BHXH failed: ${response.status}`);
  return response.json();
}

export async function calcTNCN(thu_nhap: number, so_nguoi_phu_thuoc: number) {
  const response = await authFetch(`${API_BASE}/api/calculator/tncn`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ thu_nhap, giam_tru_gia_canh: true, so_nguoi_phu_thuoc }),
  });
  if (!response.ok) throw new Error(`Calc TNCN failed: ${response.status}`);
  return response.json();
}

export async function calcChat(question: string) {
  const response = await authFetch(`${API_BASE}/api/calculator/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  if (!response.ok) throw new Error(`Calc chat failed: ${response.status}`);
  return response.json();
}

/* ----- Calendar API ----- */

export async function fetchCalendarEvents(year: number, month: number) {
  const response = await authFetch(
    `${API_BASE}/api/calendar/events?year=${year}&month=${month}`,
  );
  if (!response.ok) throw new Error(`Fetch calendar failed: ${response.status}`);
  return response.json();
}

export async function fetchUpcomingDeadlines(days: number = 7) {
  const response = await authFetch(
    `${API_BASE}/api/calendar/upcoming?days=${days}`,
  );
  if (!response.ok) throw new Error(`Fetch upcoming failed: ${response.status}`);
  return response.json();
}

/* ----- Compliance Check API ----- */

export async function fetchChecklists() {
  const response = await authFetch(`${API_BASE}/api/compliance-check/checklists`);
  if (!response.ok) throw new Error(`Fetch checklists failed: ${response.status}`);
  return response.json();
}

export async function analyzeCompliance(file: File, checklistType: string) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("checklist_type", checklistType);

  const response = await authFetch(`${API_BASE}/api/compliance-check/analyze`, {
    method: "POST",
    body: formData,
  });
  if (!response.ok) throw new Error(`Analyze failed: ${response.status}`);
  return response.json();
}

/* ----- Risk Review API ----- */

export async function fetchContractTypes() {
  const response = await authFetch(`${API_BASE}/api/risk-review/contract-types`);
  if (!response.ok) throw new Error(`Fetch contract types failed: ${response.status}`);
  return response.json();
}

export async function analyzeRisk(file: File, contractType: string) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("contract_type", contractType);

  const response = await authFetch(`${API_BASE}/api/risk-review/analyze`, {
    method: "POST",
    body: formData,
  });
  if (!response.ok) throw new Error(`Risk analyze failed: ${response.status}`);
  return response.json();
}
