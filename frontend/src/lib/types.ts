/* Shared TypeScript types — mirrors backend Pydantic models. */

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  citations?: LegalCitation[];
  metadata?: ChatResponseMetadata;
}

export interface LegalCitation {
  doc_title: string;
  doc_number: string;
  doc_type: string;
  article: string | null;
  clause: string | null;
  point: string | null;
  hierarchy_path: string;
  exact_quote: string;
  issuing_authority: string;
  effective_date: string | null;
  validity_status: string;
  amended_status: string;
  groundedness_score: number;
  is_cross_reference: boolean;
}

export interface ChatResponseMetadata {
  confidence: number;
  groundedness: number;
  sources_count: number;
  has_expired_sources: boolean;
  has_conflicts: boolean;
  validity_warnings: string[];
  conversation_id: string;
}

export interface DocumentListItem {
  id: string;
  doc_number: string;
  doc_title: string;
  doc_type: string;
  status: string;
  issuing_authority: string;
  effective_date: string | null;
  chunks_count: number;
  created_at: string;
}

export interface IngestResponse {
  success: boolean;
  doc_id: string;
  chunks_created: number;
  structure_detected: string;
  articles_found: number;
  cross_references_found: number;
  warnings: string[];
}
