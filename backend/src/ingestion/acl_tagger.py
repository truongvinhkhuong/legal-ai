"""ACL Tagger: assign access_level and allowed_departments based on doc_type."""

from __future__ import annotations

from src.api.models import AccessLevel, DocType, DocumentMetadata

DEFAULT_ACL_RULES: dict[str, dict] = {
    DocType.nghi_dinh.value: {"access_level": AccessLevel.public.value, "allowed_departments": ["all"]},
    DocType.thong_tu.value: {"access_level": AccessLevel.public.value, "allowed_departments": ["all"]},
    DocType.luat.value: {"access_level": AccessLevel.public.value, "allowed_departments": ["all"]},
    DocType.noi_quy.value: {"access_level": AccessLevel.public.value, "allowed_departments": ["all"]},
    DocType.quy_che.value: {"access_level": AccessLevel.internal.value, "allowed_departments": ["all"]},
    DocType.quy_trinh.value: {"access_level": AccessLevel.internal.value},
    DocType.hop_dong.value: {"access_level": AccessLevel.confidential.value},
    DocType.bien_ban.value: {"access_level": AccessLevel.confidential.value},
    DocType.nghi_quyet.value: {"access_level": AccessLevel.restricted.value},
}


class ACLTagger:
    """Assign default ACL based on doc_type. Admin can override."""

    def tag(
        self, doc_meta: DocumentMetadata
    ) -> tuple[str, list[str]]:
        """Return (access_level, allowed_departments) for a document.

        Admin-provided values in doc_meta take precedence over defaults.
        """
        # If admin already set non-default values, respect them
        if doc_meta.access_level != AccessLevel.public.value:
            return doc_meta.access_level, doc_meta.allowed_departments

        # Lookup default rules
        rules = DEFAULT_ACL_RULES.get(doc_meta.doc_type, {})
        access_level = rules.get("access_level", AccessLevel.public.value)
        allowed_departments = rules.get("allowed_departments", doc_meta.allowed_departments)

        return access_level, allowed_departments
