from __future__ import annotations

import uuid
from datetime import date
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class DocType(str, Enum):
    luat = "luat"
    nghi_dinh = "nghi_dinh"
    thong_tu = "thong_tu"
    quyet_dinh = "quyet_dinh"
    noi_quy = "noi_quy"
    quy_che = "quy_che"
    quy_trinh = "quy_trinh"
    hop_dong = "hop_dong"
    bien_ban = "bien_ban"
    nghi_quyet = "nghi_quyet"
    cong_van = "cong_van"
    thong_bao = "thong_bao"
    chinh_sach = "chinh_sach"
    khac = "khac"


class DocStatus(str, Enum):
    hieu_luc = "hieu_luc"
    het_hieu_luc = "het_hieu_luc"
    da_sua_doi = "da_sua_doi"


class AccessLevel(str, Enum):
    public = "public"
    internal = "internal"
    confidential = "confidential"
    restricted = "restricted"


class ChunkType(str, Enum):
    article = "article"
    clause = "clause"
    point = "point"
    paragraph = "paragraph"
    section = "section"


class StructureType(str, Enum):
    legal_standard = "legal_standard"
    numbered_articles = "numbered_articles"
    sections = "sections"
    unstructured = "unstructured"


# ---------------------------------------------------------------------------
# Document tree (output of structure parser)
# ---------------------------------------------------------------------------

class DocumentNode(BaseModel):
    type: str  # phan, chuong, muc, dieu, khoan, diem, paragraph
    number: Optional[str] = None
    title: Optional[str] = None
    text: str = ""
    children: list[DocumentNode] = Field(default_factory=list)


class DocumentTree(BaseModel):
    header: dict = Field(default_factory=dict)
    body: list[DocumentNode] = Field(default_factory=list)
    structure_type: StructureType = StructureType.unstructured


# ---------------------------------------------------------------------------
# Cross-reference
# ---------------------------------------------------------------------------

class CrossReference(BaseModel):
    ref_type: str  # "internal" | "external"
    target_article: Optional[str] = None  # "Điều 15"
    target_clause: Optional[str] = None  # "Khoản 3"
    target_doc: Optional[str] = None  # "NĐ-145/2020/NĐ-CP"
    raw_text: str = ""  # original matched text


# ---------------------------------------------------------------------------
# Parsed document (output of format router)
# ---------------------------------------------------------------------------

class ParsedDocument(BaseModel):
    raw_text: str
    format_hints: dict = Field(default_factory=dict)
    file_path: str = ""


# ---------------------------------------------------------------------------
# Document-level metadata
# ---------------------------------------------------------------------------

class DocumentMetadata(BaseModel):
    doc_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    doc_number: str = ""
    doc_title: str = ""
    doc_type: str = DocType.khac.value
    issuing_authority: str = ""
    issue_date: Optional[date] = None
    effective_date: Optional[date] = None
    expiry_date: Optional[date] = None
    status: str = DocStatus.hieu_luc.value
    scope: list[str] = Field(default_factory=lambda: ["toan_cong_ty"])
    replaces_doc: Optional[str] = None
    amended_by: list[str] = Field(default_factory=list)
    legal_hierarchy: int = 5  # 1=Luật, 2=NĐ, 3=TT, 4=QĐ nội bộ, 5=Nội quy
    access_level: str = AccessLevel.public.value
    allowed_departments: list[str] = Field(default_factory=lambda: ["all"])
    original_file_path: str = ""


# ---------------------------------------------------------------------------
# Chunk-level metadata
# ---------------------------------------------------------------------------

class ChunkMetadata(BaseModel):
    chunk_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    doc_id: str = ""
    parent_chunk_id: Optional[str] = None
    hierarchy_path: str = ""

    # Structure location
    chapter: Optional[str] = None
    section: Optional[str] = None
    article_number: Optional[str] = None
    article_title: Optional[str] = None
    clause_number: Optional[str] = None
    point: Optional[str] = None
    chunk_type: str = ChunkType.paragraph.value

    # Text content
    original_text: str = ""

    # Cross-references & amendment
    cross_references: list[str] = Field(default_factory=list)
    amended_status: str = "original"
    amended_by_chunk: Optional[str] = None

    # Inherited from document
    doc_number: str = ""
    doc_title: str = ""
    doc_type: str = ""
    effective_date: Optional[str] = None
    status: str = DocStatus.hieu_luc.value
    access_level: str = AccessLevel.public.value
    allowed_departments: list[str] = Field(default_factory=lambda: ["all"])
    legal_hierarchy: int = 5
    issuing_authority: str = ""
    scope: list[str] = Field(default_factory=lambda: ["toan_cong_ty"])


# ---------------------------------------------------------------------------
# Qdrant payload — single source of truth for what's stored per point
# ---------------------------------------------------------------------------

