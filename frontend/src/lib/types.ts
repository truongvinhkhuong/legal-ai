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

/* ----- Auth types ----- */

export interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  role: string;
  tenant_id: string;
  tenant_name: string;
  departments: string[];
  access_levels: string[];
  plan: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: UserProfile;
}

/* ----- Calculator types ----- */

export interface TaxCalcResult {
  doanh_thu: number;
  loai_hinh: string;
  vat_rate: number;
  vat_amount: number;
  tncn_rate: number;
  tncn_amount: number;
  total_tax: number;
  effective_rate: number;
}

export interface BHXHLine {
  label: string;
  rate_employee: number;
  rate_employer: number;
  amount_employee: number;
  amount_employer: number;
}

export interface BHXHCalcResult {
  luong_dong_bhxh: number;
  luong_dong_bhxh_cap: number;
  so_nhan_vien: number;
  region: string;
  min_wage: number;
  lines: BHXHLine[];
  total_employee: number;
  total_employer: number;
  total_monthly: number;
  total_company_monthly: number;
}

export interface TNCNBracket {
  from: number;
  to: number;
  rate: number;
  taxable: number;
  tax: number;
}

export interface TNCNCalcResult {
  thu_nhap: number;
  giam_tru_ban_than: number;
  giam_tru_phu_thuoc: number;
  so_nguoi_phu_thuoc: number;
  total_giam_tru: number;
  thu_nhap_chiu_thue: number;
  brackets: TNCNBracket[];
  total_tax: number;
  effective_rate: number;
}

export interface CalculatorChatResult {
  summary: string;
  tax: TaxCalcResult | null;
  bhxh: BHXHCalcResult | null;
  tncn: TNCNCalcResult | null;
}

/* ----- Calendar types ----- */

export interface CalendarEvent {
  date_str: string;
  title: string;
  description: string;
  category: string;
  is_overdue: boolean;
}

/* ----- Compliance Check types ----- */

export interface ChecklistInfo {
  key: string;
  label: string;
  items_count: number;
}

export interface GapItem {
  checklist_item_id: string;
  title_vi: string;
  legal_basis: string;
  status: "dat" | "khong_dat" | "khong_ro";
  matched_section: string;
  suggestion_vi: string;
}

export interface GapReport {
  checklist_type: string;
  total_items: number;
  dat_count: number;
  khong_dat_count: number;
  khong_ro_count: number;
  coverage_pct: number;
  items: GapItem[];
}

/* ----- Risk Review types ----- */

export interface ContractTypeInfo {
  key: string;
  label: string;
  rules_count: number;
}

export interface RiskIssue {
  rule_id: string;
  category: string;
  severity: string;
  title_vi: string;
  description_vi: string;
  legal_basis: string;
  matched_clause: string;
  suggestion_vi: string;
}

export interface RiskReport {
  contract_type: string;
  risk_score: number;
  total_rules: number;
  issues_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  summary_vi: string;
  issues: RiskIssue[];
}

/* ----- User Management types ----- */

export interface UserListItem {
  id: string;
  email: string;
  full_name: string;
  role: string;
  departments: string[];
  is_active: boolean;
  created_at: string;
}

export interface UserUpdate {
  full_name?: string;
  role?: string;
  departments?: string[];
}
