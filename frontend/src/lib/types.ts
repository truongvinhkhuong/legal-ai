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
  is_action_plan?: boolean;
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

/* ----- Contract types ----- */

export interface TemplateListItem {
  template_key: string;
  name_vi: string;
  description_vi: string;
  category: string;
}

export interface FormFieldDef {
  field_key: string;
  label_vi: string;
  field_type: "text" | "number" | "date" | "select" | "textarea";
  required: boolean;
  placeholder_vi: string;
  options?: { value: string; label: string }[];
  validation?: Record<string, unknown>;
  help_text_vi: string;
}

export interface FormStep {
  step_number: number;
  title_vi: string;
  fields: FormFieldDef[];
}

export interface TemplateDetail {
  template_key: string;
  name_vi: string;
  description_vi: string;
  category: string;
  form_steps: FormStep[];
}

export interface ComplianceIssue {
  rule_id: string;
  level: "error" | "warning" | "info";
  field: string;
  message_vi: string;
  legal_basis: string;
  suggested_value?: string;
}

export interface ComplianceResult {
  is_compliant: boolean;
  issues: ComplianceIssue[];
  checked_at: string;
}

export interface ContractResponse {
  contract_id: string;
  status: string;
  rendered_content: string;
  compliance: ComplianceResult;
  created_at: string;
}

export interface ContractDetail {
  contract_id: string;
  template_key: string;
  title: string;
  status: string;
  input_data: Record<string, unknown>;
  rendered_content: string;
  compliance: ComplianceResult | null;
  version: number;
  created_at: string;
  updated_at: string;
}

export interface ContractListItem {
  contract_id: string;
  template_key: string;
  title: string;
  status: string;
  created_at: string;
}