class ChunkPayload(BaseModel):
    """Maps 1:1 to the Qdrant point payload."""
    # Text variants
    _node_content: str = ""  # enriched text (with context prefix) — embedded
    original_text: str = ""  # raw text — for citation display
    segmented_text: str = ""  # word-segmented text — for BM25

    # IDs & hierarchy
    chunk_id: str = ""
    doc_id: str = ""
    parent_chunk_id: Optional[str] = None
    hierarchy_path: str = ""

    # Document-level
    doc_number: str = ""
    doc_title: str = ""
    doc_type: str = ""
    issuing_authority: str = ""
    effective_date: Optional[str] = None
    expiry_date: Optional[str] = None
    status: str = DocStatus.hieu_luc.value
    legal_hierarchy: int = 5

    # Structure
    chapter: Optional[str] = None
    section: Optional[str] = None
    article_number: Optional[str] = None
    article_title: Optional[str] = None
    clause_number: Optional[str] = None
    point: Optional[str] = None
    chunk_type: str = ChunkType.paragraph.value

    # Cross-references & amendment
    cross_references: list[str] = Field(default_factory=list)
    amended_status: str = "original"
    amended_by_chunk: Optional[str] = None

    # ACL
    tenant_id: str = ""
    access_level: str = AccessLevel.public.value
    allowed_departments: list[str] = Field(default_factory=lambda: ["all"])
    scope: list[str] = Field(default_factory=lambda: ["toan_cong_ty"])

    def to_qdrant_payload(self) -> dict:
        """Serialize to dict for Qdrant upsert."""
        data = self.model_dump()
        # Qdrant payload key uses underscore-prefix for the enriched text
        data["_node_content"] = data.pop("_node_content", "")
        return data

    @classmethod
    def from_chunk_metadata(
        cls,
        chunk: ChunkMetadata,
        enriched_text: str = "",
        segmented_text: str = "",
        tenant_id: str = "",
    ) -> ChunkPayload:
        """Build payload from chunk metadata + enriched/segmented text."""
        return cls(
            _node_content=enriched_text or chunk.original_text,
            original_text=chunk.original_text,
            segmented_text=segmented_text,
            chunk_id=chunk.chunk_id,
            doc_id=chunk.doc_id,
            parent_chunk_id=chunk.parent_chunk_id,
            hierarchy_path=chunk.hierarchy_path,
            doc_number=chunk.doc_number,
            doc_title=chunk.doc_title,
            doc_type=chunk.doc_type,
            issuing_authority=chunk.issuing_authority,
            effective_date=chunk.effective_date,
            expiry_date=None,
            status=chunk.status,
            legal_hierarchy=chunk.legal_hierarchy,
            chapter=chunk.chapter,
            section=chunk.section,
            article_number=chunk.article_number,
            article_title=chunk.article_title,
            clause_number=chunk.clause_number,
            point=chunk.point,
            chunk_type=chunk.chunk_type,
            cross_references=chunk.cross_references,
            amended_status=chunk.amended_status,
            amended_by_chunk=chunk.amended_by_chunk,
            tenant_id=tenant_id,
            access_level=chunk.access_level,
            allowed_departments=chunk.allowed_departments,
            scope=chunk.scope,
        )


# ---------------------------------------------------------------------------
# API request / response models
# ---------------------------------------------------------------------------

class UserContext(BaseModel):
    user_id: str = "anonymous"
    tenant_id: str = ""
    departments: list[str] = Field(default_factory=lambda: ["all"])
    access_levels: list[str] = Field(
        default_factory=lambda: [AccessLevel.public.value]
    )
    role: str = "nhan_vien"


class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    question: str
    language: str = "vi"
    conversation_id: Optional[str] = None
    conversation_history: list[ChatMessage] = Field(default_factory=list)
    user_context: Optional[UserContext] = None


class LegalCitation(BaseModel):
    doc_title: str = ""
    doc_number: str = ""
    doc_type: str = ""
    article: Optional[str] = None
    clause: Optional[str] = None
    point: Optional[str] = None
    hierarchy_path: str = ""
    exact_quote: str = ""
    issuing_authority: str = ""
    effective_date: Optional[str] = None
    validity_status: str = DocStatus.hieu_luc.value
    amended_status: str = "original"
    groundedness_score: float = 0.0
    is_cross_reference: bool = False


class ConflictInfo(BaseModel):
    topic: str = ""
    primary_source: str = ""
    conflicting_sources: list[str] = Field(default_factory=list)
    resolution_reason: str = ""


class ChatResponse(BaseModel):
    answer: str = ""
    citations: list[LegalCitation] = Field(default_factory=list)
    groundedness: float = 0.0
    confidence: float = 0.0
    sources_count: int = 0
    has_expired_sources: bool = False
    has_conflicts: bool = False
    conflict_details: Optional[list[ConflictInfo]] = None
    validity_warnings: list[str] = Field(default_factory=list)
    conversation_id: str = ""


class IngestResponse(BaseModel):
    success: bool = True
    doc_id: str = ""
    chunks_created: int = 0
    structure_detected: str = ""
    articles_found: int = 0
    cross_references_found: int = 0
    warnings: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Contract models
# ---------------------------------------------------------------------------

