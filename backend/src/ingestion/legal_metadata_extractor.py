"""Legal Metadata Extractor: extract and enrich document/chunk metadata."""

from __future__ import annotations

import uuid
from datetime import date

from src.api.models import (
    AccessLevel,
    ChunkMetadata,
    DocStatus,
    DocType,
    DocumentMetadata,
)

# Mapping from doc_type to legal_hierarchy level
_DOC_TYPE_TO_HIERARCHY: dict[str, int] = {
    DocType.luat.value: 1,
    DocType.nghi_dinh.value: 2,
    DocType.thong_tu.value: 3,
    DocType.quyet_dinh.value: 4,
    DocType.noi_quy.value: 5,
    DocType.quy_che.value: 5,
    DocType.quy_trinh.value: 5,
    DocType.hop_dong.value: 5,
    DocType.bien_ban.value: 5,
    DocType.nghi_quyet.value: 4,
    DocType.cong_van.value: 5,
    DocType.thong_bao.value: 5,
    DocType.chinh_sach.value: 5,
}

# Keywords to auto-detect doc_type from title
_TITLE_KEYWORDS: dict[str, str] = {
    "nội quy": DocType.noi_quy.value,
    "quy chế": DocType.quy_che.value,
    "quy trình": DocType.quy_trinh.value,
    "quy định": DocType.noi_quy.value,
    "nghị định": DocType.nghi_dinh.value,
    "thông tư": DocType.thong_tu.value,
    "luật": DocType.luat.value,
    "hợp đồng": DocType.hop_dong.value,
    "biên bản": DocType.bien_ban.value,
    "nghị quyết": DocType.nghi_quyet.value,
    "công văn": DocType.cong_van.value,
    "thông báo": DocType.thong_bao.value,
    "chính sách": DocType.chinh_sach.value,
    "quyết định": DocType.quyet_dinh.value,
}

# Keywords to auto-detect from doc_number prefix
_NUMBER_PREFIX_TO_TYPE: dict[str, str] = {
    "NQ": DocType.noi_quy.value,
    "QĐ": DocType.quyet_dinh.value,
    "QT": DocType.quy_trinh.value,
    "QC": DocType.quy_che.value,
    "CS": DocType.chinh_sach.value,
    "CV": DocType.cong_van.value,
    "TB": DocType.thong_bao.value,
}


class LegalMetadataExtractor:
    """Extract and enrich metadata for documents and chunks."""

    def extract_document_metadata(
        self,
        header: dict,
        file_path: str,
        override_metadata: dict | None = None,
    ) -> DocumentMetadata:
        """Build DocumentMetadata from parsed header + admin overrides.

        Priority: admin override > auto-detected > default.
        """
        override = override_metadata or {}

        # Auto-detect doc_type from title or doc_number
        auto_doc_type = self._detect_doc_type(
            header.get("title", ""),
            header.get("doc_number", ""),
        )

        # Auto-detect issue date
        auto_issue_date = None
        if header.get("issue_date"):
            try:
                auto_issue_date = date.fromisoformat(header["issue_date"])
            except (ValueError, TypeError):
                pass

        doc_type = override.get("doc_type", auto_doc_type)
        legal_hierarchy = _DOC_TYPE_TO_HIERARCHY.get(doc_type, 5)

        # Parse override dates
        effective_date = self._parse_date(override.get("effective_date")) or auto_issue_date
        expiry_date = self._parse_date(override.get("expiry_date"))
        issue_date = self._parse_date(override.get("issue_date")) or auto_issue_date

        return DocumentMetadata(
            doc_id=str(uuid.uuid4()),
            doc_number=override.get("doc_number", header.get("doc_number", "")),
            doc_title=override.get("doc_title", header.get("title", "")),
            doc_type=doc_type,
            issuing_authority=override.get(
                "issuing_authority", header.get("issuing_authority", "")
            ),
            issue_date=issue_date,
            effective_date=effective_date,
            expiry_date=expiry_date,
            status=override.get("status", DocStatus.hieu_luc.value),
            scope=override.get("scope", ["toan_cong_ty"]),
            replaces_doc=override.get("replaces_doc"),
            amended_by=override.get("amended_by", []),
            legal_hierarchy=override.get("legal_hierarchy", legal_hierarchy),
            access_level=override.get("access_level", AccessLevel.public.value),
            allowed_departments=override.get("allowed_departments", ["all"]),
            original_file_path=file_path,
        )

    def enrich_chunk_metadata(
        self,
        chunk: ChunkMetadata,
        doc_meta: DocumentMetadata,
    ) -> ChunkMetadata:
        """Copy document-level fields down to a chunk."""
        chunk.doc_id = doc_meta.doc_id
        chunk.doc_number = doc_meta.doc_number
        chunk.doc_title = doc_meta.doc_title
        chunk.doc_type = doc_meta.doc_type
        chunk.effective_date = (
            doc_meta.effective_date.isoformat()
            if doc_meta.effective_date
            else None
        )
        chunk.status = doc_meta.status
        chunk.access_level = doc_meta.access_level
        chunk.allowed_departments = doc_meta.allowed_departments
        chunk.legal_hierarchy = doc_meta.legal_hierarchy
        chunk.issuing_authority = doc_meta.issuing_authority
        chunk.scope = doc_meta.scope
        return chunk

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _detect_doc_type(title: str, doc_number: str) -> str:
        title_lower = title.lower()
        for keyword, dtype in _TITLE_KEYWORDS.items():
            if keyword in title_lower:
                return dtype

        # Fallback: detect from doc_number prefix
        for prefix, dtype in _NUMBER_PREFIX_TO_TYPE.items():
            if doc_number.startswith(prefix):
                return dtype

        # Check for law-style numbers: 145/2020/NĐ-CP
        if "/NĐ-CP" in doc_number:
            return DocType.nghi_dinh.value
        if "/TT-" in doc_number:
            return DocType.thong_tu.value
        if "/QH" in doc_number:
            return DocType.luat.value

        return DocType.khac.value

    @staticmethod
    def _parse_date(value: str | date | None) -> date | None:
        if value is None:
            return None
        if isinstance(value, date):
            return value
        try:
            return date.fromisoformat(str(value))
        except (ValueError, TypeError):
            return None
