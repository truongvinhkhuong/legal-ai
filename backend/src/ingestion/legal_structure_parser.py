"""Legal Structure Parser: detect hierarchy in Vietnamese legal documents.

Supports: Phần > Chương > Mục > Điều > Khoản > Điểm.
Fallback: unstructured for documents without clear hierarchy.
"""

from __future__ import annotations

import logging
import re
from datetime import date

from src.api.models import DocumentNode, DocumentTree, StructureType

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Regex patterns for Vietnamese legal structure elements
# ---------------------------------------------------------------------------

PATTERNS: dict[str, re.Pattern[str]] = {
    "phan": re.compile(
        r"(?:PHẦN|Phần)\s+(?:thứ\s+)?([IVXLCDM]+|\d+)[\.:\s]*(.*)$",
        re.IGNORECASE | re.MULTILINE,
    ),
    "chuong": re.compile(
        r"(?:CHƯƠNG|Chương|CHAPTER|Chapter)\s+([IVXLCDM]+|\d+)[\.:\s]*(.*)$",
        re.IGNORECASE | re.MULTILINE,
    ),
    "muc": re.compile(
        r"(?:MỤC|Mục|SECTION|Section)\s+(\d+)[\.:\s]*(.*)$",
        re.IGNORECASE | re.MULTILINE,
    ),
    "dieu": re.compile(
        r"(?:ĐIỀU|Điều|Article)\s+(\d+)[\.:\s]*(.*)$",
        re.IGNORECASE | re.MULTILINE,
    ),
}

# Khoản and Điểm are context-sensitive (only matched inside a Điều)
KHOAN_PATTERN = re.compile(r"^\s*(\d+)\.\s+(.*)", re.MULTILINE)
DIEM_PATTERN = re.compile(r"^\s*([a-zđ])\)\s+(.*)", re.MULTILINE)

# Header patterns
DOC_NUMBER_PATTERNS = [
    # Internal: NQ-HR-2025-001, QĐ-FIN-2025-003, QT-IT-2025-002
    re.compile(r"((?:NQ|QĐ|QT|QC|CS|TB|CV)[\-][\w\-\/]+)"),
    # Nghị định: 145/2020/NĐ-CP
    re.compile(r"(\d+/\d{4}/NĐ-CP)"),
    # Thông tư: 23/2023/TT-BTC
    re.compile(r"(\d+/\d{4}/TT-\w+)"),
    # Luật: số XX/YYYY/QH15
    re.compile(r"(\d+/\d{4}/QH\d*)"),
    # Quyết định: QĐ-xxx
    re.compile(r"(QĐ[\-]\d+[\w\-\/]*)"),
]

DATE_PATTERNS = [
    # "ngày 15 tháng 03 năm 2025"
    re.compile(
        r"ngày\s+(\d{1,2})\s+tháng\s+(\d{1,2})\s+năm\s+(\d{4})",
        re.IGNORECASE,
    ),
    # "15/03/2025"
    re.compile(r"(\d{1,2})/(\d{1,2})/(\d{4})"),
]

AUTHORITY_PATTERNS = [
    re.compile(
        r"((?:BỘ|ỦY BAN|HỘI ĐỒNG|GIÁM ĐỐC|TỔNG GIÁM ĐỐC|CHỦ TỊCH|QUỐC HỘI|CHÍNH PHỦ)[\w\s]*)",
        re.IGNORECASE,
    ),
]

# Hierarchy depth for stack-based parsing
LEVEL_ORDER = ["phan", "chuong", "muc", "dieu"]