class ContractTemplateKey(str, Enum):
    hdld_xdth = "hdld_xdth"
    hdld_kxdth = "hdld_kxdth"
    hd_thu_viec = "hd_thu_viec"
    hd_thue_mat_bang = "hd_thue_mat_bang"
    hd_dich_vu = "hd_dich_vu"
    qd_cham_dut_hdld = "qd_cham_dut_hdld"
    bien_ban_vi_pham = "bien_ban_vi_pham"


class RegionCode(str, Enum):
    vung_1 = "vung_1"
    vung_2 = "vung_2"
    vung_3 = "vung_3"
    vung_4 = "vung_4"


class ComplianceLevel(str, Enum):
    error = "error"
    warning = "warning"
    info = "info"


class ComplianceIssue(BaseModel):
    rule_id: str
    level: ComplianceLevel
    field: str
    message_vi: str
    legal_basis: str = ""
    suggested_value: Optional[str] = None


class ComplianceResult(BaseModel):
    is_compliant: bool
    issues: list[ComplianceIssue] = Field(default_factory=list)
    checked_at: str = ""


class FormFieldDef(BaseModel):
    field_key: str
    label_vi: str
    field_type: str  # "text", "number", "date", "select", "textarea"
    required: bool = True
    placeholder_vi: str = ""
    options: Optional[list[dict]] = None
    validation: Optional[dict] = None
    help_text_vi: str = ""


class FormStep(BaseModel):
    step_number: int
    title_vi: str
    fields: list[FormFieldDef] = Field(default_factory=list)


class TemplateListItem(BaseModel):
    template_key: str
    name_vi: str
    description_vi: str
    category: str


class TemplateDetail(BaseModel):
    template_key: str
    name_vi: str
    description_vi: str
    category: str
    form_steps: list[FormStep] = Field(default_factory=list)


class ContractValidateRequest(BaseModel):
    template_key: ContractTemplateKey
    input_data: dict
    region: RegionCode = RegionCode.vung_1


class ContractCreateRequest(BaseModel):
    template_key: ContractTemplateKey
    title: str = ""
    input_data: dict
    region: RegionCode = RegionCode.vung_1


class ContractResponse(BaseModel):
    contract_id: str
    status: str = "draft"
    rendered_content: str = ""
    compliance: ComplianceResult
    created_at: str = ""


class ContractDetail(BaseModel):
    contract_id: str
    template_key: str
    title: str
    status: str
    input_data: dict
    rendered_content: str
    compliance: Optional[ComplianceResult] = None
    version: int = 1
    created_at: str = ""
    updated_at: str = ""


class ContractListItem(BaseModel):
    contract_id: str
    template_key: str
    title: str
    status: str
    created_at: str = ""


# ---------------------------------------------------------------------------
# Auth models
# ---------------------------------------------------------------------------

class RegisterRequest(BaseModel):
    email: str
    password: str = Field(min_length=6)
    full_name: str
    company_name: str


class LoginRequest(BaseModel):
    email: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class InviteRequest(BaseModel):
    email: str
    full_name: str
    role: str = "viewer"
    departments: list[str] = Field(default_factory=list)


class UserProfile(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    tenant_id: str
    tenant_name: str = ""
    departments: list[str] = Field(default_factory=list)
    access_levels: list[str] = Field(default_factory=list)


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserProfile


# ---------------------------------------------------------------------------
# Calculator models
# ---------------------------------------------------------------------------

class TaxCalcRequest(BaseModel):
    doanh_thu_thang: int
    loai_hinh: str = "dich_vu"


class TaxCalcResponse(BaseModel):
    doanh_thu: int
    loai_hinh: str
    vat_rate: float
    vat_amount: int
    tncn_rate: float
    tncn_amount: int
    total_tax: int
    effective_rate: float


class BHXHCalcRequest(BaseModel):
    luong_dong_bhxh: int
    so_nhan_vien: int = 1
    region: str = "vung_1"


class BHXHCalcResponse(BaseModel):
    luong_dong_bhxh: int
    luong_dong_bhxh_cap: int
    so_nhan_vien: int
    region: str
    min_wage: int
    lines: list[dict] = Field(default_factory=list)
    total_employee: int = 0
    total_employer: int = 0
    total_monthly: int = 0
    total_company_monthly: int = 0


class TNCNCalcRequest(BaseModel):
    thu_nhap: int
    giam_tru_gia_canh: bool = True
    so_nguoi_phu_thuoc: int = 0


class TNCNCalcResponse(BaseModel):
    thu_nhap: int
    giam_tru_ban_than: int
    giam_tru_phu_thuoc: int
    so_nguoi_phu_thuoc: int
    total_giam_tru: int
    thu_nhap_chiu_thue: int
    brackets: list[dict] = Field(default_factory=list)
    total_tax: int
    effective_rate: float


class CalculatorChatRequest(BaseModel):
    question: str


class CalculatorChatResponse(BaseModel):
    summary: str
    tax: Optional[TaxCalcResponse] = None
    bhxh: Optional[BHXHCalcResponse] = None
    tncn: Optional[TNCNCalcResponse] = None
