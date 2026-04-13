"""Cross-reference Linker: detect legal references in chunk text."""

from __future__ import annotations

import re

from src.api.models import CrossReference

# Internal references (within same document)
INTERNAL_REF_PATTERNS = [
    # "tại Điều 15 của Nội quy này" / "theo Điều 15 Khoản 2"
    re.compile(
        r"(?:tại|theo|căn cứ|quy định tại)\s+Điều\s+(\d+)"
        r"(?:\s+Khoản\s+(\d+))?"
        r"(?:\s+(?:của|trong)\s+(?:Nội quy|Quy chế|văn bản|Quy định)\s+này)?",
        re.IGNORECASE,
    ),
    # "Khoản 3, Điều 25"
    re.compile(
        r"Khoản\s+(\d+)\s*,?\s*Điều\s+(\d+)",
        re.IGNORECASE,
    ),
]

# External references (other documents)
EXTERNAL_REF_PATTERNS = [
    # "Nghị định 145/2020/NĐ-CP" or "NĐ số 145/2020/NĐ-CP"
    re.compile(
        r"(?:Nghị định|NĐ)\s*(?:số\s*)?(\d+/\d{4}/NĐ-CP)",
        re.IGNORECASE,
    ),
    # "Thông tư 23/2023/TT-BTC"
    re.compile(
        r"(?:Thông tư|TT)\s*(?:số\s*)?(\d+/\d{4}/TT-\w+)",
        re.IGNORECASE,
    ),
    # "Luật Lao động 2019"
    re.compile(
        r"(?:Luật)\s+([\w\s]+\d{4})",
        re.IGNORECASE,
    ),
    # Internal doc numbers: "NQ-HR-2025-001", "QĐ-FIN-2025-003"
    re.compile(r"(?:NQ|QĐ|QT|QC|CS)[\-][\w\-\/]+"),
]


class CrossRefLinker:
    """Extract cross-references from chunk text (Phase 1: extract only, no graph)."""

    def extract_references(self, text: str) -> list[CrossReference]:
        refs: list[CrossReference] = []
        seen_raw: set[str] = set()

        # Internal references
        for pattern in INTERNAL_REF_PATTERNS:
            for m in pattern.finditer(text):
                raw = m.group(0).strip()
                if raw in seen_raw:
                    continue
                seen_raw.add(raw)

                groups = m.groups()
                if len(groups) >= 2 and groups[1]:
                    # Pattern: Khoản X, Điều Y
                    refs.append(CrossReference(
                        ref_type="internal",
                        target_article=f"Điều {groups[-1]}",
                        target_clause=f"Khoản {groups[0]}",
                        raw_text=raw,
                    ))
                else:
                    refs.append(CrossReference(
                        ref_type="internal",
                        target_article=f"Điều {groups[0]}",
                        raw_text=raw,
                    ))

        # External references
        for pattern in EXTERNAL_REF_PATTERNS:
            for m in pattern.finditer(text):
                raw = m.group(0).strip()
                if raw in seen_raw:
                    continue
                seen_raw.add(raw)

                refs.append(CrossReference(
                    ref_type="external",
                    target_doc=raw,
                    raw_text=raw,
                ))

        return refs

    def extract_reference_strings(self, text: str) -> list[str]:
        """Convenience: return just the raw reference strings for chunk metadata."""
        return [ref.raw_text for ref in self.extract_references(text)]