class LegalStructureParser:
    """Parse Vietnamese legal document text into a hierarchical DocumentTree."""

    def parse(self, text: str) -> DocumentTree:
        """Parse normalized text into a document tree."""
        structure_type = self._detect_structure_type(text)
        header = self._extract_header(text)

        if structure_type == StructureType.unstructured:
            body = [DocumentNode(type="paragraph", text=text)]
            return DocumentTree(
                header=header,
                body=body,
                structure_type=structure_type,
            )

        body = self._build_tree(text, structure_type)

        return DocumentTree(
            header=header,
            body=body,
            structure_type=structure_type,
        )

    # ------------------------------------------------------------------
    # Detect structure type
    # ------------------------------------------------------------------
    def _detect_structure_type(self, text: str) -> StructureType:
        counts = {}
        for name, pattern in PATTERNS.items():
            counts[name] = len(pattern.findall(text))

        dieu_count = counts.get("dieu", 0)
        chuong_count = counts.get("chuong", 0)
        muc_count = counts.get("muc", 0)
        phan_count = counts.get("phan", 0)

        if chuong_count >= 1 and dieu_count >= 2:
            return StructureType.legal_standard
        if dieu_count >= 2:
            return StructureType.numbered_articles
        if muc_count >= 2 or phan_count >= 2:
            return StructureType.sections
        if dieu_count >= 1:
            return StructureType.numbered_articles
        return StructureType.unstructured

    # ------------------------------------------------------------------
    # Extract document header
    # ------------------------------------------------------------------
    def _extract_header(self, text: str) -> dict:
        header: dict = {}

        # Take the first ~2000 chars for header extraction
        head_text = text[:2000]

        # Document number
        for pattern in DOC_NUMBER_PATTERNS:
            m = pattern.search(head_text)
            if m:
                header["doc_number"] = m.group(1)
                break

        # Date
        for pattern in DATE_PATTERNS:
            m = pattern.search(head_text)
            if m:
                groups = m.groups()
                try:
                    if len(groups) == 3:
                        day, month, year = int(groups[0]), int(groups[1]), int(groups[2])
                        header["issue_date"] = date(year, month, day).isoformat()
                except (ValueError, TypeError):
                    pass
                break

        # Issuing authority
        for pattern in AUTHORITY_PATTERNS:
            m = pattern.search(head_text)
            if m:
                header["issuing_authority"] = m.group(1).strip()
                break

        # Title: try to find a prominent line (often all-caps or centered)
        lines = head_text.split("\n")
        for line in lines:
            stripped = line.strip()
            # Skip short lines, lines that are just numbers, etc.
            if len(stripped) < 10:
                continue
            # All-caps line or line starting with common title keywords
            if stripped.isupper() or any(
                stripped.lower().startswith(kw)
                for kw in [
                    "nội quy", "quy chế", "quy định", "quy trình",
                    "nghị định", "thông tư", "luật", "chính sách",
                    "hợp đồng", "thỏa thuận", "biên bản", "nghị quyết",
                    "[center]", "[h1]", "[h2]",
                ]
            ):
                title = stripped.replace("[CENTER] ", "").replace("[H1] ", "").replace("[H2] ", "")
                header["title"] = title
                break

        return header

    # ------------------------------------------------------------------
    # Build hierarchical tree
    # ------------------------------------------------------------------
    def _build_tree(self, text: str, structure_type: StructureType) -> list[DocumentNode]:
        lines = text.split("\n")
        root_children: list[DocumentNode] = []
        # Stack: list of (level_index, node) — level_index maps to LEVEL_ORDER
        stack: list[tuple[int, DocumentNode]] = []

        current_text_lines: list[str] = []

        def _flush_text() -> None:
            """Append accumulated text to the deepest node on the stack."""
            if not current_text_lines:
                return
            joined = "\n".join(current_text_lines).strip()
            if not joined:
                current_text_lines.clear()
                return
            if stack:
                _, node = stack[-1]
                if node.text:
                    node.text += "\n" + joined
                else:
                    node.text = joined
            current_text_lines.clear()

        for line in lines:
            stripped = line.strip()
            if not stripped:
                # Keep blank lines in text accumulation for paragraph separation
                if current_text_lines:
                    current_text_lines.append("")
                continue

            matched = False

            # Check higher-level patterns (phần, chương, mục, điều)
            for level_idx, level_name in enumerate(LEVEL_ORDER):
                # For numbered_articles, skip phần/chương/mục
                if structure_type == StructureType.numbered_articles and level_name in (
                    "phan", "chuong", "muc"
                ):
                    continue
                if structure_type == StructureType.sections and level_name == "dieu":
                    continue

                pattern = PATTERNS[level_name]
                m = pattern.match(stripped)
                if m:
                    _flush_text()

                    number = m.group(1)
                    title = m.group(2).strip() if m.group(2) else ""
                    node = DocumentNode(
                        type=level_name,
                        number=number,
                        title=title,
                    )

                    # Pop stack to proper parent level
                    while stack and stack[-1][0] >= level_idx:
                        stack.pop()

                    if stack:
                        stack[-1][1].children.append(node)
                    else:
                        root_children.append(node)

                    stack.append((level_idx, node))
                    matched = True
                    break

            if matched:
                continue

            # Check khoản (only inside a điều)
            if self._inside_dieu(stack):
                km = KHOAN_PATTERN.match(stripped)
                if km:
                    _flush_text()
                    number = km.group(1)
                    khoan_text = km.group(2).strip()
                    node = DocumentNode(
                        type="khoan",
                        number=number,
                        text=khoan_text,
                    )
                    # Pop any existing khoản/điểm from stack
                    while stack and stack[-1][1].type in ("khoan", "diem"):
                        stack.pop()
                    if stack:
                        stack[-1][1].children.append(node)
                    stack.append((len(LEVEL_ORDER), node))  # depth beyond điều
                    continue

            # Check điểm (only inside a khoản)
            if self._inside_khoan(stack):
                dm = DIEM_PATTERN.match(stripped)
                if dm:
                    _flush_text()
                    letter = dm.group(1)
                    diem_text = dm.group(2).strip()
                    node = DocumentNode(
                        type="diem",
                        number=letter,
                        text=diem_text,
                    )
                    # Pop any existing điểm from stack
                    while stack and stack[-1][1].type == "diem":
                        stack.pop()
                    if stack:
                        stack[-1][1].children.append(node)
                    stack.append((len(LEVEL_ORDER) + 1, node))
                    continue

            # Regular text line — accumulate
            current_text_lines.append(stripped)

        _flush_text()
        return root_children

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _inside_dieu(stack: list[tuple[int, DocumentNode]]) -> bool:
        for _, node in reversed(stack):
            if node.type == "dieu":
                return True
            if node.type in ("phan", "chuong", "muc"):
                return False
        return False

    @staticmethod
    def _inside_khoan(stack: list[tuple[int, DocumentNode]]) -> bool:
        for _, node in reversed(stack):
            if node.type == "khoan":
                return True
            if node.type in ("dieu", "phan", "chuong", "muc"):
                return False
        return False
